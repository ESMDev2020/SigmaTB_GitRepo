USE SigmaTB
GO


--NOooooooooo
EXEC mysp_format_query_with_descriptions @InputQuery = N'SELECT TOP(100) [SHIPMAST].[SHIPMAST], [SHIPMAST].[SH], [SHIPMAST].[SHORDN], [SHIPMAST].[Shipment], [SHIPMAST].[SHCORD], [SHIPMAST].[SHIPYY], [SHIPMAST].[SHIPMM], [SHIPMAST].[SHIPDD], [SHIPMAST].[SHSHAP], [SHIPMAST].[shape], [SHIPMAST].[SHINSM], [SHIPMAST].[SHSQTY], [SHIPMAST].[Shipped], [SHIPMAST].[SHUOM], [SHIPMAST].[SHBQTY], [SHIPMAST].[SHBUOM], [SHIPMAST].[SHOINC], [SHIPMAST].[SHOQTY], [SHIPMAST].[SHOUOM], [SHIPMAST].[SHTLBS], [SHIPMAST].[SHTPCS], [SHIPMAST].[SHTFTS], [SHIPMAST].[SHTSFT], [SHIPMAST].[SHTMTR], [SHIPMAST].[SHTKG], [SHIPMAST].[SHPRCG], [SHIPMAST].[SHHAND], [SHIPMAST].[SHMSLS], [SHIPMAST].[SHMSLD], [SHIPMAST].[SHFSLS], [SHIPMAST].[SHFSLD], [SHIPMAST].[SHPSLS], [SHIPMAST].[SHPSLD], [SHIPMAST].[SHOSLS], [SHIPMAST].[SHOSLD], [SHIPMAST].[SHDSLS], [SHIPMAST].[SHDSLD], [SHIPMAST].[SHMCSS], [SHIPMAST].[SHMCSD], [SHIPMAST].[SHSLSS], [SHIPMAST].[SHSLSD], [SHIPMAST].[SHSWGS], [SHIPMAST].[SHSWGD], [SHIPMAST].[SHADPC], [SHIPMAST].[SHUNSP], [SHIPMAST].[SHUUOM], [SHIPMAST].[SHSCDL], [SHIPMAST].[SHSCLB], [SHIPMAST].[SHSCKG], [SHIPMAST].[SHTRCK], [SHIPMAST].[SHBCTY], [SHIPMAST].[SHSCTY], [SHIPMAST].[SHIP-TO], [SHIPMAST].[SHDPTI], [SHIPMAST].[SHDPTO], [SHIPMAST].[SHCSTO], [SHIPMAST].[SHADR1], [SHIPMAST].[SHADR2], [SHIPMAST].[SHADR3], [SHIPMAST].[SHCITY], [SHIPMAST].[SHSTAT], [SHIPMAST].[SHZIP]
FROM [SHIPMAST]'

--Rename
EXEC sp_rename 'mrs.sp_format_query_with_descriptions', 'mysp_format_query_with_descriptions';


EXEC mysp_format_query_with_descriptions @InputQuery = N'SELECT TOP(100) ... FROM [SHIPMAST]'

/********************************************************
CHECK XP PROPERTIES
*********************************************************/
/*****************************************
Check extended properties for 1 table or column
*****************************************/

SELECT * FROM sys.tables WHERE name like '%APWK856%'

SELECT * FROM sys.columns WHERE name like '%BSORDR%'
SELECT * FROM sys.tables WHERE name like 'z_A/P_Check_Register_Work_File_____APWK856'
select * from sys.extended_properties where name like '%BSORDR%'
z_A/P_Check_Register_Work_File_____APWK856
z_A/P_Check_Register_Work_File_____APWK856
z_A/P_Check_Register_Work_File_____APWK856

USE SigmaTB;
GO

SELECT
    t.name AS table_name,         -- Table Name
    tp.name AS table_prop_name,   -- Table Extended Property Name
    tp.value AS table_prop_value,  -- Table Extended Property Value
    c.name AS column_name,        -- Column Name
    cp.name AS column_prop_name,  -- Column Extended Property Name
    cp.value AS column_prop_value -- Column Extended Property Value
FROM
    sys.schemas AS s
INNER JOIN
    sys.tables AS t ON s.schema_id = t.schema_id
