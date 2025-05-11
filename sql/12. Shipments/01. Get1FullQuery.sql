/********************************************************************
Get 1 full query
*********************************************************************/
SELECT TOP (1000) *

FROM	[mrs].[ShipmentOrderDetails]
WHERE	
		TRY_CONVERT(DATE, [FormattedShipDate]) IS NOT NULL
AND		YEAR(TRY_CONVERT(DATE, [FormattedShipDate])) = 2025
AND		MONTH(TRY_CONVERT(DATE, [FormattedShipDate]))  = 2
AND		DAY(TRY_CONVERT(DATE, [FormattedShipDate]))  = 28

ORDER BY 
    YEAR(TRY_CONVERT(DATE, [FormattedShipDate])) DESC ,
    MONTH(TRY_CONVERT(DATE, [FormattedShipDate])) DESC



*********************************************************************/
SELECT TOP (1000) *

FROM	[mrs].[ShipmentOrderDetails]
WHERE	
		[Transaction_#_____SHORDN] LIKE '%968207%'





-- Name: Count_ShipmentOrderDetails_ByYear
-- Description: Counts shipment records by year
-- Output: Returns a count of shipments grouped by year in descending order

SELECT 
    YEAR(TRY_CONVERT(DATE, [FormattedShipDate])) AS [ShipmentYear],
    COUNT(*) AS [ShipmentCount]
FROM [mrs].[ShipmentOrderDetails]
WHERE TRY_CONVERT(DATE, [FormattedShipDate]) IS NOT NULL
GROUP BY YEAR(TRY_CONVERT(DATE, [FormattedShipDate]))
ORDER BY [ShipmentYear] DESC;




-- Name: Count_ShipmentOrderDetails_ByYearMonth
-- Description: Counts shipment records by year and month
-- Output: Returns a count of shipments grouped by year and month

SELECT 
    YEAR(TRY_CONVERT(DATE, [FormattedShipDate])) AS [ShipmentYear],
    MONTH(TRY_CONVERT(DATE, [FormattedShipDate])) AS [ShipmentMonth],
    COUNT(*) AS [ShipmentCount]
FROM [mrs].[ShipmentOrderDetails]
WHERE TRY_CONVERT(DATE, [FormattedShipDate]) IS NOT NULL
GROUP BY 
    YEAR(TRY_CONVERT(DATE, [FormattedShipDate])),
    MONTH(TRY_CONVERT(DATE, [FormattedShipDate]))
ORDER BY 
    [ShipmentYear] DESC,
    [ShipmentMonth];





/********************************************************************
Get 1 full query
*********************************************************************/
SELECT TOP (1000) 

      [PO_______PO__]
      ,[INVOICE_______INVOICE__]
      ,[DATE_____DATE]
      ,[VENDOR_NAME_____VENDOR_NAME]
      ,[AMOUNT_____AMOUNT]
      ,[BATCH_______BATCH__]
      ,[BOL______BOL_]
      ,[RESPONSIBLE_____RESPONSIBLE]
      ,[PAID_DATE_____PAID_DATE]

	  ,[DWDOCID_____DWDOCID]
      ,[DWDOCUMENTTAG_____DWDOCUMENTTAG]
      ,[DWFIELDSTAG_____DWFIELDSTAG]
		
		/*
      ,[ORIGINATION_____ORIGINATION]
      ,[WEIGHT_____WEIGHT]
      ,[COMMENT_____COMMENT]
      ,[DWSTOREDATETIME_____DWSTOREDATETIME]
      ,[DWVERSIONCOMMENT_____DWVERSIONCOMMENT]
	  */

FROM	[SigmaTB].[mrs].[mysql_____ap]
WHERE	
		[PO_______PO__] LIKE '%968207%'[mrs].[z_Shipments_File_____SHIPMAST]
