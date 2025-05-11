# FILE: my_pyfun_sql_generator.py
# =============================================================================
# 🔍 FUNCTIONAL MODULE: SQL Query Generator from File (using SQLAlchemy)
# DESCRIPTION:
#     Reads file, generates SQL query, calls DB SP via SQLAlchemy for extended query
# =============================================================================

# 📦 IMPORTS
import re
import os
import datetime
import urllib.parse
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from my_03_pyfun_sql_translator import fun_translate_sql_query  # Import the translator function

# =============================================================================
# 🧩 FUNCTION: generate_sql_query
# =============================================================================
def generate_sql_query(myVar_strInputDir, myVar_strInputFilename, myVar_strColumnPrefix):
    """
    Reads input file and generates SQL query string.
    Returns tuple of (SQL query, error message if any)
    """
    myVar_strTableCode = None
    myVar_dictOrderedColumnCodes = {}
    myVar_strFullInputPath = os.path.join(myVar_strInputDir, myVar_strInputFilename)
    myVar_strNewline = os.linesep

    try:
        with open(myVar_strFullInputPath, 'r') as myVar_filInputFile:
            for myVar_strLine in myVar_filInputFile:
                myVar_strLine = myVar_strLine.strip()
                if not myVar_strLine: continue
                
                # Find table name
                if myVar_strTableCode is None:
                    myVar_objTableMatch = re.search(r"TABLE:\s*(\S+)", myVar_strLine, re.IGNORECASE)
                    if myVar_objTableMatch:
                        myVar_strTableCode = myVar_objTableMatch.group(1)
                
                # Find column names - modified regex to exclude trailing ]
                myVar_lstColumnMatches = re.findall(rf"\b{re.escape(myVar_strColumnPrefix)}\w+(?=\]|,|\s|$)", myVar_strLine, re.IGNORECASE)
                for myVar_strCode in myVar_lstColumnMatches:
                    myVar_dictOrderedColumnCodes[myVar_strCode] = True
                    
    except FileNotFoundError:
        return None, f"Error: File not found at '{myVar_strFullInputPath}'"
    except Exception as myVar_errException:
        return None, f"Error processing file '{myVar_strFullInputPath}': {myVar_errException}"

    if not myVar_strTableCode:
        return None, f"Error: No 'TABLE: ' code found in file '{myVar_strInputFilename}'."
    if not myVar_dictOrderedColumnCodes:
        return None, f"Error: No column codes starting with '{myVar_strColumnPrefix}' found in file '{myVar_strInputFilename}'."

    myVar_lstOrderedColumns = list(myVar_dictOrderedColumnCodes.keys())
    myVar_strSelectColumnsPart = ", ".join([f"[{myVar_strTableCode}].[{myVar_strCol}]" for myVar_strCol in myVar_lstOrderedColumns])
    myVar_strSQLQuery = f"SELECT TOP(100) {myVar_strSelectColumnsPart}{myVar_strNewline}"
    myVar_strSQLQuery += f"FROM [{myVar_strTableCode}]"
    
    print("Final columns to be used in query:")
    for col in myVar_lstOrderedColumns:
        print(f"  - {col}")

    return myVar_strSQLQuery, None

# =============================================================================
# 🧩 FUNCTION: create_db_connection
# =============================================================================
def create_db_connection(myVar_strDbServer, myVar_strDbDatabase, myVar_strDbUsername, myVar_strDbPassword):
    """
    Creates and returns SQLAlchemy engine connection.
    Returns tuple of (engine, error message if any)
    """
    try:
        # Create SQLAlchemy connection URL
        myVar_strSqlalchemyUrl = (
            f"mssql+pymssql://{myVar_strDbUsername}:{urllib.parse.quote_plus(myVar_strDbPassword)}@"
            f"{myVar_strDbServer}/{myVar_strDbDatabase}"
        )
        
        myVar_objEngine = create_engine(myVar_strSqlalchemyUrl)
        return myVar_objEngine, None
    except Exception as myVar_errException:
        return None, f"Error creating database connection: {myVar_errException}"

