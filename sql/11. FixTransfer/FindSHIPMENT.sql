SELECT TOP (1000) 
		'[z_Shipments_File_____SHIPMAST]'
		,[Transaction_#_____SHORDN]
		,[Cust_P_O#_____SHCORD]
		,[Order_Release_No._____SHOREL]
		,[ITEM_NUMBER_____SHITEM]
	  
		, 'SHIPMENT DATE'		, CONCAT([Shipment_Century_____SHIPCC], [Shipment_Year_____SHIPYY], RIGHT('0' + CAST([Shipment_Month_____SHIPMM] AS VARCHAR(2)), 2), RIGHT('0' + CAST([Shipment_Day_____SHIPDD] AS VARCHAR(2)), 2)) AS FormattedShipmentDate


		, 'SHIPMENT'
		,[Shape_____SHSHAP]
		,[3_POSITION_CLASS_____SHCLS3]
		,[Shipped_Qty_____SHSQTY]
		,[SHIPPED_QTY_UOM_____SHUOM]
		,[Billing_Qty_____SHBQTY]
		,[BILLING_QTY_UOM_____SHBUOM]
		,[BILLING_QTY_INCHES_____SHBINC]
		,[Order_Qty_____SHOQTY]
		,[ORDER_QTY_UOM_____SHOUOM]
		,[ORDER_QTY_INCHES_____SHOINC]
		,[Shipped_Total_LBS_____SHTLBS]
		,[Shipped_Total_PCS_____SHTPCS]
		,[Shipped_Total_FTS_____SHTFTS]
		,[Shipped_Total_Sq.Ft_____SHTSFT]
		,[Theo._Meters_____SHTMTR]
		,[Theo_Kilos_____SHTKG]


		,[Salesman_Dist_____SHLDIS]
		,[Inside_Salesman_____SHINSM]

		,[Processing_Charge_____SHPRCG]
		,[Handling_Charge_____SHHAND]

		, 'CUSTOMER'
		,[Customer_Dist_____SHCDIS]
		,[CUSTOMER_NUMBER_____SHCUST]
		,[Salesman_Dist_____SHTERR]
		,[Outside_Salesman_____SHOUTS]
		,[Line_Number_____SHLINE]

	  
		, CONCAT([Date_Ordered_Century_____SHORCC], [Date_Ordered_Year_____SHORYY], RIGHT('0' + [Date_Ordered_Month_____SHORMM], 2), RIGHT('0' + [Date_Ordered_Day_____SHORDD], 2)) AS FormattedDateOrdered

		, CONCAT([Prom_Date_Century_____SHPRCC], [Prom_Date_Year_____SHPRYY], RIGHT('0' + [Prom_Date_Month_____SHPRMM], 2), RIGHT('0' + [Prom_Date_Day_____SHPRDD], 2)) AS FormattedPromDate

		, CONCAT([Date_Inv_Century_____SHIVCC], [Date_Inv_Year_____SHIVYY], RIGHT('0' + [Date_Inv_Month_____SHIVMM], 2), RIGHT('0' + [Date_Inv_Day_____SHIVDD], 2)) AS FormattedInvoiceDate

			
		, CONCAT([Date_Inv_Century_____SHIVCC], [Date_Inv_Year_____SHIVYY], RIGHT('0' + [Date_Inv_Month_____SHIVMM], 2), RIGHT('0' + [Date_Inv_Day_____SHIVDD], 2)) AS FormattedInvoiceDate
		, CONCAT([Date_Inv_Century_____SHIVCC], [Date_Inv_Year_____SHIVYY], RIGHT('0' + [Date_Inv_Month_____SHIVMM], 2), RIGHT('0' + [Date_Inv_Day_____SHIVDD], 2)) AS FormattedInvoiceDate




		, CONCAT([Century_added_to_S_A_____SHSACC], [Year_added_to_S_A_____SHSAYY], RIGHT('0' + [Month_added_to_S_A_____SHSAMM], 2), RIGHT('0' + [Day_added_to_S_A_____SHSADD], 2)) AS FormattedDateAddedSA

		, 'FREIGHT AND SCRAP'
	
		,[Freight_local+road_____SHFRGH]
		,[Actual_Scrap_Dollars_____SHSCDL]
		,[Actual_Scrap_LBS_____SHSCLB]
		,[Actual_Scrap_KGS_____SHSCKG]
		,[Valid_Values_1_-_PRODUCT_NOT_STOCKED_____SHDBDC]
	  
		, 'SHIP TO'

		,[Truck_Route_____SHTRCK]
		,[Order_designation_Code_____SHODES]
		,[Shop_OLD_____SHSHOP]
		,[CUSTOMER_SHIP-TO_____SHSHTO]
		,[BILL-TO_COUNTRY_____SHBCTY]
		,[SHIP-TO_COUNTRY_____SHSCTY]
		,[TEMP_SHIP-TOq_____SHTMPS]
		,[ADDRESS_ONE_____SHADR1]
		,[ADDRESS_TWO_____SHADR2]
		,[ADDRESS_THREE_____SHADR3]
		,[CITY_25_POS_____SHCITY]
		,[State_Code_____SHSTAT]
		,[Zip_Code_____SHZIP]
		,[Job_Name_____SHJOB]

		,'FLAGS'
		,[Shipment_Type_Flag_____SHTYPE]
		,[Cust_Owned_Flag_____SHCOFL]
		,[Scrap_Flag_____SHSCRP]
		,[Cutting_Process_Flag_____SHCUTC]
		,[Related_part_flag_____SHRFLG]

		, 'SALES'

		,[Material_Sales_Stock_____SHMSLS]
		,[Matl_Sales_Direct_____SHMSLD]
		,[Frght_Sales_Stock_____SHFSLS]
		,[Frght_Sales_Direct_____SHFSLD]
		,[Proc_Sales_Stock_____SHPSLS]
		,[Process_Sales_Direct_____SHPSLD]
		,[Other_Sales_Stock_____SHOSLS]
		,[Other__Sales_Direct_____SHOSLD]
		,[Discount_Sales_Stock_____SHDSLS]
		,[Discnt_Sales_Direct_____SHDSLD]
		,[Material_Cost_Stock_____SHMCSS]
		,[Material_Cost_Direct_____SHMCSD]
		,[Freight-In_Cost_Stock_____SHFISS]
		,[Freight-In_Cost_Direct_____SHFISD]
		,[Frght-Out_Cost_Stock_____SHFOSS]
		,[Frght-Out_Cost_Direct_____SHFOSD]
		,[Fin_Scrap_Fctr_Stock_____SHFSFS]
		,[Fin_Scrap_Fctr_Direct_____SHFSFD]
		,[Processing_Cost_Stock_____SHPCSS]
		,[Processing_Cost_Direct_____SHPCSD]
		,[Other_Cost_Stock_____SHOCSS]
		,[Other_Cost_Direct_____SHOCSD]
		,[Admin_Burden_Stock_____SHADBS]
		,[Admin_Burden_Direct_____SHADBD]
		,[Oper_Burden_Stock_____SHOPBS]
		,[Oper_Burden_Direct_____SHOPBD]
		,[Inv_Adj_Stock_____SHIAJS]
		,[Inv_Adj_Direct_____SHIAJD]
		,[Sales_Qty_Stock_____SHSLSS]
		,[Sales_Qty_Direct_____SHSLSD]
		,[Sales_Weight_Stock_____SHSWGS]
		,[Sales_Weight_Direct_____SHSWGD]
		,[Adjusted_GP%_____SHADPC]
		,[UNIT_PRICE_____SHUNSP]
		,[Unit_Selling_Price_UOM_____SHUUOM]
		,[S_A_addition_flag_____SHSAFL]
		,[Sale_Territory_____SHSTER]
		,[Customer_Trade_____SHTRAD]
		,[Bus._Potential_Class_____SHBPCC]
		,[EEC_Code_____SHEEC]
		,[Sector_Code_____SHSEC]
		,[Invoice_Type_____SHITYP]
		,[In_Sales_Dept_____SHDPTI]
		,[Out_Sales_Dept_____SHDPTO]
		,[Orig_cust_dist#_____SHDSTO]
		,[Orig_cust#_____SHCSTO]
		,[Orig_Slsmn_Dist_____SHSMDO]
		,[Orig_Slsmn_____SHSLMO]
		,[Inv_Comp_____SHICMP]

FROM [SigmaTB].[mrs].[z_Shipments_File_____SHIPMAST]
WHERE		
	[Transaction_#_____SHORDN] = 967682
