# =============================================================================
# 🔍 SQL TRANSLATOR MODULE
# DESCRIPTION:
#     Translates SQL queries by replacing table and column names with their
#     extended property descriptions using stored procedures
# =============================================================================

# 📦 IMPORTS
import re
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from tqdm import tqdm
import datetime
import os
import sys

# =============================================================================
# 📝 CONSTANTS
# =============================================================================
# Database connection parameters

my_con_strDbServer = "database-3.c67ymu6q22o1.us-east-1.rds.amazonaws.com"
my_con_strDbDatabase = "SigmaTB"
my_con_strDbUsername = "admin"
my_con_strDbPassword = "Er1c41234$"

# =============================================================================
# 🧩 FUNCTION: fun_create_db_connection
# =============================================================================
def fun_create_db_connection(my_var_strServer, my_var_strDatabase, my_var_strUsername, my_var_strPassword):
    """
    Creates a database connection using SQLAlchemy with pymssql
    Returns tuple of (engine, error message if any)
    """
    try:
        from urllib.parse import quote_plus
        encoded_password = quote_plus(my_var_strPassword)
        
        # Using pymssql with SQLAlchemy
        my_var_strConnectionUrl = (
            f"mssql+pymssql://{my_var_strUsername}:{encoded_password}"
            f"@{my_var_strServer}/{my_var_strDatabase}"
        )
        
        print(f"Connection URL: {my_var_strConnectionUrl}")
        
        # Create engine with optimized settings for Streamlit
        my_var_objEngine = create_engine(
            my_var_strConnectionUrl,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_pre_ping=True
        )
        
        # Test connection
        with my_var_objEngine.connect() as my_var_objConn:
            my_var_objConn.execute(text("SELECT 1"))
        return my_var_objEngine, None
        
    except Exception as my_var_errException:
        return None, f"Error creating database connection: {str(my_var_errException)}"

# =============================================================================
# 🧩 FUNCTION: fun_translate_sql_components
# =============================================================================
def fun_translate_sql_components(my_var_objEngine, my_var_strSqlComponent, my_var_strTableName=None):
    """
    Translates a single SQL component (table or column) using the stored procedure
    Returns the translated component or original if translation fails
    """
    # Variable declarations
    my_var_objConn = None         # Will store the database connection
    my_var_strFullReference = ""  # Will store the complete table.column reference for columns
    my_var_strSqlToExecute = ""   # Will store the SQL command to execute
    my_var_objResult = None       # Will store the query result
    my_var_objRow = None          # Will store a single row from the result
    my_var_errException = None    # Will store any exception that occurs

    try:
        with my_var_objEngine.connect() as my_var_objConn:
            # If table_name is provided, this is a column reference
            if my_var_strTableName:
                # For columns, we need the full table.column reference
                my_var_strFullReference = f"{my_var_strTableName}.{my_var_strSqlComponent}"
                # Building the stored procedure call for column translation
                my_var_strSqlToExecute = f"EXEC my_sp_getXPfromObjects @lookfor = '{my_var_strFullReference}', @isobject = 'column', @returnvalue = 'name'"
                print(f"\nExecuting for column: {my_var_strSqlToExecute}")
                my_var_objResult = my_var_objConn.execute(text(my_var_strSqlToExecute))
            else:
                # For tables, we just need the table name
                my_var_strSqlToExecute = f"EXEC my_sp_getXPfromObjects @lookfor = '{my_var_strSqlComponent}', @isobject = 'table', @returnvalue = 'name'"
                print(f"\nExecuting for table: {my_var_strSqlToExecute}")
                my_var_objResult = my_var_objConn.execute(text(my_var_strSqlToExecute))
            
            # Getting the first row of the result
            my_var_objRow = my_var_objResult.fetchone()
            if my_var_objRow:
                return my_var_objRow[0]
            return my_var_strSqlComponent
    except SQLAlchemyError as my_var_errException:
        print(f"\nError translating {my_var_strSqlComponent}: {str(my_var_errException)}")
        return my_var_strSqlComponent