# =============================================================================
# 🧩 FUNCTION: execute_stored_procedure
# =============================================================================
def execute_stored_procedure(myVar_objEngine, myVar_strSQLQuery):
    """
    Executes stored procedure and returns formatted extended query.
    Returns tuple of (formatted query, error message if any)
    """
    try:
        with myVar_objEngine.connect() as myVar_objConn:
            myVar_objResult = myVar_objConn.execute(
                text("EXEC mysp_format_query_with_descriptions @InputQuery = :input_query"),
                {"input_query": myVar_strSQLQuery}
            )
            
            myVar_objRow = myVar_objResult.fetchone()
            if myVar_objRow:
                myVar_strExtendedQuery = myVar_objRow[0]
                myVar_strFormattedExtendedQuery = myVar_strExtendedQuery.replace(',', f',{os.linesep}')
                return myVar_strFormattedExtendedQuery, None
            else:
                return None, "Error: Stored procedure did not return any results"
    except SQLAlchemyError as myVar_errDb:
        return None, f"Database Error: {myVar_errDb}"
    except Exception as myVar_errGeneric:
        return None, f"Unexpected Error: {myVar_errGeneric}"

# =============================================================================
# 🧩 FUNCTION: save_to_file
# =============================================================================
def save_to_file(myVar_strInputDir, myVar_strInputFilename, myVar_strSQLQuery, myVar_strFormattedExtendedQuery):
    """
    Saves original and extended queries to file.
    Returns tuple of (success boolean, error message if any)
    """
    try:
        myVar_strTimestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        myVar_strOutputFilename = f"{myVar_strTimestamp}_{myVar_strInputFilename}_SQL_Output.txt"
        myVar_strFullOutputPath = os.path.join(myVar_strInputDir, myVar_strOutputFilename)

        myVar_strFileContent = myVar_strSQLQuery
        myVar_strFileContent += f"{os.linesep}{os.linesep}"
        myVar_strFileContent += "Extended Query (with descriptions):"
        myVar_strFileContent += f"{os.linesep}{os.linesep}"
        myVar_strFileContent += myVar_strFormattedExtendedQuery

        with open(myVar_strFullOutputPath, 'w') as myVar_filOutputFile:
            myVar_filOutputFile.write(myVar_strFileContent)
        return True, None
    except Exception as myVar_errException:
        return False, f"Error saving file: {myVar_errException}"

