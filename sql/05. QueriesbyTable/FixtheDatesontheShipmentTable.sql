/******************************************************************************************
FIX THE DATES ON THE SHIPMENT TABLE
*******************************************************************************************/

/*
SELECT top 10 *
FROM [mrs].[ShipmentOrderDetails]


SELECT count(*)
FROM [mrs].[ShipmentOrderDetails]


-- Name: Inspect_FormattedShipDate_Values
-- Description: Examines the unique date formats in the ShipmentOrderDetails table
-- Output: Displays unique date formats and their counts

SELECT 
    [FormattedShipDate], 
    COUNT(*) AS [RecordCount]
FROM [mrs].[ShipmentOrderDetails]
GROUP BY [FormattedShipDate]
ORDER BY COUNT(*) DESC;

*/
-------------------------------------------------------------
-- Correct the date format

-- Name: Select_ShipmentOrderDetails_SimplifiedDateParsing
-- Description: Comprehensive date parsing with simplified CASE statements
-- Output: Returns all records with properly parsed date components

/*
		WITH [CTE_CleanFormat] AS (
			SELECT
				*,
				RTRIM([FormattedShipDate]) AS [CleanedFormat]
			FROM [mrs].[ShipmentOrderDetails]
		),
		[CTE_Components] AS (
			SELECT
				*,
				-- Extract year (always the first 4 characters)
				CASE
					WHEN LEFT([CleanedFormat], 3) LIKE '[0-9][0-9][0-9]' AND SUBSTRING([CleanedFormat], 4, 1) = '.'
					THEN 
						CASE 
							WHEN LEFT([CleanedFormat], 1) = '2' THEN '20' + LEFT([CleanedFormat], 2)
							ELSE '19' + LEFT([CleanedFormat], 2)
						END
					ELSE LEFT([CleanedFormat], 4)
				END AS [Year],
        
				-- Extract the remaining part after year and first period
				CASE 
					WHEN CHARINDEX('.', [CleanedFormat]) > 0
					THEN SUBSTRING([CleanedFormat], 
								  CHARINDEX('.', [CleanedFormat]) + 1,
								  LEN([CleanedFormat]))
					ELSE NULL
				END AS [AfterYear]
			FROM [CTE_CleanFormat]
		),
		[CTE_SimplifiedComponents] AS (
			SELECT
				*,
				REPLACE([AfterYear], '.', '') AS [CleanText],
				CASE WHEN CHARINDEX('.', [AfterYear]) > 0 THEN 1 ELSE 0 END AS [HasPeriod]
			FROM [CTE_Components]
		),
		[CTE_ParsedComponents] AS (
			SELECT
				*,
				-- Simplified month extraction
				CASE
					WHEN [AfterYear] IS NULL THEN '01'
					-- 5-digit case (e.g. "01027")
					WHEN LEN([CleanText]) = 5 AND ISNUMERIC([CleanText]) = 1 THEN LEFT([CleanText], 2)
					-- 4-digit case (e.g. "0119")
					WHEN LEN([CleanText]) = 4 AND ISNUMERIC([CleanText]) = 1 THEN LEFT([CleanText], 2)
					-- With period separator (e.g. "01.25")
					WHEN [HasPeriod] = 1 THEN 
						LEFT([AfterYear], 
						CASE WHEN CHARINDEX('.', [AfterYear]) > 0 
							 THEN CHARINDEX('.', [AfterYear]) - 1 
							 ELSE LEN([AfterYear]) 
						END)
					-- 3-digit case (e.g. "125")
					WHEN LEN([CleanText]) = 3 AND ISNUMERIC([CleanText]) = 1 THEN LEFT([CleanText], 1)
					-- Default
					ELSE [CleanText]
				END AS [Month],
        
				-- Simplified day extraction
				CASE
					WHEN [AfterYear] IS NULL THEN '01'
					-- 5-digit case
					WHEN LEN([CleanText]) = 5 AND ISNUMERIC([CleanText]) = 1 THEN RIGHT([CleanText], 3)
					-- 4-digit case
					WHEN LEN([CleanText]) = 4 AND ISNUMERIC([CleanText]) = 1 THEN RIGHT([CleanText], 2)
					-- With period separator
					WHEN [HasPeriod] = 1 AND CHARINDEX('.', [AfterYear]) < LEN([AfterYear]) THEN
						SUBSTRING([AfterYear], 
								  CHARINDEX('.', [AfterYear]) + 1,
								  LEN([AfterYear]))
					-- 3-digit case
					WHEN LEN([CleanText]) = 3 AND ISNUMERIC([CleanText]) = 1 THEN RIGHT([CleanText], 2)
					-- Default
					ELSE '01'
				END AS [Day]
			FROM [CTE_SimplifiedComponents]
		),
		[CTE_CleanedComponents] AS (
			SELECT
				*,
				-- Clean month
				CASE
					WHEN [Month] IS NULL THEN '01'
					WHEN ISNUMERIC(REPLACE([Month], '.', '')) = 0 THEN '01'
					WHEN LEN(REPLACE([Month], '.', '')) > 2 THEN LEFT(REPLACE([Month], '.', ''), 2)
					ELSE REPLACE([Month], '.', '')
				END AS [CleanedMonth],
        
				-- Clean day
				CASE
					WHEN [Day] IS NULL THEN '01'
					WHEN ISNUMERIC(REPLACE([Day], '.', '')) = 0 THEN '01'
					WHEN LEN(REPLACE([Day], '.', '')) = 3 AND LEFT(REPLACE([Day], '.', ''), 1) = '0' 
						 THEN RIGHT(REPLACE([Day], '.', ''), 2)
					ELSE REPLACE([Day], '.', '')
				END AS [CleanedDay]
			FROM [CTE_ParsedComponents]
		)
		SELECT
			[FormattedShipDate],
			[CleanedFormat],
			[Year],
			[AfterYear],
			[Month],
			[Day] AS [Raw_Day],
			[CleanedMonth] AS [Cleaned_Month],
			[CleanedDay] AS [Cleaned_Day],
			-- Format final date correctly as YYYY-MM-DD
			[Year] + '-' + 
			RIGHT('0' + [CleanedMonth], 2) + '-' + 
			RIGHT('0' + [CleanedDay], 2) AS [Formatted_Date],
    
			-- Convert to proper DATE type
			TRY_CONVERT(DATE, 
				[Year] + '-' + 
				RIGHT('0' + [CleanedMonth], 2) + '-' + 
				RIGHT('0' + [CleanedDay], 2)) 
				AS [Sortable_Date_____SORTDAT]
		FROM [CTE_CleanedComponents]
		ORDER BY [Sortable_Date_____SORTDAT];

*/