LEFT JOIN -- Join for table extended properties
    sys.extended_properties AS tp ON t.object_id = tp.major_id
                                 AND tp.minor_id = 0 -- Indicates property is on the table itself
                                 AND tp.class = 1    -- Class 1 = Object or Column
LEFT JOIN -- Join for columns within the table
    sys.columns AS c ON t.object_id = c.object_id
LEFT JOIN -- Join for column extended properties
    sys.extended_properties AS cp ON c.object_id = cp.major_id
                                 AND c.column_id = cp.minor_id -- Link property to the specific column
                                 AND cp.class = 1    -- Class 1 = Object or Column
WHERE
    s.name = 'mrs'  -- Filter for the 'mrs' schema
ORDER BY
    t.name,         -- Group results primarily by table name
    c.column_id;    -- Within each table, order by column position

    
SELECT ep.*
FROM sys.extended_properties ep
JOIN sys.objects o ON ep.major_id = o.object_id
WHERE o.name = 'z_A/P_Check_Register_Work_File_____APWK856'


--EXEC my_sp_getXPfromObjects @InputSearchTerm = 'YourTableOrColumnCode';       -- Old version
--EXEC my_sp_getXPfromObjects @InputSearchTerm = 'GLTRANS';                     -- Old version

--Column
EXEC my_sp_getXPfromObjects @lookfor = '[GLTRANS].[GLACCT]', @isobject = 'column', @returnvalue = 'name';
EXEC my_sp_getXPfromObjects @lookfor = '[GLTRANS].[GLACCT]', @isobject = 'column', @returnvalue = 'code';
--233767890


--Table 
EXEC my_sp_getXPfromObjects @lookfor = '[GLTRANS].[GLACCT]', @isobject = 'table', @returnvalue = 'name';
EXEC my_sp_getXPfromObjects @lookfor = '[GLTRANS].[GLACCT]', @isobject = 'table', @returnvalue = 'code';

--Table
EXEC my_sp_getXPfromObjects @lookfor = '[GLTRANS]', @isobject = 'table', @returnvalue = 'name';
EXEC my_sp_getXPfromObjects @lookfor = '[GLTRANS]', @isobject = 'table', @returnvalue = 'code';


/***************************************************************
WHAT STORED PROCEDURES
***************************************************************/
-- What stored procedures?
SELECT
    SCHEMA_NAME(schema_id) AS SchemaName, -- Gets the schema name (e.g., 'mrs')
    name AS ProcedureName,                 -- The name of the stored procedure
    create_date,                           -- When it was created
    modify_date                            -- When it was last modified
FROM
    sys.procedures
-- Optional: Filter by schema if you usually create them in a specific one
-- WHERE SCHEMA_NAME(schema_id) = 'YourSchemaName'
ORDER BY
    Modify_date DESC,
    SchemaName,
    ProcedureName;

/***************************************************************
LIST OF STORED PROCEDURES
***************************************************************/
mysp_analyze_table_columns    'SHIPMAST'        --Provides the count of unique values for all the columns

-- ROWCOUNT by unique value by 1 column
EXEC mysp_find_unique_values_table_column_by_code
    @InputTableCode = 'SHIPMAST',
    @InputColumnCode = 'SHPFLG',
    @InputColumnDescription = 'Shipment Flag'
    

EXEC my_sp_getXPfromObjects  'SHIPMAST', 'table', 'code'        -- bad
EXEC my_sp_getXPfromObjects @lookfor = '[GLTRANS].[GLACCT]', @isobject = 'column', @returnvalue = 'name';

EXEC mysp_find_table_column_by_code    'SHIPMAST', 'SHPFLG'  --fails
--woC mysp_format_query_with_descriptions 'SELECT TOP(100) [SHIPMAST].[SHIPMAST], [SHIPMAST].[SH], [SHIPMAST].[SHORDN], [SHIPMAST].[Shipment], [SHIPMAST].[SHCORD], [SHIPMAST].[SHIPYY], [SHIPMAST].[SHIPMM], [SHIPMAST].[SHIPDD], [SHIPMAST].[SHSHAP], [SHIPMAST].[shape], [SHIPMAST].[SHINSM], [SHIPMAST].[SHSQTY], [SHIPMAST].[Shipped], [SHIPMAST].[SHUOM], [SHIPMAST].[SHBQTY]'