# =============================================================================
# 🧩 FUNCTION: fun_translate_sql_query
# =============================================================================
def fun_translate_sql_query(my_var_strSqlQueryToTranslate, my_var_strServer, my_var_strDatabase, my_var_strUsername, my_var_strPassword):
    """
    Translates an entire SQL query by breaking it into components
    Returns the translated query or error message
    """
    # Variable declarations
    my_var_objEngine = None           # Will store the SQLAlchemy engine
    my_var_strError = ""              # Will store any error message
    my_var_strPattern = ""            # Will store the regex pattern for finding references
    my_var_lstAllOrigTablesColumnsNames = []            # Will store all matches found in the query
    my_var_lstThisTableOrigName = []       # Will store table references found in the query
    my_var_objThis1Match = None            # Will store the current match being processed
    my_var_strThisColumnOriginal1Name = ""           # Will store the original reference
    my_var_strThis1ReferenceTranslated = ""         # Will store the translated reference
    my_var_strColumnPattern = ""      # Will store the regex pattern for column references
    my_var_lstColumnsToBeTranslated = []      # Will store column references found in the query
    my_var_strTablePartofOneReference = ""          # Will store the table part of a column reference
    my_var_strColumnPartThisReference = ""         # Will store the column part of a column reference
    my_var_strTranslatedAllQuery = ""    # Will store the final translated query
    my_var_errException = None        # Will store any exception that occurs
    
    # Create the tridimensional object to store translations
    my_var_objObjectsToTranslate = []  # List of dictionaries with OriginalName, TranslatedName, and Type

    # Create database connection
    print("\nConnecting to database...")
    my_var_objEngine, my_var_strError = fun_create_db_connection(my_var_strServer, my_var_strDatabase, my_var_strUsername, my_var_strPassword)
    if my_var_strError:
        return f"Error: {my_var_strError}"

    try:
        # Setting up the pattern to find all references in square brackets
        my_var_strPattern = r'\[([^\]]+)\]'
        # Finding all matches in the query
        my_var_lstAllOrigTablesColumnsNames = list(re.finditer(my_var_strPattern, my_var_strSqlQueryToTranslate))
        
        if not my_var_lstAllOrigTablesColumnsNames:
            return "No table or column references found in the query."
        
        # First pass: identify and translate tables
        print("\nTranslating tables...{my_var_lstAllOrigTablesColumnsNames}")

        # We get the names into a list
        my_var_lstThisTableOrigName = [m for m in my_var_lstAllOrigTablesColumnsNames if '.' not in m.group(0)]
        # Filtering matches to get only table references (those without dots)

        for my_var_objThis1Match in tqdm(my_var_lstThisTableOrigName, desc="Tables"):               #Progress bar
            my_var_strThisColumnOriginal1Name = my_var_objThis1Match.group(0)  # e.g., [SHIPMAST]
            
            # First check if this table name exists in our object
            my_var_objExistingTable = next((obj for obj in my_var_objObjectsToTranslate 
                                          if obj['OriginalName'] == my_var_strThisColumnOriginal1Name 
                                          and obj['Type'] == 'table'), None)
            
            if my_var_objExistingTable:
                # If it exists, skip it
                print(f"Table {my_var_strThisColumnOriginal1Name} already exists in object, skipping")
                continue
            
            # First try as a table
            my_var_strThis1ReferenceTranslated = fun_translate_sql_components(my_var_objEngine, my_var_strThisColumnOriginal1Name)
            
            # If we get "NOT FOUND", add it as a column
            if my_var_strThis1ReferenceTranslated == "NOT FOUND":
                print(f"Table not found, adding as column: {my_var_strThisColumnOriginal1Name}")
                # Add to our translation object as a column
                my_var_objObjectsToTranslate.append({
                    'OriginalName': my_var_strThisColumnOriginal1Name,
                    'TranslatedName': "NOT FOUND",  # Keep NOT FOUND as the translated name
                    'Type': 'column'
                })
            else:
                # Add to our translation object as a table
                my_var_objObjectsToTranslate.append({
                    'OriginalName': my_var_strThisColumnOriginal1Name,
                    'TranslatedName': my_var_strThis1ReferenceTranslated,
                    'Type': 'table'
                })
                print(f"Table translated: {my_var_strThis1ReferenceTranslated}")

        # *******************************************
        #NOW WE TRANSLATE THE COLUMNS        
        # *******************************************
        # Second pass: translate columns using their table references
        print("\nTranslating columns...")
        # Setting up the pattern to find column references (table.column)
        my_var_strColumnPattern = r'\[([^\]]+)\]\.\[([^\]]+)\]'
        my_var_lstColumnsToBeTranslated = re.finditer(my_var_strColumnPattern, my_var_strSqlQueryToTranslate)
        
        for my_var_objThis1Match in tqdm(list(my_var_lstColumnsToBeTranslated), desc="Columns"):
            my_var_strTablePartofOneReference = f"[{my_var_objThis1Match.group(1)}]"  # [SHIPMAST]
            my_var_strColumnPartThisReference = f"[{my_var_objThis1Match.group(2)}]"  # [SHORDN]
            my_var_strThisColumnTableOriginal1Name = f"{my_var_strTablePartofOneReference}.{my_var_strColumnPartThisReference}"
            my_var_strThisColumnOriginal1Name = f"{my_var_strColumnPartThisReference}"

            # First check if this column name exists as a table in our object
            my_var_objExistingTable = next((obj for obj in my_var_objObjectsToTranslate 
                                          if obj['OriginalName'] == my_var_strThisColumnOriginal1Name 
                                          and obj['Type'] == 'table'), None)
            
            if my_var_objExistingTable:
                # If it exists as a table, use its translation
                my_var_strThis1ReferenceTranslated = my_var_objExistingTable['TranslatedName']
                print(f"Column {my_var_strThisColumnOriginal1Name} found as table, using translation: {my_var_strThis1ReferenceTranslated}")
            else:
                # Find the existing column entry in our object
                my_var_objExistingColumn = next((obj for obj in my_var_objObjectsToTranslate 
                                               if obj['OriginalName'] == my_var_strThisColumnOriginal1Name 
                                               and obj['Type'] == 'column'), None)
                
                if my_var_objExistingColumn:
                    # Execute the stored procedure for the column
                    my_var_strThis1ReferenceTranslated = fun_translate_sql_components(
                        my_var_objEngine, 
                        my_var_strColumnPartThisReference,
                        my_var_strTablePartofOneReference
                    )
                    print(f"Column translated: {my_var_strThis1ReferenceTranslated}")
                    # Update the existing column's TranslatedName
                    my_var_objExistingColumn['TranslatedName'] = my_var_strThis1ReferenceTranslated
                else:
                    # If column doesn't exist, add it
                    my_var_strThis1ReferenceTranslated = fun_translate_sql_components(
                        my_var_objEngine, 
                        my_var_strColumnPartThisReference,
                        my_var_strTablePartofOneReference
                    )
                    print(f"Column translated: {my_var_strThis1ReferenceTranslated}")
                    my_var_objObjectsToTranslate.append({
                        'OriginalName': my_var_strThisColumnOriginal1Name,
                        'TranslatedName': my_var_strThis1ReferenceTranslated,
                        'Type': 'column'
                    })

        # Add square brackets around each translated name
        for my_var_objTranslation in my_var_objObjectsToTranslate:
            if my_var_objTranslation["TranslatedName"] != "NOT FOUND":
                my_var_objTranslation["TranslatedName"] = f"[{my_var_objTranslation['TranslatedName']}]"

        # Starting with the original query for replacement
        my_var_strTranslatedAllQuery = my_var_strSqlQueryToTranslate
        
        # Replace all occurrences in the query using our translation object
        for my_var_objTranslation in my_var_objObjectsToTranslate:
            my_var_strTranslatedAllQuery = my_var_strTranslatedAllQuery.replace(
                my_var_objTranslation['OriginalName'], 
                my_var_objTranslation['TranslatedName']
            )
            print(f"{my_var_objTranslation['OriginalName']}, {my_var_objTranslation['TranslatedName']}")

        # Add line breaks after each comma
        my_var_strTranslatedAllQuery = my_var_strTranslatedAllQuery.replace(", ", ",\n")

        # Print the full translated query
        print("\nFull translated query:")
        print(my_var_strTranslatedAllQuery)

        return my_var_strTranslatedAllQuery
    except Exception as my_var_errException:
        return f"Error during translation: {str(my_var_errException)}"
    finally:
        if my_var_objEngine:
            my_var_objEngine.dispose()

