USE [SigmaTB]
GO
/** Object:  StoredProcedure [mrs].[sub_FindColumnPropertiesAndSearch]    Script Date: 5/9/2025 9:38:45 PM **/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

-- =============================================
-- Author:      Gemini AI (Modified by Claude)
-- Create date: 2025-05-04
--                FINDS COLUMNS IN OTHER TABLES LIKE THE ONE WE ARE AUDITING
--              AND OPTIONALLY SEARCHES FOR MATCHING VALUES
-- Description: Finds extended properties attached to columns within the 'mrs' schema
--              where the property name matches a given pattern (@myVarVARCHARParamColumnCode).
--              It lists the schema, table, column name, property name (interpreted as 'Column Code'),
--              property value, and now includes the minimum and maximum distinct values for each column.
--              The procedure also identifies if the column is a primary key or foreign key and checks
--              if the values match with known primary keys stored in mrs.PKRangeResults.
--              
--              ENHANCED FUNCTIONALITY: If @myVarVARCHARParamSearchValue is provided, the procedure
--              will search all matching columns for this value and return results including:
--              - HasMatches: Flag indicating if any matches found
--              - MatchCount: Number of matching rows
--              - ResultValues: Formatted JSON with all columns from matching rows
--
--              The results are ordered by the property name and match status.
-- Database:    SigmaTB
-- Schema:      mrs
--
-- Parameters:
--   @myVarVARCHARParamColumnCode NVARCHAR(128): Pattern (using LIKE) to match the extended property name (the 'Column Code').
--   @myVarBITDebugMode BIT: 1 = Print debug/progress messages, 0 = Silent execution.
--   @myVarVARCHARParamSearchValue NVARCHAR(MAX): Optional value to search for in the matching columns.
--
-- Returns:     
--   When @myVarVARCHARParamSearchValue is NULL:
--     A result set containing SchemaName, TableName (actual table name), ColumnName (actual column name),
--     PropertyName (used as 'Column Code' for filtering and sorting), PropertyValue,
--     IsPrimaryKey (Yes/No), ValuesMatchPK (Yes/No),
--     MaxDistinctValue, MinDistinctValue.
--   
--   When @myVarVARCHARParamSearchValue is provided:
--     All columns above, plus HasMatches, MatchCount, and ResultValues.
--     Results are ordered by HasMatches DESC, MatchCount DESC.
--
/*    EXECUTION

    EXEC [mrs].[sub_FindColumnPropertiesAndSearch] 
        @myVarVARCHARParamColumnCode = N'%ORD%',
        @myVarVARCHARParamSearchValue = N'968207',
        @myVarBITDebugMode = 1;

    */
-- =============================================
ALTER   PROCEDURE [mrs].[sub_FindColumnPropertiesAndSearch]
    -- === Input Parameters ===
    -- Parameter to filter the extended property name (interpreted as 'Column Code')
    @myVarVARCHARParamColumnCode NVARCHAR(128),
    -- Parameter to enable/disable debug messages (1 for debug, 0 for silent)
    @myVarBITDebugMode BIT = 0,
    -- Parameter to search for matching values in the identified columns (NULL to skip search)
    @myVarVARCHARParamSearchValue NVARCHAR(MAX) = NULL