DECLARE @output_query NVARCHAR(MAX); 
EXEC mrs.my_sp_translate_sql_query @input_query = 'SELECT TOP(100) [SHIPMAST].[SHIPMAST], [SHIPMAST].[SH], [SHIPMAST].[SHORDN], [SHIPMAST].[Shipment], [SHIPMAST].[SHCORD], [SHIPMAST].[SHIPYY], [SHIPMAST].[SHIPMM], [SHIPMAST].[SHIPDD], [SHIPMAST].[SHSHAP], [SHIPMAST].[shape], [SHIPMAST].[SHINSM], [SHIPMAST].[SHSQTY], [SHIPMAST].[Shipped], [SHIPMAST].[SHUOM], [SHIPMAST].[SHBQTY]', @translated_query = @output_query OUTPUT
SELECT @output_query AS TranslatedQuery;

EXEC dbo.sp_translate_sql_query
EXEC mrs.sp_translate_sql_query
EXEC my_sp_getAllColumnXPfromTables
EXEC mysp_format_query_with_descriptions
EXEC my_sp_getXPfromObjects                     --old

    @input_query NVARCHAR(MAX),
    @translated_query NVARCHAR(MAX) OUTPUT

USE Sigmatb;
EXEC mrs.usp_TranslateName @InputName = 'SPHEADER'

select top(10) * from [mrs].[01_AS400_MSSQL_Equivalents]


--Exec the SP to translate Column
EXEC my_sp_getXPfromObjects @lookfor = '[GLTRANS].[GLACCT]', @isobject = 'column', @returnvalue = 'name';
EXEC my_sp_getXPfromObjects @lookfor = '[GLTRANS].[GLACCT]', @isobject = 'column', @returnvalue = 'code';
EXEC my_sp_getXPfromObjects @lookfor = '[z_General_Ledger_Transaction_File_____GLTRANS].[G/L_Account_Number_____GLACCT]', @isobject = 'column', @returnvalue = 'code';
-- needs work

--233767890


--Table 
EXEC my_sp_getXPfromObjects @lookfor = '[GLTRANS].[GLACCT]', @isobject = 'table', @returnvalue = 'name';
EXEC my_sp_getXPfromObjects @lookfor = '[GLTRANS].[GLACCT]', @isobject = 'table', @returnvalue = 'code';

--Table - Get name or code from code
EXEC my_sp_getXPfromObjects @lookfor = '[GLTRANS]', @isobject = 'table', @returnvalue = 'name';
EXEC my_sp_getXPfromObjects @lookfor = '[GLTRANS]', @isobject = 'table', @returnvalue = 'code';

--Table - Get name or code from name
EXEC my_sp_getXPfromObjects @lookfor = '[z_General_Ledger_Transaction_File_____GLTRANS]', @isobject = 'table', @returnvalue = 'name';
EXEC my_sp_getXPfromObjects @lookfor = '[z_General_Ledger_Transaction_File_____GLTRANS]', @isobject = 'table', @returnvalue = 'code';


-- 
-- G/L_Account_Number_____GLACCT

DECLARE @input_query NVARCHAR(MAX); DECLARE  @translated_query NVARCHAR(MAX);
EXEC dbo.sp_translate_sql_query  @input_query  = 'Select * from VNDREQHD', @translated_query = @translated_query OUTPUT
SELECT @translated_query;

EXEC mrs.sp_translate_sql_query
EXEC my_sp_getAllColumnXPfromTables
EXEC mysp_format_query_with_descriptions
EXEC my_sp_getXPfromObjects                     --old

/**************************************************************************/
--CHECK all extended properties
-- Query for extended properties in mrs schema
SELECT
    SCHEMA_NAME(o.schema_id) AS [SchemaName],
    o.name AS [ObjectName],
    CASE o.type
        WHEN 'U' THEN 'Table'
        WHEN 'V' THEN 'View'
        WHEN 'P' THEN 'Stored Procedure'
        WHEN 'FN' THEN 'Function'
        ELSE o.type_desc 
    END AS [ObjectType],
    CASE 
        WHEN c.name IS NULL THEN 'Object-level' 
        ELSE 'Column: ' + c.name 
    END AS [PropertyLevel],
    ep.name AS [PropertyName],
    CAST(ep.value AS NVARCHAR(MAX)) AS [PropertyValue]
FROM 
    sys.objects o
JOIN 
    sys.extended_properties ep ON ep.major_id = o.object_id
LEFT JOIN 
    sys.columns c ON ep.major_id = c.object_id AND ep.minor_id = c.column_id
