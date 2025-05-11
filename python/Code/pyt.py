import pyodbc
from tqdm import tqdm

# Connect to AS/400
as400_conn = pyodbc.connect("DSN=METALNET;UID=ESAAVEDR;PWD=ESM25;Timeout=10")
as400_cursor = as400_conn.cursor()

# Connect to SQL Server
sqlserver_conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=database-3.c67ymu6q22o1.us-east-1.rds.amazonaws.com,1433;"
    "DATABASE=SigmaTB;"
    "UID=admin;"
    "PWD=Er1c41234$"
)
sqlserver_cursor = sqlserver_conn.cursor()
sqlserver_cursor.fast_executemany = True

tables = [
    ("$DSPFDA", "SELECT * FROM QSYS2.SYSCOLUMNS"),
    ("MLRDAT", "Retrieval_date_year_month_day_____MLRDAT"),
    ("MLRTIM", "Retrieval_time_hour_minute_second_____MLRTIM"),
        ('MLFILE', 'File_____MLFILE'),
        ('MLLIB', 'Library_____MLLIB'),
        ('MLFTYP', 'P_PF__L_LF__R_DDM_PF__S_DDM_LF_____MLFTYP'),
        ('MLFILA', 'File_attribute__PHY_or__LGL_____MLFILA'),
        ('MLMXD', 'Reserved_____MLMXD'),
        ('MLFATR', 'File_attribute__PF__LF__PF38__or_LF38_____MLFATR'),
        ('MLSYSN', 'System_Name__Source_System__if_file_is_DDM______MLSYSN'),
        ('MLASP', 'Auxiliary_storage_pool_ID__1_System_ASP_____MLASP'),
        ('MLRES', 'Reserved_____MLRES'),
        ('MLNOMB', 'Number_of_members_____MLNOMB'),
        ('MLNAME', 'Member_____MLNAME'),
        ('MLNRCD', 'Current_number_of_records_____MLNRCD'),
        ('MLNDTR', 'Number_of_deleted_records_____MLNDTR'),
        ('MLSIZE', 'Data_space_and_index_size_in_bytes_____MLSIZE'),
        ('MLSEU', 'Source_type_for_S_38_View_as_it_appeared_on_S_38_____MLSEU'),
        ('MLCCEN', 'Member_creation_century_0_20th__1_21st_____MLCCEN'),
        ('MLCDAT', 'Member_creation_date_year_month_day_____MLCDAT'),
        ('MLCHGC', 'Last_change_century_0_20th__1_21st_____MLCHGC'),
        ('MLCHGD', 'Last_change_date_year_month_day_____MLCHGD'),
        ('MLCHGT', 'Last_change_time_hour_minute_second_____MLCHGT'),
        ('MLMTXT', 'Text__description______MLMTXT'),
        ('MLSEU2', 'Source_type_____MLSEU2'),
        ('MLUCEN', 'Last_Used_Century_0_20th__1_21st_____MLUCEN'),
        ('MLUDAT', 'Last_Used_Date_year_month_day_____MLUDAT'),
        ('MLUCNT', 'Days_Used_Count_____MLUCNT'),
        ('MLTCEN', 'Usage_Data_Reset_Century_0_20th__1_21st_____MLTCEN'),
        ('MLTDAT', 'Usage_Data_Reset_Date_year_month_day_____MLTDAT'),
    ("ACHINFO", [
    ('ACHINFO', "
        ('ACHRCD', 'Record_Code_____ACHRCD'),
        ('ACHCORV', 'Vendor_Customer_____ACHCORV'),
        ('ACHCMP', 'Company_____ACHCMP'),
        ('ACHVND', 'Vendor_____ACHVND'),
        ('ACHDST', 'Customer_District_____ACHDST'),
        ('ACHCST', 'Customer_____ACHCST'),
        ('ACHVRM', 'Remit_To_Seq_____ACHVRM'),
        ('ACHACT', 'Bank_Account_____ACHACT'),
        ('ACHRTE', 'Bank_Routing_____ACHRTE'),
        ('ACHTYP', 'Account_Type_____ACHTYP'),
    ("ACHINFO", [
    ('ADDHSTCT', "
        ('ATRECD', 'A_ACTIVE__D_DELETED_____ATRECD'),
        ('ATTRNT', 'Additional_Charge_Transaction_Type_____ATTRNT'),
        ('ATDIST', 'Transaction_District_____ATDIST'),
        ('ATTRN#', 'Transaction_Number_____ATTRN#'),
        ('ATMLIN', 'Transaction_Line_Number_____ATMLIN'),
        ('ATULIN', 'Transaction_Used_Line_Number_____ATULIN'),
        ('ATRLIN', 'Transaction_Receipt__Restock_Line_Number_____ATRLIN'),
        ('ATSEQ#', 'Additional_Charge_Sequence_Number_____ATSEQ#'),
        ('ATACCD', 'Additional_Charge_Code_____ATACCD'),
        ('ATQTY', 'Additional_Charge_Quantity_____ATQTY'),
        ('ATQUOM', 'Quantity_UOM_____ATQUOM'),
        ('ATUPRC', 'Unit_Price_____ATUPRC'),
        ('ATPUOM', 'Price_UOM_____ATPUOM'),
        ('ATEPRC', 'Extended_Price_____ATEPRC'),
        ('ATUCST', 'Unit_Cost_____ATUCST'),
        ('ATCUOM', 'Cost_UOM_____ATCUOM'),
        ('ATECST', 'Extended_Cost_____ATECST'),
        ('ATIOCD', 'Inside_Outside_____ATIOCD'),
        ('ATCOMP', 'Company_____ATCOMP'),
        ('ATVNDR', 'Vendor_Number_____ATVNDR'),
        ('ATINCD', 'Include_Code_____ATINCD'),
        ('ATBOL', 'BOL___PRO_Number_____ATBOL'),
        ('ATWOCF', 'Created_from_W_O______ATWOCF'),
        ('ATXPFL', 'Exch_Price_Flag_____ATXPFL'),
        ('ATXUSL', 'Exch_Unit_Price_____ATXUSL'),
        ('ATXSLS', 'Exch_Sales_Amt_____ATXSLS'),
        ('ATXCFL', 'Exch_Cost_Flag_____ATXCFL'),
        ('ATXUCS', 'Exch_Unit_Cost_____ATXUCS'),
        ('ATXCST', 'Exch_Cost_Amt_____ATXCST'),
        ('ATXCTY', 'Exch_Currency_____ATXCTY'),
        ('ATXRAT', 'Cost_Exch_Rate_____ATXRAT'),
        ('ATXLCK', 'Exch_Rate_Lock_____ATXLCK'),
        ('ATEFCC', 'Effective_Century_____ATEFCC'),
        ('ATEFYY', 'Effective_Year_____ATEFYY'),
        ('ATEFMM', 'Effective_Month_____ATEFMM'),
        ('ATEFDD', 'Effective_Day_____ATEFDD'),
        ('ATLANG', 'LANGUAGE_COUNTRY_____ATLANG'),
        ('ATFDTX', 'Fed_Tax_Taxable_____ATFDTX'),
        ('ATFTXA', 'FED_TAX_AMOUNT_____ATFTXA'),
        ('ATPVTX', 'Provincial_Taxable_____ATPVTX'),
        ('ATPTXA', 'PROV_TAX_AMOUNT_____ATPTXA'),
        ('ATCTRC', 'Cust_Trans_Code_____ATCTRC'),
        ('ATCORD', 'Cust_Work_Order______ATCORD'),
        ('ATCSOR', 'Cust_Sub_Order______ATCSOR'),
        ('ATVAC', 'Value_Added_Charge_____ATVAC'),
        ('ATAUTO', 'Auto_Added_Charge_____ATAUTO'),
        ('ATFIRM', 'Firm_Price_Chrg_____ATFIRM'),
        ('ATQAAP', 'Quality_Approval_____ATQAAP'),
        ('ATQACR', 'QA_Comments_Reviewed_____ATQACR'),
        ('ATUSER', 'Entered_By_____ATUSER'),
        ('ATSPS#', 'SPO_Sequence_____ATSPS#'),
        ('ATPRT#', 'Paperwork_print_step_sequence_____ATPRT#'),
        ('ATAUTC', 'Auto_Charge_may_not_delete_____ATAUTC'),
        ('ATINCF', 'Inc4_Processed_____ATINCF'),
        ('ATBTCH', 'P_O_Receiving_Batch_Register_Seq_Number_____ATBTCH'),
    ("ACHINFO", [
    ('APCHKH', "
        ('PHRECD', 'Record_Code_____PHRECD'),
        ('PHSTAT', 'Status_____PHSTAT'),
        ('PHFLAG', '1_Cancel_void_2_Reprint_void_3_Void_a_void_____PHFLAG'),
        ('PHCOMP', 'COMPANY_NUMBER_____PHCOMP'),
        ('PHDIST', 'DISTRICT_NUMBER_____PHDIST'),
        ('PHBCDE', 'Bank_Code_____PHBCDE'),
        ('PHVEND', 'Vendor_______PHVEND'),
        ('PHCHCK', 'Check______PHCHCK'),
        ('PHCAMT', 'Cash_Amount_____PHCAMT'),
        ('PHDISA', 'Discount_Amt_____PHDISA'),
        ('PHTAMT', 'Trade_Amount_____PHTAMT'),
        ('PHCKCC', 'Check_Date_Century_____PHCKCC'),
        ('PHCDAT', 'Check_Date_____PHCDAT'),
        ('PHLMCC', 'Last_Maintained_Century_____PHLMCC'),
        ('PHLMYY', 'Last_Maintained_Year_____PHLMYY'),
        ('PHLMMM', '01_12_____PHLMMM'),
        ('PHLMDD', 'Last_Maintained_Day_____PHLMDD'),
        ('PHLMUS', 'Last_Maintained_User_____PHLMUS'),
        ('PHCHKT', 'Check_Type_____PHCHKT'),
        ('PHVSEQ', 'Remit_TO_Sequence_____PHVSEQ'),
        ('PHVDCC', 'Void_Date_Century_____PHVDCC'),
        ('PHVDAT', 'Void_Date_____PHVDAT'),
        ('PHXCAM', 'Exch_Cash_Amount_____PHXCAM'),
        ('PHXDIS', 'Exch_Discount_Amt_____PHXDIS'),
        ('PHHCOD', 'Payment_Handling_Code_____PHHCOD'),
        ('PHRCCC', 'Reconciled_Century_____PHRCCC'),
        ('PHRCYY', 'Reconciled_Year_____PHRCYY'),
        ('PHRCMM', 'Reconcilied_Month_____PHRCMM'),
        ('PHRCDD', 'Reconciled_Day_____PHRCDD'),
        ('PHRCUS', 'Reconciled_User_____PHRCUS'),
        ('PHRCST', 'Reconciled_Status_____PHRCST'),
    ]),
]


for table_index, (table, cols) in enumerate(tqdm(tables, desc="Importing tables")):
    col_names = [col for col, _ in cols]
    aliases = [alias for _, alias in cols]
    select_expr = ", ".join([f"{col} AS [{alias}]" for col, alias in cols])

    try:
        # Step 1: Read from AS/400
        query = f"SELECT {select_expr} FROM MW4FILE.{table}"
        as400_cursor.execute(query)
        rows = as400_cursor.fetchall()
        if not rows:
            print(f"No data in {table}")
            continue

        # Step 2: Prepare insert into SQL Server
        placeholders = ", ".join(["?"] * len(aliases))
        sql_cols = ", ".join([f"[{alias}]" for alias in aliases])
        dest_table_name = f"z_{aliases[0].split('_____')[0]}_____{table}".replace(" ", "_").replace("/", "_")
        insert_sql = f"INSERT INTO {dest_table_name} ({sql_cols}) VALUES ({placeholders})"

        # Step 3: Insert
        sqlserver_cursor.executemany(insert_sql, rows)
        sqlserver_conn.commit()
        print(f"✔ Imported {len(rows)} rows into {dest_table_name}")

    except Exception as e:
        print(f"✘ Error importing table {table}: {e}")

as400_conn.close()
sqlserver_conn.close()
print("\nAll done.")
