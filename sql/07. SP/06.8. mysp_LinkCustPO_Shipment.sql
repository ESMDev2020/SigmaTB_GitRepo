/****************************************************************************
NOW LINK ALL CUSTOMER PUCHASE ORDERS TO SHIPMENT ORDERS AND SAVE THEM INTO 
	A NEW TABLE	ShipmentOrderDetails
----------------------------------------------------------------------------
		-- Create a new table and insert all matching records
		SELECT 
			'****** Customer Purchase Order  ********' AS PurchaseOrderSection,
			CM.[Customer_Name_____CCUSTN],
			SM.[Cust_P/O#_____SHCORD],
			SM.[ITEM_NUMBER_____SHITEM],
			SM.[Transaction_#_____SHORDN],
			CONCAT(CAST(SM.[Century_added_to_S/A_____SHSACC] AS VARCHAR(2)) + CAST(SM.[Shipment_Year_____SHIPYY] AS VARCHAR(4)), 
				   RIGHT('0' + CAST(SM.[Shipment_Month_____SHIPMM] AS VARCHAR(2)), 2), 
				   RIGHT('0' + CAST(SM.[Shipment_Day_____SHIPDD] AS VARCHAR(2)), 2)) AS FormattedShipDate,
			SM.[Truck_Route_____SHTRCK],
	
			'****** Sales order  ********' AS SalesOrderSection,
	
			'******Shipment company ********' AS ShipmentCompanySection,
			AP.[INVOICE_______INVOICE__] AS dwINVOICE,
			AP.[DATE_____DATE] AS DATE,
			AP.[VENDOR_NAME_____VENDOR_NAME] AS dwVENDOR,
			AP.[AMOUNT_____AMOUNT] AS dwAMOUNT,
			AP.[BATCH_______BATCH__] AS dwBATCH,
			AP.[BOL______BOL_] AS dwBOL,
	
			'******Delivery address  ********' AS DeliveryAddressSection,
			SM.[ADDRESS_ONE_____SHADR1],
			SM.[CITY_25_POS_____SHCITY],
			SM.[State_Code_____SHSTAT],
			SM.[Zip_Code_____SHZIP]
		INTO 
			[SigmaTB].[mrs].[ShipmentOrderDetails] -- Name of new table
		FROM
			[SigmaTB].[mrs].[z_Shipments_File_____SHIPMAST] AS SM
			INNER JOIN [SigmaTB].[mrs].[z_Customer_Master_File_____ARCUST] AS CM
				ON CM.[CUSTOMER_NUMBER_____CCUST] = SM.[Orig_cust#_____SHCSTO]
			INNER JOIN [SigmaTB].[mrs].[mysql_____ap] AS AP
				ON CASE
					WHEN LEFT(AP.[PO_______PO__], 2) = '01' 
						THEN RIGHT(AP.[PO_______PO__], LEN(AP.[PO_______PO__]) - 2) 
					ELSE AP.[PO_______PO__]
				   END = REPLACE(SM.[Transaction_#_____SHORDN], '.0', '')


***************************************************************************************/