WHERE 
    SCHEMA_NAME(o.schema_id) = 'mrs'
    AND o.type IN ('U', 'V') -- Tables and Views
ORDER BY 
    o.name, c.name, ep.name;
    /**************************************************************************/


    /**************************************************************************/
    -- Check extended properties for specific tables
SELECT 
    t.name AS TableName,
    ep.name AS PropertyName,
    CAST(ep.value AS NVARCHAR(MAX)) AS PropertyValue
FROM 
    sys.tables t
JOIN 
    sys.extended_properties ep ON ep.major_id = t.object_id AND ep.minor_id = 0
WHERE 
    SCHEMA_NAME(t.schema_id) = 'mrs'
    AND (t.name LIKE '%Customer%' OR ep.name LIKE '%ARCUST%')
ORDER BY 
    t.name;

-- Check the 01_AS400_MSSQL_Equivalents table for the same tables
SELECT 
    [AS400_TableName],
    [TABLEDESCRIPTION],
    [MSSQL_TableName]
FROM 
    [mrs].[01_AS400_MSSQL_Equivalents]
WHERE 
    [AS400_TableName] LIKE '%CUST%' OR [MSSQL_TableName] LIKE '%Customer%';

    /*****************************************************************************/
    /*****************************************************************************/


--DECLARE @input NVARCHAR(MAX) = N'SELECT c.[CustomerName], o.[OrderDate] FROM [dbo].[Customers] AS c JOIN [dbo].[Orders] AS o ON c.[CustomerID] = o.[CustomerID] WHERE c.[CustomerID] > 10;';

/*************************************************************************************
TRANSLATE ONE QUERY
***************************************************************************************/

SELECT * from [mrs].[01_AS400_MSSQL_Equivalents]



USE Sigmatb;
EXEC mrs.usp_TranslateName @InputName = 'SPHEADER'

--Returns several queries
EXEC mrs.[mysp_QuerySelector]

select top(10) * from [mrs].[01_AS400_MSSQL_Equivalents]


/**************************************************
CLAUDE. FIND COLUMNS IN OTHER TABLES LIKE THE ONE WE ARE AUDITING
****************************************************/

	EXEC [mrs].[sub_FindColumnPropertiesAndSearch] 
	    @myVarVARCHARParamColumnCode = N'%ORD%',
	    @myVarVARCHARParamSearchValue = N'968207',
	    @myVarBITDebugMode = 1;


/**************************************************
CLAUDE. FIND PK IN DATABASE, AND UPDATE MAX,MIN RANGES
****************************************************/
/*
Example usage:
-- Mode 1: Identify PKs and analyze ranges (starting fresh)
EXEC [mrs].[PKIdentificationAndAnalysis] 
    @myVarBitDebugMode = 1, 
    @myVarBitUseExtendedProps = 0, 
    @myVarIntIdentificationMode = 1, 
    @myVarBitExecuteFromZero = 1;

-- Mode 1: Identify PKs and analyze ranges (resume/append)
EXEC [mrs].[PKIdentificationAndAnalysis] 
    @myVarBitDebugMode = 1, 
    @myVarBitUseExtendedProps = 0, 
    @myVarIntIdentificationMode = 1, 
    @myVarBitExecuteFromZero = 0;

-- Mode 2: Only analyze ranges (using existing PKCheckResults)
EXEC [mrs].[PKIdentificationAndAnalysis] 
    @myVarBitDebugMode = 1, 
    @myVarBitUseExtendedProps = 0, 
    @myVarIntIdentificationMode = 2, 
    @myVarBitExecuteFromZero = 1;

-- Silent execution with extended properties
EXEC [mrs].[PKIdentificationAndAnalysis] 
    @myVarBitDebugMode = 0, 
    @myVarBitUseExtendedProps = 1, 
    @myVarIntIdentificationMode = 1, 
    @myVarBitExecuteFromZero = 1;

-- View all PK identification results
SELECT * FROM [mrs].[PKCheckResults] ORDER BY [TableName];

-- View all range analysis results
SELECT * FROM [mrs].[PKRangeResults] ORDER BY [TableName];

-- View only successful range analyses
SELECT * FROM [mrs].[PKRangeResults] WHERE [IsError] = 0 ORDER BY [TableName];

-- View only errors
SELECT * FROM [mrs].[PKRangeResults] WHERE [IsError] = 1 ORDER BY [TableName];

-- Example resultset from PKCheckResults:
-- TableName                  | RowCount | Comment   | ColumnPK
-- ----------------------------------------------------------
-- z_Customer_Master_File     | 5000     | PK found  | CUSTOMER_NUMBER_____CCUST
-- z_General_Ledger_File      | 10000    | PK found  | GL_ACCOUNT_____ACCT
-- z_Product_Master_File      | 2500     | no PK found | NULL

-- Example resultset from PKRangeResults:
-- TableName | TableCode | ColumnPK | ColumnCode | TotalRows | Comment | LowestValue | HighestValue | IsError | ErrorMessage
-- ----------------------------------------------------------------------------------------------------------------------------------------
-- z_Customer_Master_File | ARCUST | CUSTOMER_NUMBER_____CCUST | CCUST | 5000 | PK found | 10000 | 99999 | 0 | NULL
-- z_General_Ledger_File  | GLTRANS | GL_ACCOUNT_____ACCT | ACCT | 10000 | PK found | 100-1000 | 999-9999 | 0 | NULL
*/