/*****************************************************************************************
NOW THAT THE DATE FORMAT IS CORRECTED, WE CREATE A QUERY TO UPDATE THE TABLE
******************************************************************************************/

		-- Name: Update_ShipmentOrderDetails_StandardizeDates
		-- Description: Updates FormattedShipDate to consistent YYYY-MM-DD format
		-- Input: None
		-- Output: Updates table with standardized dates

		-- Step 1: First let's check if the column exists and create it if needed
		BEGIN TRANSACTION;

		-- Simplify it to just update the date format without creating a backup column
		;WITH [CTE_CleanFormat] AS (
			SELECT
				*,
				RTRIM([FormattedShipDate]) AS [CleanedFormat]
			FROM [mrs].[ShipmentOrderDetails]
		),
		[CTE_Components] AS (
			SELECT
				*,
				CASE
					WHEN LEFT([CleanedFormat], 3) LIKE '[0-9][0-9][0-9]' AND SUBSTRING([CleanedFormat], 4, 1) = '.'
					THEN 
						CASE 
							WHEN LEFT([CleanedFormat], 1) = '2' THEN '20' + LEFT([CleanedFormat], 2)
							ELSE '19' + LEFT([CleanedFormat], 2)
						END
					ELSE LEFT([CleanedFormat], 4)
				END AS [Year],
        
				CASE 
					WHEN CHARINDEX('.', [CleanedFormat]) > 0
					THEN SUBSTRING([CleanedFormat], 
								  CHARINDEX('.', [CleanedFormat]) + 1,
								  LEN([CleanedFormat]))
					ELSE NULL
				END AS [AfterYear]
			FROM [CTE_CleanFormat]
		),
		[CTE_SimplifiedComponents] AS (
			SELECT
				*,
				REPLACE([AfterYear], '.', '') AS [CleanText],
				CASE WHEN CHARINDEX('.', [AfterYear]) > 0 THEN 1 ELSE 0 END AS [HasPeriod]
			FROM [CTE_Components]
		),
		[CTE_ParsedComponents] AS (
			SELECT
				*,
				CASE
					WHEN [AfterYear] IS NULL THEN '01'
					WHEN LEN([CleanText]) = 5 AND ISNUMERIC([CleanText]) = 1 THEN LEFT([CleanText], 2)
					WHEN LEN([CleanText]) = 4 AND ISNUMERIC([CleanText]) = 1 THEN LEFT([CleanText], 2)
					WHEN [HasPeriod] = 1 THEN 
						LEFT([AfterYear], 
						CASE WHEN CHARINDEX('.', [AfterYear]) > 0 
							 THEN CHARINDEX('.', [AfterYear]) - 1 
							 ELSE LEN([AfterYear]) 
						END)
					WHEN LEN([CleanText]) = 3 AND ISNUMERIC([CleanText]) = 1 THEN LEFT([CleanText], 1)
					ELSE [CleanText]
				END AS [Month],
        
				CASE
					WHEN [AfterYear] IS NULL THEN '01'
					WHEN LEN([CleanText]) = 5 AND ISNUMERIC([CleanText]) = 1 THEN RIGHT([CleanText], 3)
					WHEN LEN([CleanText]) = 4 AND ISNUMERIC([CleanText]) = 1 THEN RIGHT([CleanText], 2)
					WHEN [HasPeriod] = 1 AND CHARINDEX('.', [AfterYear]) < LEN([AfterYear]) THEN
						SUBSTRING([AfterYear], 
								  CHARINDEX('.', [AfterYear]) + 1,
								  LEN([AfterYear]))
					WHEN LEN([CleanText]) = 3 AND ISNUMERIC([CleanText]) = 1 THEN RIGHT([CleanText], 2)
					ELSE '01'
				END AS [Day]
			FROM [CTE_SimplifiedComponents]
		),
		[CTE_CleanedComponents] AS (
			SELECT
				*,
				CASE
					WHEN [Month] IS NULL THEN '01'
					WHEN ISNUMERIC(REPLACE([Month], '.', '')) = 0 THEN '01'
					WHEN LEN(REPLACE([Month], '.', '')) > 2 THEN LEFT(REPLACE([Month], '.', ''), 2)
					ELSE REPLACE([Month], '.', '')
				END AS [CleanedMonth],
        
				CASE
					WHEN [Day] IS NULL THEN '01'
					WHEN ISNUMERIC(REPLACE([Day], '.', '')) = 0 THEN '01'
					WHEN LEN(REPLACE([Day], '.', '')) = 3 AND LEFT(REPLACE([Day], '.', ''), 1) = '0' 
						 THEN RIGHT(REPLACE([Day], '.', ''), 2)
					ELSE REPLACE([Day], '.', '')
				END AS [CleanedDay]
			FROM [CTE_ParsedComponents]
		),
		[CTE_FinalDates] AS (
			SELECT
				*,
				[Year] + '-' + 
				RIGHT('0' + [CleanedMonth], 2) + '-' + 
				RIGHT('0' + [CleanedDay], 2) AS [Formatted_Date],
        
				TRY_CONVERT(DATE, 
					[Year] + '-' + 
					RIGHT('0' + [CleanedMonth], 2) + '-' + 
					RIGHT('0' + [CleanedDay], 2)) AS [Sortable_Date]
			FROM [CTE_CleanedComponents]
		)
		-- Update the table
		UPDATE [sod]
		SET [FormattedShipDate] = [cte].[Formatted_Date]
		FROM [mrs].[ShipmentOrderDetails] [sod]
		INNER JOIN [CTE_FinalDates] [cte] ON [sod].[FormattedShipDate] = [cte].[CleanedFormat]
		WHERE [cte].[Sortable_Date] IS NOT NULL;

		-- Get statistics on the update
		DECLARE @UpdatedRows INT = @@ROWCOUNT;
		PRINT 'Updated ' + CAST(@UpdatedRows AS VARCHAR) + ' rows with standardized date format.';

		-- Check for any remaining problematic dates
		SELECT 'Remaining problematic dates: ' + CAST(COUNT(*) AS VARCHAR) AS [Message]
		FROM [mrs].[ShipmentOrderDetails]
		WHERE TRY_CONVERT(DATE, [FormattedShipDate]) IS NULL;

		COMMIT TRANSACTION;