# =============================================================================
# 🧩 MAIN FUNCTION: create_sql_query_from_file
# =============================================================================
def create_sql_query_from_file(
    myVar_strInputDir,
    myVar_strInputFilename,
    myVar_strColumnPrefix,
    myVar_strDbServer,
    myVar_strDbDatabase,
    myVar_strDbUsername,
    myVar_strDbPassword
):
    """
    Creates a SQL query from a file containing table and column information.
    
    Args:
        myVar_strInputDir: Directory containing the input file
        myVar_strInputFilename: Name of the input file
        myVar_strColumnPrefix: Default column prefix to use if not specified in file
        myVar_strDbServer: Database server name
        myVar_strDbDatabase: Database name
        myVar_strDbUsername: Database username
        myVar_strDbPassword: Database password
        
    Returns:
        str: Generated SQL query or error message
    """
    # Variable declarations
    myVar_strFullInputPath = ""       # Will store the complete path to the input file
    myVar_strTableCode = None         # Will store the table name found in the file
    myVar_strFilePrefix = None        # Will store the prefix found in the file
    myVar_dictOrderedColumnCodes = {} # Will store unique column codes in order of appearance
    myVar_strGeneratedSQL = ""        # Will store the final generated SQL query
    myVar_strError = ""               # Will store any error message
    myVar_filInputFile = None         # Will store the file object
    myVar_strLine = ""                # Will store each line read from the file
    myVar_objTableMatch = None        # Will store the regex match for table name
    myVar_objPrefixMatch = None       # Will store the regex match for prefix
    myVar_lstColumnMatches = []       # Will store column matches in each line
    myVar_strCode = ""                # Will store each column code found
    myVar_strTranslatedSQL = ""       # Will store the translated SQL query

    try:
        # Building the complete path to the input file
        myVar_strFullInputPath = os.path.join(myVar_strInputDir, myVar_strInputFilename)
        
        # Opening the input file for reading
        with open(myVar_strFullInputPath, 'r') as myVar_filInputFile:
            # Reading each line from the file
            for myVar_strLine in myVar_filInputFile:
                # Removing whitespace from the beginning and end of the line
                myVar_strLine = myVar_strLine.strip()
                
                # Skip empty lines
                if not myVar_strLine: 
                    continue
                
                # Check if this line contains a table definition
                myVar_objTableMatch = re.search(r"TABLE:\s*(\S+)", myVar_strLine, re.IGNORECASE)
                if myVar_objTableMatch:
                    # Store the table name if found
                    myVar_strTableCode = myVar_objTableMatch.group(1)
                    continue
                
                # Check if this line contains a prefix definition
                myVar_objPrefixMatch = re.search(r"PREFIX:\s*([A-Za-z]{2})", myVar_strLine, re.IGNORECASE)
                if myVar_objPrefixMatch:
                    # Store the prefix if found
                    myVar_strFilePrefix = myVar_objPrefixMatch.group(1)
                    continue
                
                # If we have a prefix (either from file or parameter), look for columns
                myVar_strCurrentPrefix = myVar_strFilePrefix if myVar_strFilePrefix else myVar_strColumnPrefix
                if myVar_strCurrentPrefix:
                    # Find all words that start with the current prefix
                    #myVar_lstColumnMatches = re.findall(rf"\b{re.escape(myVar_strCurrentPrefix)}\S*", myVar_strLine, re.IGNORECASE)
                    myVar_lstColumnMatches = re.findall(rf"\b{re.escape(myVar_strCurrentPrefix)}\w+(?=\W|$)", myVar_strLine, re.IGNORECASE)
                    # Store each column code found
                    for myVar_strCode in myVar_lstColumnMatches:
                        myVar_dictOrderedColumnCodes[myVar_strCode] = True

        # Debug print of collected information
        print("\n📊 Debug Information:")
        print(f"Table: {myVar_strTableCode}")
        print(f"Prefix used: {myVar_strFilePrefix if myVar_strFilePrefix else myVar_strColumnPrefix}")
        print("Columns found:")
        for myVar_strColumn in myVar_dictOrderedColumnCodes:
            print(f"  - {myVar_strColumn}")

        # Generate the SQL query if we have both table and columns
        if myVar_strTableCode and myVar_dictOrderedColumnCodes:
            # Add table name and square brackets around each column name and join them
            myVar_lstBracketedColumns = [f"[{myVar_strTableCode}].[{col}]" for col in myVar_dictOrderedColumnCodes.keys()]
            myVar_strGeneratedSQL = f"SELECT TOP(100) {', '.join(myVar_lstBracketedColumns)} FROM [{myVar_strTableCode}]"
            
            # Call the SQL translator with the generated query
            myVar_strTranslatedSQL = fun_translate_sql_query(
                myVar_strGeneratedSQL,
                myVar_strDbServer,
                myVar_strDbDatabase,
                myVar_strDbUsername,
                myVar_strDbPassword
            )
            
            # Save the translated query to a file
            myVar_strTimestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            myVar_strOutputFilename = f"{myVar_strTimestamp}_{myVar_strInputFilename}_translated.txt"
            myVar_strFullOutputPath = os.path.join(myVar_strInputDir, myVar_strOutputFilename)
            
            with open(myVar_strFullOutputPath, 'w') as myVar_filOutput:
                myVar_filOutput.write("-------------------------------------------\n")
                myVar_filOutput.write("Translated query:\n")
                myVar_filOutput.write(myVar_strTranslatedSQL)
                myVar_filOutput.write("\n---------------------------------------------")
            
            print(f"\n💾 Translated query saved to: {myVar_strFullOutputPath}")
            
            return myVar_strGeneratedSQL
        else:
            myVar_strGeneratedSQL = "Error: Missing table name or columns"
            return myVar_strGeneratedSQL

    except FileNotFoundError:
        return f"Error: Input file not found at {myVar_strFullInputPath}"
    except Exception as myVar_errException:
        return f"Error: {str(myVar_errException)}"

# my_script_insert_vbcrlf.py

def insert_vbcrlf_before_double_dash(my_input_text):
    # Insert \r\n before each "--" that starts a column definition
    result = my_input_text.replace('-- Column:', '\r\n-- Column:')
    return result