/*************************************************/
/*************************************************************************************
TRANSLATE ONE QUERY
***************************************************************************************/
DECLARE @output NVARCHAR(MAX); DECLARE @SQLQuery NVARCHAR(MAX)
--DECLARE @input NVARCHAR(MAX) = N'SELECT DISTINCT ''customer summary'', [ARCUST].[CDIST] * 100000 + [ARCUST].[CCUST], [ARCUST].[CALPHA], [ARCUST].[CLIMIT], [ARCUST].[CISMD1] * 100 + [ARCUST].[CISLM1], [ARCUST].[CSMDI1] * 100 + [ARCUST].[CSLMN1], [SALESMAN].[SMNAME] FROM [ARCUST] [ARCUST], [SALESMAN] [SALESMAN] WHERE [ARCUST].[CISMD1] = [SALESMAN].[SMDIST] AND [ARCUST].[CISLM1] = [SALESMAN].[SMSMAN] ORDER BY [ARCUST].[CALPHA];';
--DECLARE @input NVARCHAR(MAX) = N'SET NOCOUNT ON; SELECT DISTINCT ''customer summary'', [mrs].[z_Customer_Master_File_____ARCUST].[CUSTOMER_DISTRICT_NUMBER_____CDIST] * 100000 + [mrs].[z_Customer_Master_File_____ARCUST].[CUSTOMER_NUMBER_____CCUST], [mrs].[z_Customer_Master_File_____ARCUST].[Customer_Alpha_Name_____CALPHA], [mrs].[z_Customer_Master_File_____ARCUST].[Credit_Limit_____CLIMIT], [mrs].[z_Customer_Master_File_____ARCUST].[Inside_Salesman_District_Number_____CISMD1] * 100 + [mrs].[z_Customer_Master_File_____ARCUST].[Inside_Salesman_Number_____CISLM1], [mrs].[z_Customer_Master_File_____ARCUST].[Salesman_One_District_Number_____CSMDI1] * 100 + [mrs].[z_Customer_Master_File_____ARCUST].[Salesman_One_Number_____CSLMN1], [mrs].[z_Salesman_Master_File_____SALESMAN].[Salesman_Name_____SMNAME] FROM [mrs].[z_Customer_Master_File_____ARCUST] [z_Customer_Master_File_____ARCUST], [mrs].[z_Salesman_Master_File_____SALESMAN] [z_Salesman_Master_File_____SALESMAN] WHERE [z_Customer_Master_File_____ARCUST].[Inside_Salesman_District_Number_____CISMD1] = [z_Salesman_Master_File_____SALESMAN].[Salesman_District_Number_____SMDIST] AND [z_Customer_Master_File_____ARCUST].[Inside_Salesman_Number_____CISLM1] = [z_Salesman_Master_File_____SALESMAN].[Salesman_Number_____SMSMAN] ORDER BY [z_Customer_Master_File_____ARCUST].[Customer_Alpha_Name_____CALPHA];'
DECLARE @input NVARCHAR(MAX) = N'SELECT [GACDES], [GARP3] FROM [mrs].[GLACCT]; SELECT [GLACCT], [GLAPPL], [GLDESC], [GLPGM], [GLRECD], [GLREF], [GLRP#], [GLRPTY], [GLUSER] FROM [mrs].[GLDEBCRED]; SELECT [GLACCT], [GLAMTQ], [GLAPPL], [GLDESC], [GLPGM], [GLRECD], [GLREF], [GLRP#], [GLRPTY], [GLTRDS], [GLTRN#], [GLTRNT], [GLTYPE], [GLUSER] FROM [mrs].[GLTRANS];';

