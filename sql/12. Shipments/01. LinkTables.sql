USE SIGMATB;
GO

SELECT 
	[Transaction_#_____SHORDN],
	[Cust_P_O#_____SHCORD],
	[ITEM_NUMBER_____SHITEM],
	--[FormattedShipmentDate],
	[Shipment_Type_Flag_____SHTYPE],
	[Scrap_Flag_____SHSCRP],
	[Cutting_Process_Flag_____SHCUTC]
FROM 
	[MRS].[z_Shipments_File_____SHIPMAST]
WHERE 
	[Transaction_#_____SHORDN] = 968207 
OR	[Transaction_#_____SHORDN] = 967682



	[Transaction_#_____SHORDN] = 967682
	AND [Cust_P_O#_____SHCORD] = 204844
	AND [ITEM_NUMBER_____SHITEM] = 51966
	--AND [FormattedShipmentDate] = '20250228'
	AND [Shipment_Type_Flag_____SHTYPE] = 'OE'
	AND [Scrap_Flag_____SHSCRP] = 'N'
	AND [Cutting_Process_Flag_____SHCUTC] = 'Y'

AND 
	--[Transaction_#_____SHORDN] = 967682		--CUTTING PROCESS



	