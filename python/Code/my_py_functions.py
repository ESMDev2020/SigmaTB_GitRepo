import sp_TranslateQueries as myFunTranslateQueries # Assuming sp_TranslateQueries.py exists and is importable

# --- Database Connection Constants ---
myCon_strDbDriver = '{ODBC Driver 17 for SQL Server}' # Adjust if needed
myCon_strDbServer = "database-3.c67ymu6q22o1.us-east-1.rds.amazonaws.com"
myCon_strDbDatabase = "SigmaTB"
myCon_strDbUsername = "admin"
# !!! SECURITY WARNING: Avoid hardcoding passwords in production code !!!
myCon_strDbPassword = "Er1c41234$" # !! Use secrets !!

# --- Construct the pyodbc-style connection string ---
my_connection_string_value = (
    f"Driver={myCon_strDbDriver};"
    f"Server={myCon_strDbServer};"
    f"Database={myCon_strDbDatabase};"
    f"UID={myCon_strDbUsername};"
    f"PWD={myCon_strDbPassword};"
)

# --- Set the output format argument ---
my_output_format_value = "name" # (name/code) Set based on user choice 


# Call the function using explicit keyword arguments
# This matches the parameter names in the function definition
myVarResult = myFunTranslateQueries.fun_get_xp_info(
    my_var_str_connection_string = my_connection_string_value,
    my_var_str_sql_statement = '''SELECT TOP(100) [SHIPMAST].[SHIPMAST], [SHIPMAST].[SH], [SHIPMAST].[SHORDN],
[SHIPMAST].[Shipment], [SHIPMAST].[SHCORD], [SHIPMAST].[SHIPYY], [SHIPMAST].[SHIPMM], [SHIPMAST].[SHIPDD], [SHIPMAST].[SHSHAP], [SHIPMAST].[shape], [SHIPMAST].[SHINSM], [SHIPMAST].[SHSQTY], [SHIPMAST].[Shipped], [SHIPMAST].[SHUOM], [SHIPMAST].[SHBQTY], [SHIPMAST].[SHBUOM], [SHIPMAST].[SHOINC], [SHIPMAST].[SHOQTY], [SHIPMAST].[SHOUOM], [SHIPMAST].[SHTLBS], [SHIPMAST].[SHTPCS], [SHIPMAST].[SHTFTS], [SHIPMAST].[SHTSFT], [SHIPMAST].[SHTMTR], [SHIPMAST].[SHTKG], [SHIPMAST].[SHPRCG], [SHIPMAST].[SHHAND], [SHIPMAST].[SHMSLS], [SHIPMAST].[SHMSLD], [SHIPMAST].[SHFSLS], [SHIPMAST].[SHFSLD], [SHIPMAST].[SHPSLS], [SHIPMAST].[SHPSLD], [SHIPMAST].[SHOSLS], [SHIPMAST].[SHOSLD], [SHIPMAST].[SHDSLS], [SHIPMAST].[SHDSLD], [SHIPMAST].[SHMCSS], [SHIPMAST].[SHMCSD], [SHIPMAST].[SHSLSS], [SHIPMAST].[SHSLSD], [SHIPMAST].[SHSWGS], [SHIPMAST].[SHSWGD], [SHIPMAST].[SHADPC], [SHIPMAST].[SHUNSP], [SHIPMAST].[SHUUOM], [SHIPMAST].[SHSCDL], [SHIPMAST].[SHSCLB], [SHIPMAST].[SHSCKG], [SHIPMAST].[SHTRCK], [SHIPMAST].[SHBCTY], [SHIPMAST].[SHSCTY], [SHIPMAST].[SHIP-TO], [SHIPMAST].[SHDPTI], [SHIPMAST].[SHDPTO], [SHIPMAST].[SHCSTO], [SHIPMAST].[SHADR1], [SHIPMAST].[SHADR2], [SHIPMAST].[SHADR3], [SHIPMAST].[SHCITY], [SHIPMAST].[SHSTAT], [SHIPMAST].[SHZIP]
FROM [SHIPMAST]''',
    my_var_str_output_format = my_output_format_value
)

# Optional: You can print the result to see what the function returned
print(f"Result from function: {myVarResult}")