DECLARE @DebugMode INT; DECLARE @Execution INT;
-- Execute the procedure
--  EXEC dbo.sp_translate_sql_query @input_query = @input, @translated_query = @output OUTPUT;  -- translate with spaces
--  EXEC mrs.sp_translate_sql_query @input_query = @input, @translated_query = @output OUTPUT;  -- translate with spaces
-- EXEC [mrs].[my_sp_translate_sql_query] @input_query = @input, @translated_query = @output OUTPUT;  -- translate with spaces
 --EXEC [mrs].[usp_TranslateSQLQuery] @p_InputQuery = @input,  @p_TranslatedQuery = @output OUTPUT --, @Execution = 1; --v2
 EXEC [mrs].[usp_TranslateSQLQuery] @SQLQuery = @input,  @TranslatedQuery = @output OUTPUT, @DebugMode = 1, @Execution = 1; --, @Execution = 1; --V4
SELECT @output


SET NOCOUNT ON; SELECT DISTINCT 'customer summary', [mrs].[z_Customer_Master_File_____ARCUST].[CUSTOMER_DISTRICT_NUMBER_____CDIST] * 100000 + [z_Customer_Master_File_____ARCUST].[CUSTOMER_NUMBER_____CCUST], [mrs].[z_Customer_Master_File_____ARCUST].[Customer_Alpha_Name_____CALPHA], [mrs].[z_Customer_Master_File_____ARCUST].[Credit_Limit_____CLIMIT], [mrs].[z_Customer_Master_File_____ARCUST].[Inside_Salesman_District_Number_____CISMD1] * 100 + [z_Customer_Master_File_____ARCUST].[Inside_Salesman_Number_____CISLM1], [mrs].[z_Customer_Master_File_____ARCUST].[Salesman_One_District_Number_____CSMDI1] * 100 + [z_Customer_Master_File_____ARCUST].[Salesman_One_Number_____CSLMN1], [mrs].[z_Salesman_Master_File_____SALESMAN].[Salesman_Name_____SMNAME] FROM [mrs].[z_Customer_Master_File_____ARCUST] [z_Customer_Master_File_____ARCUST], [mrs].[z_Salesman_Master_File_____SALESMAN] [z_Salesman_Master_File_____SALESMAN] WHERE [z_Customer_Master_File_____ARCUST].[Inside_Salesman_District_Number_____CISMD1] = [z_Salesman_Master_File_____SALESMAN].[Salesman_District_Number_____SMDIST] AND [z_Customer_Master_File_____ARCUST].[Inside_Salesman_Number_____CISLM1] = [z_Salesman_Master_File_____SALESMAN].[Salesman_Number_____SMSMAN] ORDER BY [z_Customer_Master_File_____ARCUST].[Customer_Alpha_Name_____CALPHA];
SET NOCOUNT ON; SELECT DISTINCT 'customer summary' AS Summary, cust.[CUSTOMER_DISTRICT_NUMBER_____CDIST] * 100000 + cust.[CUSTOMER_NUMBER_____CCUST] AS CustomerID, cust.[Customer_Alpha_Name_____CALPHA] AS CustomerName, cust.[Credit_Limit_____CLIMIT] AS CreditLimit, cust.[Inside_Salesman_District_Number_____CISMD1] * 100 + cust.[Inside_Salesman_Number_____CISLM1] AS InsideSalesmanID, cust.[Salesman_One_District_Number_____CSMDI1] * 100 + cust.[Salesman_One_Number_____CSLMN1] AS SalesmanOneID, sm.[Salesman_Name_____SMNAME] AS SalesmanName FROM [mrs].[z_Customer_Master_File_____ARCUST] AS cust, [mrs].[z_Salesman_Master_File_____SALESMAN] AS sm WHERE cust.[Inside_Salesman_District_Number_____CISMD1] = sm.[Salesman_District_Number_____SMDIST] AND cust.[Inside_Salesman_Number_____CISLM1] = sm.[Salesman_Number_____SMSMAN] ORDER BY CustomerName;








