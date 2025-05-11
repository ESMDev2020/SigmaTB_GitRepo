USE SigmaTBLocal;
GO

-- Create the mrs schema if it doesn't exist
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'mrs')
BEGIN
    EXEC('CREATE SCHEMA [mrs]')
END
GO

-- Create the dbo schema if it doesn't exist (just in case)
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'dbo')
BEGIN
    EXEC('CREATE SCHEMA [dbo]')
END
GO

-- Script to copy all stored procedures
DECLARE @ProcName NVARCHAR(255)
DECLARE @SchemaName NVARCHAR(255)
DECLARE @SQL NVARCHAR(MAX)
DECLARE @FullProcName NVARCHAR(510)

-- Create a temporary table to hold procedure names
CREATE TABLE #Procs (
    SchemaName NVARCHAR(255),
    ProcName NVARCHAR(255)
)

-- Get all stored procedures from the linked server
INSERT INTO #Procs (SchemaName, ProcName)
SELECT 
    ROUTINE_SCHEMA,
    ROUTINE_NAME
FROM [AWS_SigmaTB].[SigmaTB].INFORMATION_SCHEMA.ROUTINES
WHERE ROUTINE_TYPE = 'PROCEDURE'
ORDER BY ROUTINE_SCHEMA, ROUTINE_NAME

-- Print summary of how many procedures were found
DECLARE @ProcCount INT
SELECT @ProcCount = COUNT(*) FROM #Procs
PRINT 'Found ' + CAST(@ProcCount AS NVARCHAR(10)) + ' stored procedures to copy'

-- Method that doesn't require RPC - Uses text directly from syscomments
CREATE TABLE #Definition (
    id int IDENTITY(1,1),
    text nvarchar(MAX)
)

-- Create a table to hold the complete procedures for execution
CREATE TABLE #CompleteProcedures (
    id int IDENTITY(1,1),
    schema_name nvarchar(255),
    proc_name nvarchar(255),
    complete_script nvarchar(MAX)
)

-- Loop through procedures to get definitions
DECLARE ProcCursor CURSOR FOR 
    SELECT SchemaName, ProcName FROM #Procs
OPEN ProcCursor
FETCH NEXT FROM ProcCursor INTO @SchemaName, @ProcName
WHILE @@FETCH_STATUS = 0
BEGIN
    SET @FullProcName = '[' + @SchemaName + '].[' + @ProcName + ']'
    
    -- Create the schema if it doesn't exist
    IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = @SchemaName)
    BEGIN
        SET @SQL = 'CREATE SCHEMA [' + @SchemaName + ']'
        EXEC (@SQL)
        PRINT 'Created schema: ' + @SchemaName
    END
    
    -- Clear previous definitions
    TRUNCATE TABLE #Definition
    
    -- Get procedure text from syscomments using OpenQuery (doesn't require RPC)
    SET @SQL = '
    INSERT INTO #Definition (text)
    SELECT text 
    FROM OPENQUERY([AWS_SigmaTB], 
        ''SELECT text 
         FROM SigmaTB.sys.syscomments 
         WHERE id = OBJECT_ID(''''SigmaTB.' + @SchemaName + '.' + @ProcName + ''''')
         ORDER BY colid'')'
    
    BEGIN TRY
        EXEC (@SQL)
        
        -- Check if we got any results
        IF EXISTS (SELECT 1 FROM #Definition)
        BEGIN
            -- Combine all lines into a complete procedure definition
            DECLARE @ProcText NVARCHAR(MAX) = ''
            
            SELECT @ProcText = @ProcText + text
            FROM #Definition
            ORDER BY id
            
            -- Build complete script with DROP and CREATE statements separated by GO
            INSERT INTO #CompleteProcedures (schema_name, proc_name, complete_script)
            VALUES (@SchemaName, @ProcName, 
                    'IF OBJECT_ID(''' + @FullProcName + ''', ''P'') IS NOT NULL
                     DROP PROCEDURE ' + @FullProcName + '
                     GO
                     
                     CREATE PROCEDURE ' + @FullProcName + ' ' + @ProcText)
            
            PRINT 'Added to execution queue: ' + @FullProcName
        END
        ELSE
        BEGIN
            PRINT 'Warning: No definition found for: ' + @FullProcName
            
            -- Create placeholder for missing definition
            INSERT INTO #CompleteProcedures (schema_name, proc_name, complete_script)
            VALUES (@SchemaName, @ProcName, 
                    'IF OBJECT_ID(''' + @FullProcName + ''', ''P'') IS NOT NULL
                     DROP PROCEDURE ' + @FullProcName + '
                     GO
                     
                     CREATE PROCEDURE ' + @FullProcName + ' AS
                     BEGIN
                         -- Original procedure definition not found
                         -- Original name: ' + @FullProcName + '
                         SELECT ''Procedure needs to be fixed'' AS Message
                     END')
            
            PRINT 'Added placeholder to queue: ' + @FullProcName
        END
    END TRY
    BEGIN CATCH
        PRINT 'Error reading definition for ' + @FullProcName + ': ' + ERROR_MESSAGE()
        
        -- Create placeholder for error case
        INSERT INTO #CompleteProcedures (schema_name, proc_name, complete_script)
        VALUES (@SchemaName, @ProcName, 
                'IF OBJECT_ID(''' + @FullProcName + ''', ''P'') IS NOT NULL
                 DROP PROCEDURE ' + @FullProcName + '
                 GO
                 
                 CREATE PROCEDURE ' + @FullProcName + ' AS
                 BEGIN
                     -- Error occurred: ' + REPLACE(ERROR_MESSAGE(), '''', '''''') + '
                     -- Original name: ' + @FullProcName + '
                     SELECT ''Procedure needs to be fixed'' AS Message
                 END')
        
        PRINT 'Added error placeholder to queue: ' + @FullProcName
    END CATCH
    
    FETCH NEXT FROM ProcCursor INTO @SchemaName, @ProcName
END

CLOSE ProcCursor
DEALLOCATE ProcCursor

-- Now execute each procedure script in a separate batch using dynamic SQL
DECLARE @id int = 1
DECLARE @max_id int = (SELECT MAX(id) FROM #CompleteProcedures)
DECLARE @curr_schema nvarchar(255)
DECLARE @curr_proc nvarchar(255)
DECLARE @script nvarchar(MAX)

WHILE @id <= @max_id
BEGIN
    SELECT 
        @curr_schema = schema_name,
        @curr_proc = proc_name,
        @script = complete_script
    FROM #CompleteProcedures
    WHERE id = @id
    
    BEGIN TRY
        -- Generate a script file instead of direct execution
        PRINT '-------------------------------------------------------------------'
        PRINT '-- PROCEDURE: [' + @curr_schema + '].[' + @curr_proc + ']'
        PRINT '-------------------------------------------------------------------'
        PRINT @script
        PRINT 'GO'
        PRINT ''
    END TRY
    BEGIN CATCH
        PRINT 'Error with procedure [' + @curr_schema + '].[' + @curr_proc + ']: ' + ERROR_MESSAGE()
    END CATCH
    
    SET @id = @id + 1
END

DROP TABLE #Procs
DROP TABLE #Definition
DROP TABLE #CompleteProcedures

PRINT 'Script generation complete! Copy the output and execute it manually to create procedures.'