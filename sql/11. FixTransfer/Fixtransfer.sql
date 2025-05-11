/*
-- Try a simple manual insert to test if the table allows inserts
USE SigmaTB;

-- First, check the table structure
SELECT TOP 1 * FROM mrs.z_General_Ledger_Transaction_File_____GLTRANS;

-- Then try to insert a single test record
-- (Adjust column names and values based on the actual table structure)
BEGIN TRANSACTION;
INSERT INTO mrs.z_General_Ledger_Transaction_File_____GLTRANS 
(GLPPYY /* Year field */, /* other required columns */)
VALUES 
(24 /* 2024 */, /* other values */);
-- Check if it worked
SELECT @@ROWCOUNT;
-- If it worked, roll back so we don't affect your data
ROLLBACK TRANSACTION;




-- Get table structure
SELECT 
    COLUMN_NAME, 
    DATA_TYPE, 
    IS_NULLABLE,
    COLUMN_DEFAULT
FROM 
    INFORMATION_SCHEMA.COLUMNS
WHERE 
    TABLE_SCHEMA = 'mrs' 
    AND TABLE_NAME = 'z_General_Ledger_Transaction_File_____GLTRANS'
ORDER BY 
    ORDINAL_POSITION;




USE SigmaTB;
BEGIN TRANSACTION;

INSERT INTO mrs.z_General_Ledger_Transaction_File_____GLTRANS 
(
    Record_Code_____GLRECD,
    Company_Number_____GLCOMP,
    District_Number_____GLDIST,
    Application_Code_____GLAPPL,
    G_L_Posting_Period_____GLPERD,
    G_L_Posting_Year_____GLPPYY,
    Cost_Center_____GLCSTC,
    Credit___Debit_Code_____GLCRDB,
    G_L_Account_Number_____GLACCT,
    G_L_Amount_____GLAMT
)
VALUES 
(
    'T',                     -- Record_Code
    CAST(1 AS DECIMAL(9,0)), -- Company_Number
    CAST(1 AS DECIMAL(9,0)), -- District_Number
    'GL',                    -- Application_Code
    CAST(1 AS DECIMAL(9,0)), -- G_L_Posting_Period
    CAST(24 AS DECIMAL(9,0)), -- G_L_Posting_Year (2024)
    CAST(100 AS DECIMAL(9,0)), -- Cost_Center
    'C',                     -- Credit___Debit_Code
    CAST(1000 AS DECIMAL(9,0)), -- G_L_Account_Number
    CAST(100.00 AS DECIMAL(12,2)) -- G_L_Amount
);

-- Don't use @@ROWCOUNT this time, just check visually
SELECT * FROM mrs.z_General_Ledger_Transaction_File_____GLTRANS
WHERE G_L_Posting_Year_____GLPPYY = 24;

ROLLBACK TRANSACTION;



-- First, analyze the 2024 source data to find problematic values
-- This is pseudocode - adapt to your actual source connection
SELECT 
    MAX(LEN(CAST(GLAMT AS VARCHAR(100)))) AS MaxLengthAmount,
    MAX(CASE WHEN GLAMT LIKE '%.%' THEN LEN(SUBSTRING(GLAMT, CHARINDEX('.', GLAMT) + 1, LEN(GLAMT))) ELSE 0 END) AS MaxDecimalPlaces
FROM mrs.z_General_Ledger_Transaction_File_____GLTRANS
WHERE GLPPYY = 24;




-- Alter the GL Amount column to handle the larger values in 2024 data
ALTER TABLE mrs.z_General_Ledger_Transaction_File_____GLTRANS 
ALTER COLUMN G_L_Amount_____GLAMT DECIMAL(18,4);

-- Also modify the queries amount column with the same precision
ALTER TABLE mrs.z_General_Ledger_Transaction_File_____GLTRANS 
ALTER COLUMN [G_L_Amount_-_Queries_____GLAMTQ] DECIMAL(18,4);

-- Make sure we have a clean transaction log
CHECKPOINT;



*/







-- First, get a single row from the 2024 data in GLTRANS that has a large amount value
DECLARE @GLRECD CHAR(10), @GLCOMP DECIMAL(20,0), @GLDIST DECIMAL(20,0), @GLAPPL CHAR(10), 
        @GLPERD DECIMAL(20,0), @GLPPYY DECIMAL(20,0), @GLCSTC DECIMAL(20,0), @GLCRDB CHAR(10),
        @GLACCT DECIMAL(20,0), @GLAMT DECIMAL(20,4);

-- Run this to see a sample row we can use
SELECT TOP 1 *
FROM mrs.z_General_Ledger_Transaction_File_____GLTRANS
WHERE G_L_Posting_Year_____GLPPYY = 23  -- Use 2023 data since we know it works
ORDER BY ABS(G_L_Amount_____GLAMT) DESC;  -- Get a row with a large amount value

-- Now let's try to insert a similar row but for 2024
BEGIN TRANSACTION;

INSERT INTO mrs.z_General_Ledger_Transaction_File_____GLTRANS 
(
    Record_Code_____GLRECD,
    Company_Number_____GLCOMP,
    District_Number_____GLDIST,
    Application_Code_____GLAPPL,
    G_L_Posting_Period_____GLPERD,
    G_L_Posting_Year_____GLPPYY,
    Cost_Center_____GLCSTC,
    Credit___Debit_Code_____GLCRDB,
    G_L_Account_Number_____GLACCT,
    G_L_Amount_____GLAMT
    -- Add other columns as needed based on the sample row
)
SELECT 
    Record_Code_____GLRECD,
    Company_Number_____GLCOMP,
    District_Number_____GLDIST,
    Application_Code_____GLAPPL,
    G_L_Posting_Period_____GLPERD,
    24 AS G_L_Posting_Year_____GLPPYY,  -- Change to 2024
    Cost_Center_____GLCSTC,
    Credit___Debit_Code_____GLCRDB,
    G_L_Account_Number_____GLACCT,
    G_L_Amount_____GLAMT
    -- Add other columns as needed
FROM mrs.z_General_Ledger_Transaction_File_____GLTRANS
WHERE G_L_Posting_Year_____GLPPYY = 23  -- Use 2023 data since we know it works
ORDER BY ABS(G_L_Amount_____GLAMT) DESC
OFFSET 0 ROWS FETCH NEXT 1 ROWS ONLY;

-- Check if it worked
SELECT @@ROWCOUNT;

-- Roll back so we don't affect your data
ROLLBACK TRANSACTION;