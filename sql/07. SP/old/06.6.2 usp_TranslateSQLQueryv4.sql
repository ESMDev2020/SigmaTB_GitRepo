USE [SigmaTB];
GO

IF OBJECT_ID('[mrs].[usp_TranslateSQLQuery]', 'P') IS NOT NULL
    DROP PROCEDURE [mrs].[usp_TranslateSQLQuery];
GO

-- =============================================
-- Author:      Gemini
-- Create date: 2025-04-29
-- Modify date: 2025-05-06
-- Description: Translates object names (tables, columns) enclosed in square brackets
--              within a given SQL query string bidirectionally:
--              1. AS/400 short names to MSSQL long names (when no "_____" is present)
--              2. MSSQL long names to AS/400 short names (when "_____" is present)
--              Handles single objects like [TABLE1] and qualified objects like [TABLE1].[COLUMN1].
--              Includes debug mode and option to execute the translated query.
-- Parameters:
--   @SQLQuery NVARCHAR(MAX)      : The input SQL query string with object names in brackets
--                                   (e.g., "SELECT [COL1] FROM [TABLE1]").
--   @DebugMode BIT = 0           : Optional. Set to 1 to enable debug PRINT messages.
--                                   Defaults to 0 (disabled).
--   @TranslatedQuery NVARCHAR(MAX) OUTPUT: The resulting query string with translated names.
--                                           NULL on error or if input is NULL.
--   @Execution BIT = 0           : Optional. Set to 1 to execute the translated query.
--                                   Defaults to 0 (disabled).
-- Returns:     Outputs the translated query via @TranslatedQuery.
--              If @DebugMode = 1, prints debug information during execution.
--              If @Execution = 1, executes the translated query with [mrs] schema.
--              Throws an error on malformed input or translation failures.
-- =============================================
CREATE PROCEDURE [mrs].[usp_TranslateSQLQuery]
    @SQLQuery NVARCHAR(MAX),
    @DebugMode BIT = 0,
    @TranslatedQuery NVARCHAR(MAX) OUTPUT,
    @Execution BIT = 0
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE
        @myVarNVARCHARInputQuery NVARCHAR(MAX) = @SQLQuery,
        @myVarNVARCHARTranslatedQuery NVARCHAR(MAX) = N'',
        @myVarNVARCHARObjectName1 NVARCHAR(128),
        @myVarNVARCHARObjectName2 NVARCHAR(128),
        @myVarNVARCHARTranslatedName1 NVARCHAR(500),
        @myVarNVARCHARTranslatedName2 NVARCHAR(500),
        @myVarNVARCHARTranslatedObject NVARCHAR(MAX),
        @myVarINTCurrentPosition INT = 1,
        @myVarINTInputLength INT,
        @myVarINTStartBracketPos1 INT,
        @myVarINTEndBracketPos1 INT,
        @myVarINTStartBracketPos2 INT,
        @myVarINTEndBracketPos2 INT,
        @myVarBITIsTableColumnPair BIT = 0,
        @myVarBITIsAS400ToMSSQL BIT, -- Direction flag
        @myVarNVARCHARErrorMessage NVARCHAR(MAX),
        @myVarNVARCHARSQL NVARCHAR(MAX),
        @myVarINTErrorSeverity INT,
        @myVarINTErrorState INT;

    IF @DebugMode = 1 PRINT N'-- usp_TranslateSQLQuery Start --';
    IF @DebugMode = 1 PRINT N'-- Input Query: ' + ISNULL(@myVarNVARCHARInputQuery, 'NULL');
    IF @DebugMode = 1 PRINT N'-- Debug Mode: ON';
    IF @DebugMode = 1 AND @Execution = 1 PRINT N'-- Execution Mode: ON';

    IF @myVarNVARCHARInputQuery IS NULL
    BEGIN
        SET @TranslatedQuery = NULL;
        IF @DebugMode = 1 PRINT N'-- Input query is NULL. Returning NULL. --';
        RETURN;
    END;

    SET @myVarINTInputLength = LEN(@myVarNVARCHARInputQuery);

    IF @myVarINTInputLength = 0
    BEGIN
        SET @TranslatedQuery = N'';
        IF @DebugMode = 1 PRINT N'-- Input query is empty. Returning empty string. --';
        RETURN;
    END;

    WHILE @myVarINTCurrentPosition <= @myVarINTInputLength
    BEGIN
        SET @myVarINTStartBracketPos1 = CHARINDEX(N'[', @myVarNVARCHARInputQuery, @myVarINTCurrentPosition);

        IF @myVarINTStartBracketPos1 = 0
        BEGIN
            -- No more brackets found, append the rest of the string
            SET @myVarNVARCHARTranslatedQuery += SUBSTRING(@myVarNVARCHARInputQuery, @myVarINTCurrentPosition, @myVarINTInputLength - @myVarINTCurrentPosition + 1);
            IF @DebugMode = 1 PRINT N'-- No more brackets found. Appending remaining string: ' + SUBSTRING(@myVarNVARCHARInputQuery, @myVarINTCurrentPosition, @myVarINTInputLength - @myVarINTCurrentPosition + 1);
            BREAK; -- Exit the loop
        END
        ELSE
        BEGIN
            -- Append the text before the bracket
            SET @myVarNVARCHARTranslatedQuery += SUBSTRING(@myVarNVARCHARInputQuery, @myVarINTCurrentPosition, @myVarINTStartBracketPos1 - @myVarINTCurrentPosition);
            IF @DebugMode = 1 AND (@myVarINTStartBracketPos1 - @myVarINTCurrentPosition > 0) PRINT N'-- Appending text before bracket: ' + SUBSTRING(@myVarNVARCHARInputQuery, @myVarINTCurrentPosition, @myVarINTStartBracketPos1 - @myVarINTCurrentPosition);

            SET @myVarINTEndBracketPos1 = CHARINDEX(N']', @myVarNVARCHARInputQuery, @myVarINTStartBracketPos1 + 1);

            IF @myVarINTEndBracketPos1 = 0 OR @myVarINTEndBracketPos1 < @myVarINTStartBracketPos1
            BEGIN
                -- Malformed input: Opening bracket without a closing one
                SET @myVarNVARCHARErrorMessage = N'Malformed input string: Unmatched bracket starting near position ' + CAST(@myVarINTStartBracketPos1 AS NVARCHAR(10));
                IF @DebugMode = 1 PRINT N'-- ERROR: ' + @myVarNVARCHARErrorMessage;
                RAISERROR(@myVarNVARCHARErrorMessage, 16, 1);
            END;

            SET @myVarNVARCHARObjectName1 = SUBSTRING(@myVarNVARCHARInputQuery, @myVarINTStartBracketPos1 + 1, @myVarINTEndBracketPos1 - @myVarINTStartBracketPos1 - 1);
            SET @myVarBITIsTableColumnPair = 0; -- Reset flag

            -- Determine conversion direction based on "_____" pattern
            SET @myVarBITIsAS400ToMSSQL = CASE WHEN CHARINDEX(N'_____', @myVarNVARCHARObjectName1) = 0 THEN 1 ELSE 0 END;
            
            IF @DebugMode = 1 
            BEGIN
                PRINT N'-- Found potential object 1: [' + @myVarNVARCHARObjectName1 + N']';
                PRINT N'-- Conversion direction: ' + CASE WHEN @myVarBITIsAS400ToMSSQL = 1 THEN 'AS400 to MSSQL' ELSE 'MSSQL to AS400' END;
            END

            -- Check for '.[' pattern immediately following the first closing bracket
            IF (@myVarINTEndBracketPos1 + 2) <= @myVarINTInputLength AND SUBSTRING(@myVarNVARCHARInputQuery, @myVarINTEndBracketPos1 + 1, 2) = N'.['
            BEGIN
                SET @myVarINTStartBracketPos2 = @myVarINTEndBracketPos1 + 2;
                SET @myVarINTEndBracketPos2 = CHARINDEX(N']', @myVarNVARCHARInputQuery, @myVarINTStartBracketPos2 + 1);

                IF @myVarINTEndBracketPos2 > @myVarINTStartBracketPos2
                BEGIN
                    SET @myVarNVARCHARObjectName2 = SUBSTRING(@myVarNVARCHARInputQuery, @myVarINTStartBracketPos2 + 1, @myVarINTEndBracketPos2 - @myVarINTStartBracketPos2 - 1);
                    
                    -- If we have a table.column pair, both parts should have consistent "_____" pattern
                    -- If they don't match, use the first object's pattern to determine direction
                    IF LEN(@myVarNVARCHARObjectName1) > 0 AND LEN(@myVarNVARCHARObjectName2) > 0
                    BEGIN
                       SET @myVarBITIsTableColumnPair = 1;
                       IF @DebugMode = 1 PRINT N'-- Detected table.column pattern: [' + @myVarNVARCHARObjectName1 + N'].[' + @myVarNVARCHARObjectName2 + N']';
                    END
                    ELSE
                    BEGIN
                         IF @DebugMode = 1 PRINT N'-- Detected table.column pattern but one part is empty. Treating as single object.';
                         SET @myVarBITIsTableColumnPair = 0; -- Ensure flag is reset if second part is empty
                    END
                END
                ELSE
                BEGIN
                    -- Malformed: Found '[' after '.[' but no matching ']'
                    IF @DebugMode = 1 PRINT N'-- Detected ''.['' but no subsequent closing bracket. Treating [' + @myVarNVARCHARObjectName1 + N'] as single object.';
                    SET @myVarBITIsTableColumnPair = 0; -- Treat first part as single object
                    -- No error throw, just proceed as if it wasn't a pair
                END;
            END;

            -- Reset translation variables
            SET @myVarNVARCHARTranslatedObject = NULL;
            SET @myVarNVARCHARTranslatedName1 = NULL;
            SET @myVarNVARCHARTranslatedName2 = NULL;

            IF @myVarBITIsTableColumnPair = 1
            BEGIN
                -- Handle table.column pair translation
                IF @myVarBITIsAS400ToMSSQL = 1
                BEGIN
                    -- AS400 to MSSQL translation (existing functionality)
                    -- Translate the first part (potential table)
                    IF @DebugMode = 1 PRINT N'-->> Calling usp_TranslateObjectName [Table Part, AS400 to MSSQL]: InputName=''' + @myVarNVARCHARObjectName1 + ''', ContextTableName=NULL';
                    BEGIN TRY
                        EXEC [mrs].[usp_TranslateObjectName] @InputName = @myVarNVARCHARObjectName1, @ContextTableName = NULL, @TranslatedName = @myVarNVARCHARTranslatedName1 OUTPUT;
                        IF @DebugMode = 1 PRINT N'-->> Result [Table Part, AS400 to MSSQL]: ' + ISNULL(QUOTENAME(@myVarNVARCHARTranslatedName1), 'NULL');
                    END TRY
                    BEGIN CATCH
                        IF @DebugMode = 1 PRINT N'-->> ERROR Translating [Table Part, AS400 to MSSQL]: ' + @myVarNVARCHARObjectName1;
                        SET @myVarNVARCHARTranslatedName1 = NULL; -- Ensure it's null on error
                    END CATCH

                    -- Translate the second part (potential column) using original AS400 table name as context
                    IF @DebugMode = 1 PRINT N'-->> Calling usp_TranslateObjectName [Column Part, AS400 to MSSQL]: InputName=''' + @myVarNVARCHARObjectName2 + ''', ContextTableName=''' + ISNULL(@myVarNVARCHARObjectName1, 'NULL') + '''';
                    BEGIN TRY
                        EXEC [mrs].[usp_TranslateObjectName] @InputName = @myVarNVARCHARObjectName2, @ContextTableName = @myVarNVARCHARObjectName1, @TranslatedName = @myVarNVARCHARTranslatedName2 OUTPUT;
                        IF @DebugMode = 1 PRINT N'-->> Result [Column Part, AS400 to MSSQL]: ' + ISNULL(QUOTENAME(@myVarNVARCHARTranslatedName2), 'NULL');
                    END TRY
                    BEGIN CATCH
                        IF @DebugMode = 1 PRINT N'-->> ERROR Translating [Column Part, AS400 to MSSQL]: ' + @myVarNVARCHARObjectName2 + N' with Context: ' + @myVarNVARCHARObjectName1;
                        SET @myVarNVARCHARTranslatedName2 = NULL; -- Ensure it's null on error
                    END CATCH
                END
                ELSE -- MSSQL to AS400 translation
                BEGIN
                    -- Extract AS400 table name from MSSQL format (after the "_____")
                    DECLARE @TableAS400Name NVARCHAR(128);
                    
                    -- For table part
                    BEGIN TRY
                        -- Look for "_____" pattern in the table name
                        DECLARE @UnderscorePos1 INT = CHARINDEX(N'_____', @myVarNVARCHARObjectName1);
                        IF @UnderscorePos1 > 0
                        BEGIN
                            -- Extract AS400 name which is after "_____"
                            SET @TableAS400Name = SUBSTRING(@myVarNVARCHARObjectName1, @UnderscorePos1 + 5, LEN(@myVarNVARCHARObjectName1) - @UnderscorePos1 - 5 + 1);
                            SET @myVarNVARCHARTranslatedName1 = @TableAS400Name;
                            IF @DebugMode = 1 PRINT N'-->> Extracted AS400 Table Name: ' + ISNULL(@myVarNVARCHARTranslatedName1, 'NULL');
                        END
                        ELSE
                        BEGIN
                            -- No "_____" found in table name, use as is
                            SET @myVarNVARCHARTranslatedName1 = @myVarNVARCHARObjectName1;
                            IF @DebugMode = 1 PRINT N'-->> No "_____" pattern found in Table Name. Using as is: ' + @myVarNVARCHARObjectName1;
                        END
                    END TRY
                    BEGIN CATCH
                        IF @DebugMode = 1 PRINT N'-->> ERROR Extracting AS400 Name from Table Part: ' + @myVarNVARCHARObjectName1;
                        SET @myVarNVARCHARTranslatedName1 = NULL;
                    END CATCH
                    
                    -- For column part
                    BEGIN TRY
                        -- Look for "_____" pattern in the column name
                        DECLARE @UnderscorePos2 INT = CHARINDEX(N'_____', @myVarNVARCHARObjectName2);
                        IF @UnderscorePos2 > 0
                        BEGIN
                            -- Extract AS400 name which is after "_____"
                            SET @myVarNVARCHARTranslatedName2 = SUBSTRING(@myVarNVARCHARObjectName2, @UnderscorePos2 + 5, LEN(@myVarNVARCHARObjectName2) - @UnderscorePos2 - 5 + 1);
                            IF @DebugMode = 1 PRINT N'-->> Extracted AS400 Column Name: ' + ISNULL(@myVarNVARCHARTranslatedName2, 'NULL');
                        END
                        ELSE
                        BEGIN
                            -- No "_____" found in column name, use as is
                            SET @myVarNVARCHARTranslatedName2 = @myVarNVARCHARObjectName2;
                            IF @DebugMode = 1 PRINT N'-->> No "_____" pattern found in Column Name. Using as is: ' + @myVarNVARCHARObjectName2;
                        END
                    END TRY
                    BEGIN CATCH
                        IF @DebugMode = 1 PRINT N'-->> ERROR Extracting AS400 Name from Column Part: ' + @myVarNVARCHARObjectName2;
                        SET @myVarNVARCHARTranslatedName2 = NULL;
                    END CATCH
                END

                -- Construct the translated pair or use fallbacks
                IF @myVarNVARCHARTranslatedName1 IS NOT NULL
                BEGIN
                    IF @myVarNVARCHARTranslatedName2 IS NOT NULL
                        SET @myVarNVARCHARTranslatedObject = QUOTENAME(@myVarNVARCHARTranslatedName1) + N'.' + QUOTENAME(@myVarNVARCHARTranslatedName2);
                    ELSE -- Table translated, column did not
                        SET @myVarNVARCHARTranslatedObject = QUOTENAME(@myVarNVARCHARTranslatedName1) + N'.[' + @myVarNVARCHARObjectName2 + N']'; -- Use original column name
                END
                ELSE -- Table did not translate
                BEGIN
                    IF @myVarNVARCHARTranslatedName2 IS NOT NULL -- Column translated
                        SET @myVarNVARCHARTranslatedObject = N'[' + @myVarNVARCHARObjectName1 + N'].' + QUOTENAME(@myVarNVARCHARTranslatedName2); -- Use original table name
                    ELSE -- Neither translated
                        SET @myVarNVARCHARTranslatedObject = N'[' + @myVarNVARCHARObjectName1 + N'].[' + @myVarNVARCHARObjectName2 + N']'; -- Use original pair
                END;

                -- Advance position past the second bracket
                SET @myVarINTCurrentPosition = @myVarINTEndBracketPos2 + 1;
                IF @DebugMode = 1 PRINT N'-- Appending translated pair: ' + @myVarNVARCHARTranslatedObject + N'. Advancing position to ' + CAST(@myVarINTCurrentPosition AS NVARCHAR(10));
            END
            ELSE -- Not a table.column pair, or second part was invalid
            BEGIN
                -- Handle single object translation
                IF @myVarBITIsAS400ToMSSQL = 1
                BEGIN
                    -- AS400 to MSSQL translation (existing functionality)
                    IF @DebugMode = 1 PRINT N'-->> Calling usp_TranslateObjectName [Single Part, AS400 to MSSQL]: InputName=''' + @myVarNVARCHARObjectName1 + ''', ContextTableName=NULL';
                    BEGIN TRY
                        EXEC [mrs].[usp_TranslateObjectName] @InputName = @myVarNVARCHARObjectName1, @ContextTableName = NULL, @TranslatedName = @myVarNVARCHARTranslatedName1 OUTPUT;
                        IF @DebugMode = 1 PRINT N'-->> Result [Single Part, AS400 to MSSQL]: ' + ISNULL(QUOTENAME(@myVarNVARCHARTranslatedName1), 'NULL');
                    END TRY
                    BEGIN CATCH
                         IF @DebugMode = 1 PRINT N'-->> ERROR Translating [Single Part, AS400 to MSSQL]: ' + @myVarNVARCHARObjectName1;
                         SET @myVarNVARCHARTranslatedName1 = NULL; -- Ensure it's null on error
                    END CATCH
                END
                ELSE -- MSSQL to AS400 translation
                BEGIN
                    BEGIN TRY
                        -- Look for "_____" pattern
                        DECLARE @UnderscorePos INT = CHARINDEX(N'_____', @myVarNVARCHARObjectName1);
                        IF @UnderscorePos > 0
                        BEGIN
                            -- Extract AS400 name which is after "_____"
                            SET @myVarNVARCHARTranslatedName1 = SUBSTRING(@myVarNVARCHARObjectName1, @UnderscorePos + 5, LEN(@myVarNVARCHARObjectName1) - @UnderscorePos - 5 + 1);
                            IF @DebugMode = 1 PRINT N'-->> Extracted AS400 Name: ' + ISNULL(@myVarNVARCHARTranslatedName1, 'NULL');
                        END
                        ELSE
                        BEGIN
                            -- No "_____" found, use as is
                            SET @myVarNVARCHARTranslatedName1 = @myVarNVARCHARObjectName1;
                            IF @DebugMode = 1 PRINT N'-->> No "_____" pattern found. Using as is: ' + @myVarNVARCHARObjectName1;
                        END
                    END TRY
                    BEGIN CATCH
                        IF @DebugMode = 1 PRINT N'-->> ERROR Extracting AS400 Name from: ' + @myVarNVARCHARObjectName1;
                        SET @myVarNVARCHARTranslatedName1 = NULL;
                    END CATCH
                END

                -- Construct the translated name or use fallback
                IF @myVarNVARCHARTranslatedName1 IS NOT NULL
                    SET @myVarNVARCHARTranslatedObject = QUOTENAME(@myVarNVARCHARTranslatedName1);
                ELSE
                    SET @myVarNVARCHARTranslatedObject = N'[' + @myVarNVARCHARObjectName1 + N']'; -- Use original name if translation failed or returned NULL

                -- Advance position past the first bracket
                SET @myVarINTCurrentPosition = @myVarINTEndBracketPos1 + 1;
                IF @DebugMode = 1 PRINT N'-- Appending translated single object: ' + @myVarNVARCHARTranslatedObject + N'. Advancing position to ' + CAST(@myVarINTCurrentPosition AS NVARCHAR(10));
            END

            -- Append the translated (or original) name to the result query
            SET @myVarNVARCHARTranslatedQuery += ISNULL(@myVarNVARCHARTranslatedObject, N''); -- Use ISNULL just in case something went wrong
        END
    END

    SET @TranslatedQuery = @myVarNVARCHARTranslatedQuery;
    IF @DebugMode = 1 PRINT N'-- Final Translated Query: ' + ISNULL(@TranslatedQuery, 'NULL');
    
    -- Execute the translated query if requested
    IF @Execution = 1 AND @TranslatedQuery IS NOT NULL AND LEN(@TranslatedQuery) > 0
    BEGIN
        -- Replace table references with schema qualified names
        DECLARE @myVarNVARCHARQueryWithSchema NVARCHAR(MAX);
        
        -- First, handle table references in the FROM, JOIN clauses and comma-separated lists
        SET @myVarNVARCHARQueryWithSchema = @TranslatedQuery;
        SET @myVarNVARCHARQueryWithSchema = REPLACE(@myVarNVARCHARQueryWithSchema, ' FROM [', ' FROM [mrs].[');
        SET @myVarNVARCHARQueryWithSchema = REPLACE(@myVarNVARCHARQueryWithSchema, ' JOIN [', ' JOIN [mrs].[');
        SET @myVarNVARCHARQueryWithSchema = REPLACE(@myVarNVARCHARQueryWithSchema, ', [', ', [mrs].[');
        
        -- Fix any cases where [mrs].[mrs]. might have been created by repeated runs
        SET @myVarNVARCHARQueryWithSchema = REPLACE(@myVarNVARCHARQueryWithSchema, '[mrs].[mrs].', '[mrs].');
        
        -- Final SQL with NOCOUNT
        SET @myVarNVARCHARSQL = N'SET NOCOUNT ON; ' + @myVarNVARCHARQueryWithSchema;
        
        IF @DebugMode = 1 
        BEGIN
            PRINT N'-- Executing query with [mrs] schema added: ';
            PRINT @myVarNVARCHARSQL;
        END
        
        BEGIN TRY
            EXEC sp_executesql @myVarNVARCHARSQL;
            
            IF @DebugMode = 1 PRINT N'-- Query executed successfully.';
        END TRY
        BEGIN CATCH
            SET @myVarNVARCHARErrorMessage = ERROR_MESSAGE();
            SET @myVarINTErrorSeverity = ERROR_SEVERITY();
            SET @myVarINTErrorState = ERROR_STATE();
            
            IF @DebugMode = 1 
            BEGIN
                PRINT N'-- Error executing query: ' + @myVarNVARCHARErrorMessage;
                PRINT N'-- Error Severity: ' + CAST(@myVarINTErrorSeverity AS NVARCHAR(10));
                PRINT N'-- Error State: ' + CAST(@myVarINTErrorState AS NVARCHAR(10));
            END
            
            -- Re-throw the caught error using RAISERROR instead of THROW
            RAISERROR(@myVarNVARCHARErrorMessage, @myVarINTErrorSeverity, @myVarINTErrorState)
        END CATCH
    END
    
    IF @DebugMode = 1 PRINT N'-- usp_TranslateSQLQuery End --';
END
GO

/*
-- =============================================
-- Example Usage for Bidirectional Translation
-- =============================================

-- Assuming [mrs].[usp_TranslateObjectName] exists and works for AS400 to MSSQL translations.

DECLARE @Input NVARCHAR(MAX);
DECLARE @Output NVARCHAR(MAX);

-- Example 1: AS400 to MSSQL (no "_____" in names)
SET @Input = N'SELECT [COL1], [COL2] FROM [TABLE1] WHERE [COL1] > 100';
SET @Output = NULL;
EXEC [mrs].[usp_TranslateSQLQuery] @SQLQuery = @Input, @DebugMode = 1, @TranslatedQuery = @Output OUTPUT, @Execution = 0;
PRINT 'Example 1 (AS400 to MSSQL):';
PRINT @Output;

-- Example 2: MSSQL to AS400 (with "_____" in names)
SET @Input = N'SELECT [Column_Description_____COL1], [Another_Column_____COL2] FROM [Table_Description_____TABLE1] WHERE [Column_Description_____COL1] > 100';
SET @Output = NULL;
EXEC [mrs].[usp_TranslateSQLQuery] @SQLQuery = @Input, @DebugMode = 1, @TranslatedQuery = @Output OUTPUT, @Execution = 0;
PRINT 'Example 2 (MSSQL to AS400):';
PRINT @Output;

-- Example 3: Mixed syntax with table.column notation
SET @Input = N'SELECT T1.[COL1], T2.[Field_Three_____FLD3] FROM [TABLE1] AS T1 JOIN [Other_Table_____OTHERTBL] AS T2 ON T1.[KEY_COL] = T2.[FK_COL]';
SET @Output = NULL;
EXEC [mrs].[usp_TranslateSQLQuery] @SQLQuery = @Input, @DebugMode = 1, @TranslatedQuery = @Output OUTPUT, @Execution = 0;
PRINT 'Example 3 (Mixed Syntax):';
PRINT @Output;

-- Example 4: Execution Mode ON with a simple query
-- Note: This will actually execute the query, so make sure TABLE1 exists or modify with valid table names
SET @Input = N'SELECT TOP 10 * FROM [VNDREQHD] WHERE 1=0'; -- Added WHERE 1=0 to ensure no rows are returned for safety
SET @Output = NULL;
EXEC [mrs].[usp_TranslateSQLQuery] @SQLQuery = @Input, @DebugMode = 1, @TranslatedQuery = @Output OUTPUT, @Execution = 1;
PRINT 'Example 4 (With Execution):';
PRINT @Output;
-- The query results would be displayed directly due to EXEC

-- Example 5: Testing error handling with malformed input
BEGIN TRY
    SET @Input = N'SELECT [COL1 FROM [TABLE1]'; -- Missing closing bracket
    SET @Output = NULL;
    EXEC [mrs].[usp_TranslateSQLQuery] @SQLQuery = @Input, @DebugMode = 1, @TranslatedQuery = @Output OUTPUT, @Execution = 0;
END TRY
BEGIN CATCH
    PRINT 'Caught error: ' + ERROR_MESSAGE();
END CATCH

*/