AS
BEGIN
    -- === Local Variables ===
    -- Variable to store the start time for duration calculation in debug mode
    DECLARE @myVarDATETIMEStartTime DATETIME2;
    -- Variable for constructing debug messages
    DECLARE @myVarVARCHARMessage NVARCHAR(MAX);
    -- Variables for dynamic SQL
    DECLARE @myVarNvarSQL NVARCHAR(MAX);
    -- Variables for table and column info
    DECLARE @myVarNvarSchemaName NVARCHAR(128);
    DECLARE @myVarNvarTableName NVARCHAR(128);
    DECLARE @myVarNvarColumnName NVARCHAR(128);
    DECLARE @myVarNvarFullTableName NVARCHAR(257); -- Schema + Table with brackets

    -- Check if the PKRangeResults table exists
    DECLARE @myVarBITTableExists BIT = 0;
    IF EXISTS (SELECT 1 FROM sys.tables t 
               INNER JOIN sys.schemas s ON t.schema_id = s.schema_id 
               WHERE t.name = 'PKRangeResults' AND s.name = 'mrs')
    BEGIN
        SET @myVarBITTableExists = 1;

        IF @myVarBITDebugMode = 1
        BEGIN
            PRINT N'PKRangeResults table found - will check for PK matching.';
        END
    END
    ELSE
    BEGIN
        IF @myVarBITDebugMode = 1
        BEGIN
            PRINT N'WARNING: PKRangeResults table not found - PK checking will be skipped.';
        END
    END

    -- Create a temporary table to store results with MIN/MAX values and PK information
    CREATE TABLE #ColumnResults (
        [SchemaName] NVARCHAR(128),
        [TableName] NVARCHAR(128),
        [ColumnName] NVARCHAR(128),
        [ColumnCode] NVARCHAR(128),
        [PropertyValue] NVARCHAR(MAX),
        [IsPrimaryKey] NVARCHAR(3) DEFAULT 'No',
        [ValuesMatchPK] NVARCHAR(3) DEFAULT 'No',
        [MinDistinctValue] NVARCHAR(255),
        [MaxDistinctValue] NVARCHAR(255),
        [IsError] BIT,
        [ErrorMessage] NVARCHAR(MAX)
    );

    -- Create temporary table to store search results (when search value is provided)
    CREATE TABLE #SearchResults (
        [SchemaName] NVARCHAR(128),
        [TableName] NVARCHAR(128),
        [ColumnName] NVARCHAR(128),
        [HasMatches] BIT DEFAULT 0,
        [MatchCount] INT DEFAULT 0,
        [ResultValues] NVARCHAR(MAX)
    );

    -- Setting the start time
    SET @myVarDATETIMEStartTime = SYSUTCDATETIME(); -- Assign current UTC time to the variable

    -- Improve performance by preventing the 'xx rows affected' messages
    SET NOCOUNT ON;

    -- === Debug: Print start message ===
    -- Check if debug mode is enabled
    IF @myVarBITDebugMode = 1
    BEGIN
        -- Construct and print the start message including the timestamp
        SET @myVarVARCHARMessage = CONCAT(N'Starting execution at: ', CONVERT(VARCHAR, @myVarDATETIMEStartTime, 121));
        PRINT @myVarVARCHARMessage;
        PRINT N'-- Parameters: @myVarVARCHARParamColumnCode = ''' + ISNULL(@myVarVARCHARParamColumnCode, N'NULL') + 
              ''', @myVarBITDebugMode = ' + CAST(@myVarBITDebugMode AS VARCHAR) + 
              CASE WHEN @myVarVARCHARParamSearchValue IS NULL THEN N'' 
                   ELSE N', @myVarVARCHARParamSearchValue = ''' + @myVarVARCHARParamSearchValue + '''' END;
        PRINT N'-- Action: Searching for extended properties on columns in schema [mrs] where property name (Column Code) LIKE @myVarVARCHARParamColumnCode.';
        IF @myVarVARCHARParamSearchValue IS NOT NULL
        BEGIN
            PRINT N'-- Additional action: Searching for value ''' + @myVarVARCHARParamSearchValue + ''' in matching columns.';
        END
    END

    -- === Main Logic ===
    BEGIN TRY
        -- First, get all columns with the matching property name
        -- and insert them into our temporary results table
        INSERT INTO #ColumnResults ([SchemaName], [TableName], [ColumnName], [ColumnCode], [PropertyValue], [MinDistinctValue], [MaxDistinctValue], [IsError], [ErrorMessage])
        SELECT
            [s].[name] AS [SchemaName],         -- Schema of the table
            [t].[name] AS [TableName],          -- Actual name of the table the column belongs to
            [c].[name] AS [ColumnName],         -- Actual name of the column the property is attached to
            [ep].[name] AS [ColumnCode],        -- Name of the extended property (used as 'Column Code')
            CAST([ep].[value] AS NVARCHAR(MAX)) AS [PropertyValue], -- Value of the extended property
            NULL AS [MinDistinctValue],         -- Placeholder for minimum distinct value (to be updated)
            NULL AS [MaxDistinctValue],         -- Placeholder for maximum distinct value (to be updated)
            0 AS [IsError],                     -- Flag to indicate error status (0 = no error)
            NULL AS [ErrorMessage]              -- Field to store error messages if any
        FROM
            -- Source table for extended properties
            [sys].[extended_properties] AS [ep]
        INNER JOIN
            -- Join with columns based on object ID and column ID
            [sys].[columns] AS [c] ON [ep].[major_id] = [c].[object_id] AND [ep].[minor_id] = [c].[column_id]
        INNER JOIN
            -- Join with tables based on object ID
            [sys].[tables] AS [t] ON [c].[object_id] = [t].[object_id]
        INNER JOIN
            -- Join with schemas based on schema ID
            [sys].[schemas] AS [s] ON [t].[schema_id] = [s].[schema_id]
        WHERE
            -- Filter for properties specifically attached to columns (class=1 means object/column, minor_id > 0 means column)
            [ep].[class] = 1 AND [ep].[minor_id] > 0
            -- Filter for the specified schema 'mrs'
            AND [s].[name] = N'mrs'
            -- Filter for property names (interpreted as 'Column Code') matching the input pattern
            AND [ep].[name] LIKE @myVarVARCHARParamColumnCode;

        -- Debug: Print number of columns found
        IF @myVarBITDebugMode = 1
        BEGIN
            DECLARE @myVarINTColumnCount INT = (SELECT COUNT(*) FROM #ColumnResults);
            PRINT N'Found ' + CAST(@myVarINTColumnCount AS NVARCHAR) + N' columns with matching property name.';
        END

        -- Now, for each column, get the MIN and MAX distinct values
        -- Create a cursor to loop through each schema, table, column combination
        DECLARE column_cursor CURSOR FOR
        SELECT [SchemaName], [TableName], [ColumnName] FROM #ColumnResults;

        -- Open the cursor
        OPEN column_cursor;

        -- Fetch the first row
        FETCH NEXT FROM column_cursor INTO @myVarNvarSchemaName, @myVarNvarTableName, @myVarNvarColumnName;

        -- Loop through all rows
        WHILE @@FETCH_STATUS = 0
        BEGIN
            -- Debug: Print current column being processed
            IF @myVarBITDebugMode = 1
            BEGIN
                PRINT N'Processing column: [' + @myVarNvarSchemaName + N'].[' + @myVarNvarTableName + N'].[' + @myVarNvarColumnName + N']';
            END

            -- Construct the full table name
            SET @myVarNvarFullTableName = QUOTENAME(@myVarNvarSchemaName) + N'.' + QUOTENAME(@myVarNvarTableName);

            -- Construct dynamic SQL to get MIN and MAX values
            -- Using dynamic SQL to handle different data types and avoid conversion errors
            SET @myVarNvarSQL = N'
            BEGIN TRY
                UPDATE #ColumnResults
                SET 
                    [MinDistinctValue] = CONVERT(NVARCHAR(255), (SELECT MIN(' + QUOTENAME(@myVarNvarColumnName) + ') FROM ' + @myVarNvarFullTableName + ' WHERE ' + QUOTENAME(@myVarNvarColumnName) + ' IS NOT NULL)),
                    [MaxDistinctValue] = CONVERT(NVARCHAR(255), (SELECT MAX(' + QUOTENAME(@myVarNvarColumnName) + ') FROM ' + @myVarNvarFullTableName + ' WHERE ' + QUOTENAME(@myVarNvarColumnName) + ' IS NOT NULL)),
                    [IsError] = 0,
                    [ErrorMessage] = NULL
                WHERE
                    [SchemaName] = ''' + REPLACE(@myVarNvarSchemaName, '''', '''''') + ''' AND
                    [TableName] = ''' + REPLACE(@myVarNvarTableName, '''', '''''') + ''' AND
                    [ColumnName] = ''' + REPLACE(@myVarNvarColumnName, '''', '''''') + ''';
            END TRY
            BEGIN CATCH
                UPDATE #ColumnResults
                SET 
                    [MinDistinctValue] = ''ERROR'',
                    [MaxDistinctValue] = ''ERROR'',
                    [IsError] = 1,
                    [ErrorMessage] = ERROR_MESSAGE()
                WHERE
                    [SchemaName] = ''' + REPLACE(@myVarNvarSchemaName, '''', '''''') + ''' AND
                    [TableName] = ''' + REPLACE(@myVarNvarTableName, '''', '''''') + ''' AND
                    [ColumnName] = ''' + REPLACE(@myVarNvarColumnName, '''', '''''') + ''';
            END CATCH';

            -- Execute the dynamic SQL
            BEGIN TRY
                EXEC sp_executesql @myVarNvarSQL;

                -- Debug: Print success message
                IF @myVarBITDebugMode = 1
                BEGIN
                    PRINT N'  Successfully retrieved MIN/MAX values for column.';
                END
            END TRY
            BEGIN CATCH
                -- If the dynamic SQL execution itself fails, update the record
                UPDATE #ColumnResults
                SET 
                    [MinDistinctValue] = 'EXEC ERROR',
                    [MaxDistinctValue] = 'EXEC ERROR',
                    [IsError] = 1,
                    [ErrorMessage] = 'Execute SQL error: ' + ERROR_MESSAGE()
                WHERE
                    [SchemaName] = @myVarNvarSchemaName AND
                    [TableName] = @myVarNvarTableName AND
                    [ColumnName] = @myVarNvarColumnName;

                -- Debug: Print error message
                IF @myVarBITDebugMode = 1
                BEGIN
                    PRINT N'  ERROR executing SQL for column: ' + ERROR_MESSAGE();
                END
            END CATCH

            -- Fetch the next row
            FETCH NEXT FROM column_cursor INTO @myVarNvarSchemaName, @myVarNvarTableName, @myVarNvarColumnName;
        END

        -- Close and deallocate the cursor
        CLOSE column_cursor;
        DEALLOCATE column_cursor;

        -- Check if the column is a primary key by looking at PKRangeResults table
        IF @myVarBITTableExists = 1
        BEGIN
            -- Update IsPrimaryKey flag for columns that exist in PKRangeResults
            UPDATE cr
            SET cr.[IsPrimaryKey] = 'Yes'
            FROM #ColumnResults cr
            INNER JOIN mrs.PKRangeResults pk 
                ON pk.[TableName] = cr.[TableName]
                AND pk.[ColumnPK] = cr.[ColumnName];

            IF @myVarBITDebugMode = 1
            BEGIN
                DECLARE @myVarINTPKCount INT = (SELECT COUNT(*) FROM #ColumnResults WHERE [IsPrimaryKey] = 'Yes');
                PRINT N'Found ' + CAST(@myVarINTPKCount AS NVARCHAR) + N' primary key columns.';
            END

            -- For each column that is not a primary key, check if its values match any primary key values
            DECLARE value_match_cursor CURSOR FOR
            SELECT cr.[SchemaName], cr.[TableName], cr.[ColumnName] 
            FROM #ColumnResults cr
            WHERE cr.[IsPrimaryKey] = 'No';

            OPEN value_match_cursor;

            FETCH NEXT FROM value_match_cursor INTO @myVarNvarSchemaName, @myVarNvarTableName, @myVarNvarColumnName;

            WHILE @@FETCH_STATUS = 0
            BEGIN
                -- For each column, check if it potentially matches any primary key range in PKRangeResults
                DECLARE @myVarNvarMinValue NVARCHAR(255);
                DECLARE @myVarNvarMaxValue NVARCHAR(255);

                -- Get the min/max values for the current column
                SELECT @myVarNvarMinValue = [MinDistinctValue], @myVarNvarMaxValue = [MaxDistinctValue]
                FROM #ColumnResults 
                WHERE [SchemaName] = @myVarNvarSchemaName 
                  AND [TableName] = @myVarNvarTableName 
                  AND [ColumnName] = @myVarNvarColumnName;

                -- Skip error values
                IF @myVarNvarMinValue <> 'ERROR' AND @myVarNvarMaxValue <> 'ERROR' 
                   AND @myVarNvarMinValue <> 'EXEC ERROR' AND @myVarNvarMaxValue <> 'EXEC ERROR'
                BEGIN
                    -- If column values fall within any primary key's range, mark it as a potential foreign key
                    UPDATE cr
                    SET cr.[ValuesMatchPK] = 'Yes'
                    FROM #ColumnResults cr
                    WHERE cr.[SchemaName] = @myVarNvarSchemaName
                      AND cr.[TableName] = @myVarNvarTableName
                      AND cr.[ColumnName] = @myVarNvarColumnName
                      AND EXISTS (
                          SELECT 1 
                          FROM mrs.PKRangeResults pk
                          WHERE 
                          -- Check if the range overlaps (one of these conditions must be true)
                          -- This is a simplified check to detect potential FK relationships
                          (
                              -- Handle NULL values gracefully
                              (@myVarNvarMinValue IS NOT NULL AND pk.[LowestValue] IS NOT NULL AND 
                               @myVarNvarMaxValue IS NOT NULL AND pk.[HighestValue] IS NOT NULL)
                              AND
                              -- Simple range overlap check
                              (@myVarNvarMinValue <= pk.[HighestValue] AND @myVarNvarMaxValue >= pk.[LowestValue])
                          )
                      );
                END

                -- Debug: Print current column being checked for value matches
                IF @myVarBITDebugMode = 1
                BEGIN
                    DECLARE @myVarNvarMatchStatus NVARCHAR(3) = (
                        SELECT [ValuesMatchPK] 
                        FROM #ColumnResults 
                        WHERE [SchemaName] = @myVarNvarSchemaName 
                          AND [TableName] = @myVarNvarTableName 
                          AND [ColumnName] = @myVarNvarColumnName
                    );

                    PRINT N'Checked column for PK value match: [' + @myVarNvarSchemaName + N'].[' + 
                          @myVarNvarTableName + N'].[' + @myVarNvarColumnName + N'] - Match: ' + 
                          @myVarNvarMatchStatus;
                END

                FETCH NEXT FROM value_match_cursor INTO @myVarNvarSchemaName, @myVarNvarTableName, @myVarNvarColumnName;
            END

            CLOSE value_match_cursor;
            DEALLOCATE value_match_cursor;
        END

        -- NEW: SEARCH FUNCTIONALITY 
        -- If a search value is provided, search for it in all matching columns
        IF @myVarVARCHARParamSearchValue IS NOT NULL
        BEGIN
            IF @myVarBITDebugMode = 1
            BEGIN
                PRINT N'-- Starting search for value: ' + @myVarVARCHARParamSearchValue;
            END

            -- Initialize search results for all columns (with HasMatches = 0)
            INSERT INTO #SearchResults ([SchemaName], [TableName], [ColumnName])
            SELECT [SchemaName], [TableName], [ColumnName] 
            FROM #ColumnResults;

            -- Variables for search operation
            DECLARE @myVarBITHasMatches BIT;
            DECLARE @myVarINTMatchCount INT;
            DECLARE @myVarVARCHARResultValues NVARCHAR(MAX);

            -- Create cursor for search
            DECLARE search_cursor CURSOR FOR
            SELECT [SchemaName], [TableName], [ColumnName] FROM #ColumnResults;

            OPEN search_cursor;
            FETCH NEXT FROM search_cursor INTO @myVarNvarSchemaName, @myVarNvarTableName, @myVarNvarColumnName;

            WHILE @@FETCH_STATUS = 0
            BEGIN
                -- Debug: Print current column being searched
                IF @myVarBITDebugMode = 1
                BEGIN
                    PRINT N'-- Searching in [' + @myVarNvarSchemaName + N'].[' + @myVarNvarTableName + N'].[' + @myVarNvarColumnName + N']';
                END

                -- Construct SQL to count matches
                SET @myVarNvarSQL = N'
                DECLARE @MatchCount INT = 0;

                BEGIN TRY
                    SELECT @MatchCount = COUNT(*) 
                    FROM ' + QUOTENAME(@myVarNvarSchemaName) + N'.' + QUOTENAME(@myVarNvarTableName) + N' 
                    WHERE CAST(' + QUOTENAME(@myVarNvarColumnName) + N' AS NVARCHAR(MAX)) LIKE ''%' + REPLACE(@myVarVARCHARParamSearchValue, '''', '''''') + N'%'';

                    -- Update the match count
                    UPDATE #SearchResults
                    SET 
                        [HasMatches] = CASE WHEN @MatchCount > 0 THEN 1 ELSE 0 END,
                        [MatchCount] = @MatchCount
                    WHERE 
                        [SchemaName] = ''' + REPLACE(@myVarNvarSchemaName, '''', '''''') + ''' AND
                        [TableName] = ''' + REPLACE(@myVarNvarTableName, '''', '''''') + ''' AND
                        [ColumnName] = ''' + REPLACE(@myVarNvarColumnName, '''', '''''') + ''';
                END TRY
                BEGIN CATCH
                    -- Handle errors in search
                    UPDATE #SearchResults
                    SET 
                        [HasMatches] = 0,
                        [MatchCount] = 0,
                        [ResultValues] = ''Error counting matches: '' + ERROR_MESSAGE()
                    WHERE 
                        [SchemaName] = ''' + REPLACE(@myVarNvarSchemaName, '''', '''''') + ''' AND
                        [TableName] = ''' + REPLACE(@myVarNvarTableName, '''', '''''') + ''' AND
                        [ColumnName] = ''' + REPLACE(@myVarNvarColumnName, '''', '''''') + ''';
                END CATCH';

                -- Execute SQL to count matches
                BEGIN TRY
                    EXEC sp_executesql @myVarNvarSQL;

                    -- Get the match count for this column
                    SELECT @myVarBITHasMatches = [HasMatches], @myVarINTMatchCount = [MatchCount]
                    FROM #SearchResults
                    WHERE [SchemaName] = @myVarNvarSchemaName
                      AND [TableName] = @myVarNvarTableName
                      AND [ColumnName] = @myVarNvarColumnName;

                    -- If matches found, get the actual row data
                    IF @myVarBITHasMatches = 1
                    BEGIN
                        -- Construct SQL to get matching rows in JSON format
                        SET @myVarNvarSQL = N'
                        BEGIN TRY
                            DECLARE @Results NVARCHAR(MAX);

                            -- Get top 10 matching rows with ALL COLUMNS
                            WITH MatchedRows AS (
                                SELECT TOP 10 * 
                                FROM ' + QUOTENAME(@myVarNvarSchemaName) + N'.' + QUOTENAME(@myVarNvarTableName) + N' 
                                WHERE CAST(' + QUOTENAME(@myVarNvarColumnName) + N' AS NVARCHAR(MAX)) LIKE ''%' + REPLACE(@myVarVARCHARParamSearchValue, '''', '''''') + N'%''
                            )

                            -- Convert to JSON for easy formatting
                            SELECT @Results = (
                                SELECT * FROM MatchedRows
                                FOR JSON PATH
                            );

                            -- Update results
                            UPDATE #SearchResults
                            SET 
                                [ResultValues] = @Results
                            WHERE 
                                [SchemaName] = ''' + REPLACE(@myVarNvarSchemaName, '''', '''''') + ''' AND
                                [TableName] = ''' + REPLACE(@myVarNvarTableName, '''', '''''') + ''' AND
                                [ColumnName] = ''' + REPLACE(@myVarNvarColumnName, '''', '''''') + ''';
                        END TRY
                        BEGIN CATCH
                            UPDATE #SearchResults
                            SET 
                                [ResultValues] = ''Error formatting results: '' + ERROR_MESSAGE()
                            WHERE 
                                [SchemaName] = ''' + REPLACE(@myVarNvarSchemaName, '''', '''''') + ''' AND
                                [TableName] = ''' + REPLACE(@myVarNvarTableName, '''', '''''') + ''' AND
                                [ColumnName] = ''' + REPLACE(@myVarNvarColumnName, '''', '''''') + ''';
                        END CATCH';

                        -- Execute SQL to get matching row data
                        EXEC sp_executesql @myVarNvarSQL;

                        -- Format the JSON results for better display
                        UPDATE #SearchResults
                        SET [ResultValues] = 
                            CASE 
                                WHEN [ResultValues] LIKE 'Error%' THEN [ResultValues]
                                ELSE 
                                    'Found ' + CAST([MatchCount] AS NVARCHAR(10)) + ' matches. ' + 
                                    CASE WHEN [MatchCount] > 10 THEN 'Sample of first 10 matches:' ELSE 'All matches:' END + 
                                    CHAR(13) + CHAR(10) + 
                                    REPLACE(
                                        REPLACE(
                                            REPLACE(
                                                REPLACE([ResultValues], ',"', CHAR(13) + CHAR(10) + '    "'),
                                                '{"', '{'+ CHAR(13) + CHAR(10) + '    "'),
                                            '"}', CHAR(13) + CHAR(10) + '}'),
                                        '},', '},' + CHAR(13) + CHAR(10))
                            END
                        WHERE 
                            [SchemaName] = @myVarNvarSchemaName AND
                            [TableName] = @myVarNvarTableName AND
                            [ColumnName] = @myVarNvarColumnName;
                    END
                    ELSE
                    BEGIN
                        -- No matches found
                        UPDATE #SearchResults
                        SET [ResultValues] = 'No matches found'
                        WHERE 
                            [SchemaName] = @myVarNvarSchemaName AND
                            [TableName] = @myVarNvarTableName AND
                            [ColumnName] = @myVarNvarColumnName;
                    END

                    -- Debug: Print match count
                    IF @myVarBITDebugMode = 1
                    BEGIN
                        PRINT N'   -- Found ' + CAST(@myVarINTMatchCount AS NVARCHAR(10)) + ' matches.';
                    END
                END TRY
                BEGIN CATCH
                    -- If the dynamic SQL execution fails
                    UPDATE #SearchResults
                    SET 
                        [HasMatches] = 0,
                        [MatchCount] = 0,
                        [ResultValues] = 'Error executing search: ' + ERROR_MESSAGE()
                    WHERE 
                        [SchemaName] = @myVarNvarSchemaName AND
                        [TableName] = @myVarNvarTableName AND
                        [ColumnName] = @myVarNvarColumnName;

                    -- Debug: Print error message
                    IF @myVarBITDebugMode = 1
                    BEGIN
                        PRINT N'   -- ERROR executing search: ' + ERROR_MESSAGE();
                    END
                END CATCH

                FETCH NEXT FROM search_cursor INTO @myVarNvarSchemaName, @myVarNvarTableName, @myVarNvarColumnName;
            END

            CLOSE search_cursor;
            DEALLOCATE search_cursor;

            -- Return combined results
            SELECT 
                cr.[SchemaName],
                cr.[TableName],
                cr.[ColumnName],
                cr.[ColumnCode],
                cr.[PropertyValue],
                cr.[IsPrimaryKey],
                cr.[ValuesMatchPK],
                cr.[MinDistinctValue],
                cr.[MaxDistinctValue],
                sr.[HasMatches],
                sr.[MatchCount],
                sr.[ResultValues]
            FROM #ColumnResults cr
            INNER JOIN #SearchResults sr ON 
                cr.[SchemaName] = sr.[SchemaName] AND
                cr.[TableName] = sr.[TableName] AND
                cr.[ColumnName] = sr.[ColumnName]
            ORDER BY 
                sr.[HasMatches] DESC,
                sr.[MatchCount] DESC,
                cr.[ColumnCode] ASC;
        END
        ELSE
        BEGIN
            -- Return the original results without search
            SELECT
                [SchemaName],
                [TableName],
                [ColumnName],
                [ColumnCode],
                [PropertyValue],
                [IsPrimaryKey],
                [ValuesMatchPK],
                [MinDistinctValue],
                [MaxDistinctValue]
            FROM
                #ColumnResults
            ORDER BY
                -- Order results by Property Name ('Column Code') ascending as requested
                [ColumnCode] ASC;
        END

    END TRY
    -- === Error Handling ===
    BEGIN CATCH
        -- Close and deallocate cursors if they're still open
        IF CURSOR_STATUS('global', 'column_cursor') >= 0
        BEGIN
            CLOSE column_cursor;
            DEALLOCATE column_cursor;
        END

        IF CURSOR_STATUS('global', 'value_match_cursor') >= 0
        BEGIN
            CLOSE value_match_cursor;
            DEALLOCATE value_match_cursor;
        END

        IF CURSOR_STATUS('global', 'search_cursor') >= 0
        BEGIN
            CLOSE search_cursor;
            DEALLOCATE search_cursor;
        END

        -- Print error details if an exception occurs
        PRINT N'ERROR: An error occurred during execution.';
        PRINT N'Error Number: ' + CAST(ERROR_NUMBER() AS VARCHAR);
        PRINT N'Error Severity: ' + CAST(ERROR_SEVERITY() AS VARCHAR);
        PRINT N'Error State: ' + CAST(ERROR_STATE() AS VARCHAR);
        PRINT N'Error Procedure: ' + ISNULL(ERROR_PROCEDURE(), N'N/A');
        PRINT N'Error Line: ' + CAST(ERROR_LINE() AS VARCHAR);
        PRINT N'Error Message: ' + ERROR_MESSAGE();

        -- === Debug: Print error completion message ===
        -- Check if debug mode is enabled
        IF @myVarBITDebugMode = 1
        BEGIN
            DECLARE @myVarDATETIMEErrorTime DATETIME2 = SYSUTCDATETIME(); -- Get time of error
            -- Construct and print the error completion message
            SET @myVarVARCHARMessage = CONCAT(N'Execution failed at: ', CONVERT(VARCHAR, @myVarDATETIMEErrorTime, 121));
            PRINT @myVarVARCHARMessage;
        END;

        -- Re-throw the error so the calling application knows the procedure failed
        THROW;
    END CATCH

    -- === Debug: Print successful completion message ===
    -- Check if debug mode is enabled AND no error occurred previously
    IF @myVarBITDebugMode = 1 AND @@ERROR = 0
    BEGIN
        DECLARE @myVarDATETIMEEndTime DATETIME2 = SYSUTCDATETIME(); -- Get the end time
        DECLARE @myVarINTDurationMs INT = DATEDIFF(MILLISECOND, @myVarDATETIMEStartTime, @myVarDATETIMEEndTime); -- Calculate duration
        -- Construct and print the success message including timestamp and duration
        SET @myVarVARCHARMessage = CONCAT(N'Finished execution successfully at: ', CONVERT(VARCHAR, @myVarDATETIMEEndTime, 121), N'. Duration: ', CAST(@myVarINTDurationMs AS VARCHAR), N' ms.');
        PRINT @myVarVARCHARMessage;
    END

    -- Clean up the temporary tables
    DROP TABLE #ColumnResults;
    IF OBJECT_ID('tempdb..#SearchResults') IS NOT NULL
        DROP TABLE #SearchResults;

    -- Restore default row count behavior
    SET NOCOUNT OFF;
END;