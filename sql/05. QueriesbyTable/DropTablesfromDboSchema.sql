/***********************************************************************************
DROP THE TABLES FROM THE DBO SCHEMA... OLD TABLES
**************************************************************************************/

-- Step 1: List all tables in the dbo schema with creation date information
SELECT 
    t.name AS TableName,
    SCHEMA_NAME(t.schema_id) AS SchemaName,
    CONVERT(VARCHAR(20), create_date, 120) AS CreatedDate,
    CONVERT(VARCHAR(20), modify_date, 120) AS LastModifiedDate
FROM 
    sys.tables t
WHERE 
    SCHEMA_NAME(t.schema_id) = 'dbo'
ORDER BY 
    create_date ASC, name;

-- Step 2: Generate DROP TABLE statements for all tables in dbo schema
SELECT 
    'DROP TABLE [dbo].[' + t.name + '];' AS DropScript
FROM 
    sys.tables t
WHERE 
    SCHEMA_NAME(t.schema_id) = 'dbo'
ORDER BY 
    t.name;

-- Step 3: Option to drop tables older than a specific date (example: tables created before 2023)
-- Modify the date as needed
SELECT 
    'DROP TABLE [dbo].[' + t.name + '];' AS DropScript
FROM 
    sys.tables t
WHERE 
    SCHEMA_NAME(t.schema_id) = 'dbo'
    AND create_date < '2023-01-01'
ORDER BY 
    t.name;

-- Step 4: Execute all drops at once (use with extreme caution!)
DECLARE @sql NVARCHAR(MAX) = '';

SELECT @sql = @sql + 'DROP TABLE [dbo].[' + t.name + '];' + CHAR(13) + CHAR(10)
FROM sys.tables t
WHERE SCHEMA_NAME(t.schema_id) = 'dbo'
-- Uncomment to filter by date
-- AND create_date < '2023-01-01'
ORDER BY t.name;

-- Uncomment to print the statements first (recommended)
PRINT @sql;

-- Uncomment to execute the drops (use with caution!)
 --EXEC sp_executesql @sql;