# =============================================================================
# 🚀 MAIN EXECUTION
# =============================================================================
if __name__ == "__main__":
    # Variable declarations
    my_var_strSqlQuery = ""          # Will store the SQL query to translate
    my_var_strResult = ""            # Will store the translation result
    my_var_dtStartTime = None        # Will store the execution start time
    my_var_dtEndTime = None          # Will store the execution end time
    my_var_strInputFile = None       # Will store the optional input file path
    my_var_strOutputFile = None      # Will store the output file path
    my_var_strFileContent = ""       # Will store the content of the input file

    # Check if an input file was provided as a command line argument
    if len(sys.argv) > 1:
        my_var_strInputFile = sys.argv[1]
        try:
            # Read the SQL query from the input file
            with open(my_var_strInputFile, 'r') as my_var_filInput:
                my_var_strFileContent = my_var_filInput.read()
            # Use the file content as the SQL query
            my_var_strSqlQuery = my_var_strFileContent
            # Create output filename by appending "translated" before the extension
            my_var_strOutputFile = os.path.splitext(my_var_strInputFile)[0] + "_translated.txt"
        except Exception as my_var_errFile:
            print(f"❌ Error reading input file: {my_var_errFile}")
            sys.exit(1)
    else:
        # Use the default SQL query if no input file is provided
        my_var_strSqlQuery = """
        SELECT TOP(100) [SHIPMAST].[SHORDN],  [SHIPMAST].[SHCORD], [SHIPMAST].[SHIPYY], [SHIPMAST].[SHIPMM], [SHIPMAST].[SHIPDD], [SHIPMAST].[SHSHAP],  [SHIPMAST].[SHINSM], [SHIPMAST].[SHSQTY],  [SHIPMAST].[SHUOM], [SHIPMAST].[SHBQTY], [SHIPMAST].[SHBUOM], [SHIPMAST].[SHOINC], [SHIPMAST].[SHOQTY], [SHIPMAST].[SHOUOM], [SHIPMAST].[SHTLBS], [SHIPMAST].[SHTPCS], [SHIPMAST].[SHTFTS], [SHIPMAST].[SHTSFT], [SHIPMAST].[SHTMTR], [SHIPMAST].[SHTKG], [SHIPMAST].[SHPRCG], [SHIPMAST].[SHHAND], [SHIPMAST].[SHMSLS], [SHIPMAST].[SHMSLD], [SHIPMAST].[SHFSLS], [SHIPMAST].[SHFSLD], [SHIPMAST].[SHPSLS], [SHIPMAST].[SHPSLD], [SHIPMAST].[SHOSLS], [SHIPMAST].[SHOSLD], [SHIPMAST].[SHDSLS], [SHIPMAST].[SHDSLD], [SHIPMAST].[SHMCSS], [SHIPMAST].[SHMCSD], [SHIPMAST].[SHSLSS], [SHIPMAST].[SHSLSD], [SHIPMAST].[SHSWGS], [SHIPMAST].[SHSWGD], [SHIPMAST].[SHADPC], [SHIPMAST].[SHUNSP], [SHIPMAST].[SHUUOM], [SHIPMAST].[SHSCDL], [SHIPMAST].[SHSCLB], [SHIPMAST].[SHSCKG], [SHIPMAST].[SHTRCK], [SHIPMAST].[SHBCTY], [SHIPMAST].[SHSCTY], [SHIPMAST].[SHIP-TO], [SHIPMAST].[SHDPTI], [SHIPMAST].[SHDPTO], [SHIPMAST].[SHCSTO], [SHIPMAST].[SHADR1], [SHIPMAST].[SHADR2], [SHIPMAST].[SHADR3], [SHIPMAST].[SHCITY], [SHIPMAST].[SHSTAT], [SHIPMAST].[SHZIP]
        FROM [SHIPMAST]
        """

    # Recording the start time of execution
    my_var_dtStartTime = datetime.datetime.now()
    print(f"Starting execution at: {my_var_dtStartTime.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Translating the query using the stored procedure
    my_var_strResult = fun_translate_sql_query(
        my_var_strSqlQuery, 
        my_con_strDbServer, 
        my_con_strDbDatabase, 
        my_con_strDbUsername, 
        my_con_strDbPassword
    )
    
    print("\nOriginal query:")
    print(my_var_strSqlQuery)
    print("\nTranslated query:")
    print(my_var_strResult)
    
    # If we have an input file, create the output file
    if my_var_strInputFile:
        try:
            with open(my_var_strOutputFile, 'w') as my_var_filOutput:
                my_var_filOutput.write("-------------------------------------------\n")
                my_var_filOutput.write("Translated query:\n")
                my_var_filOutput.write(my_var_strResult)
                my_var_filOutput.write("\n---------------------------------------------")
            print(f"\n💾 Translated query saved to: {my_var_strOutputFile}")
        except Exception as my_var_errFile:
            print(f"❌ Error saving output file: {my_var_errFile}")
    
    # Recording the end time and calculating total execution time
    my_var_dtEndTime = datetime.datetime.now()
    print(f"\nExecution completed at: {my_var_dtEndTime.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total execution time: {my_var_dtEndTime - my_var_dtStartTime}") 