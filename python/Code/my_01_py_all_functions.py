# FILE: main_script.py (Example)
# =============================================================================
# 🎯 ALL PHYTON FUNCTIONS
# DESCRIPTION:
#     Wrapper script to call a function that generates SQL queries from a file.
#     Uses SQLAlchemy via the imported function.
# =============================================================================

# 📦 IMPORTS
import os
from datetime import datetime
# Ensure the secondary file is named correctly and in the same directory or Python path
from my_02_pyfun_sql_generator import create_sql_query_from_file
# Removed unused imports like Streamlit, pandas etc. from the example you provided
# Add back any specific imports YOUR main script actually needs.
import traceback # For error details (Optional but good for debugging)


# ────────────────────────────────────────────────────────────────────────────
# 📜 CONSTANTS & CONFIGURATION
# ────────────────────────────────────────────────────────────────────────────
# --- File Processing Constants ---
#myCon_strDataDirectory = 'C:\Users\esaavedra\Documents\GitHub\SigmaTB_LocalRepo\data'
myCon_strDataDirectory = '/Users/bmate/Documents/GitHub/SigmaTB_LocalRepo/data/'
myCon_strFilename = 'ColumnsToQuery.txt'
myCon_strPrefix = 'SH'
myCon_booShouldSave = True # Set to True to enable saving and SP call

# --- Database Connection Constants ---
myCon_strDbDriver = '{ODBC Driver 17 for SQL Server}' # Adjust if needed
myCon_strDbServer = "database-3.c67ymu6q22o1.us-east-1.rds.amazonaws.com"
myCon_strDbDatabase = "SigmaTB"
myCon_strDbUsername = "admin"
# !!! SECURITY WARNING: Avoid hardcoding passwords in production code !!!
myCon_strDbPassword = "Er1c41234$" # !! Use secrets !!

# --- Remove Construction of pyodbc connection string ---
# myCon_strDbConnectionString = ... (This is no longer needed here)

# --- Initial Check (Optional - function does basic checks now) ---
# You might still want a check here if certain configs are absolutely mandatory
# before even trying to call the function.

# --- Script Variables ---
# 🧠 VARIABLES
myVar_strGeneratedSQL = "" # Will store the *original* query returned by the function
myVar_strFilePath = os.path.join(myCon_strDataDirectory, myCon_strFilename)     #Assign the file path to the variable

# =============================================================================
# 🚀 MAIN EXECUTION
# =============================================================================
try:
    # 🕓 Start timestamp
    print(f"🟢 Starting execution at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 🛠️ Print processing info
    print(f"📄 Processing file: {myVar_strFilePath}")
    if myCon_booShouldSave:
        print(f"💾 File saving and SP execution enabled using server: {myCon_strDbServer}, database: {myCon_strDbDatabase}")

    # 📞 Call the external function, passing the individual DB components
    myVar_strGeneratedSQL = create_sql_query_from_file(
        myVar_strInputDir=myCon_strDataDirectory,           #input directory
        myVar_strInputFilename=myCon_strFilename,           #input filename
        myVar_strColumnPrefix=myCon_strPrefix,             #column prefix
        # Pass database components directly
        myVar_strDbServer=myCon_strDbServer,               #database server
        myVar_strDbDatabase=myCon_strDbDatabase,           #database name   
        myVar_strDbUsername=myCon_strDbUsername,           #database username
        myVar_strDbPassword=myCon_strDbPassword            #database password
    )

    # 🧪 Evaluate result (based on the original query string returned)
    if myVar_strGeneratedSQL.startswith("Error:"):
        print(f"❌ An error occurred during processing: {myVar_strGeneratedSQL}")
    else:
        print("\n📜 Original Generated SQL (Returned by function):")
        print(myVar_strGeneratedSQL)
        
        if myCon_booShouldSave:
            try:
                # Generate timestamp for filename
                myVar_strTimestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                # Create output filename with timestamp
                myVar_strOutputFilename = f"{myVar_strTimestamp}_{myCon_strFilename}_SQL_Output.txt"
                # Create full output path
                myVar_strOutputPath = os.path.join(myCon_strDataDirectory, myVar_strOutputFilename)
                
                # Write the SQL query to the file
                with open(myVar_strOutputPath, 'w') as myVar_filOutput:
                    myVar_filOutput.write(myVar_strGeneratedSQL)
                
                print(f"\n💾 Output file was generated: {myVar_strOutputPath}")
            except Exception as myVar_errFile:
                print(f"❌ Error saving output file: {myVar_errFile}")
        else:
            print("\nℹ️ File saving was disabled.")


    # 🕓 End timestamp
    print(f"\n✅ Finished execution at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

except ImportError as myVar_errImp:
     print(f"🔴 ImportError: Could not import 'create_sql_query_from_file'.")
     print(f"🔴 Ensure 'my_pyfun_sql_generator.py' exists and is in the correct location.")
     print(f"🔴 Error details: {myVar_errImp}")
except Exception as myVar_errException:
    # ❌ General error control block
    print(f"🔴 Execution failed with unexpected error: {myVar_errException}")
    # Print traceback for detailed debugging info
    print("---------------- Traceback ----------------")
    traceback.print_exc()
    print("-----------------------------------------")