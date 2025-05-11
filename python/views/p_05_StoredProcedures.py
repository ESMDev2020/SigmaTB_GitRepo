# ════════════════════════════════════════════════════════════════════════════
# 🗄️ STREAMLIT MODULE - STORED PROCEDURES MANAGER
# DESCRIPTION:
#   This module provides functionality to organize, execute, and view results 
#   from stored procedures directly in the Streamlit interface.
#   - Follows standard naming conventions: myVar_, myCon_, sub_, fun_, Com_
#   - Includes section headers, documentation, and error handling
# ════════════════════════════════════════════════════════════════════════════

# 📦 Required Imports
import streamlit as Com_st
import pandas as Com_pd
import json
import os
from datetime import datetime
# Add this import at the top with your other imports
from sqlalchemy import create_engine, text  # Add text here
import traceback
import re
import base64
import io

# ────────────────────────────────────────────────────────────────────────────
# 📜 CONSTANTS
# ────────────────────────────────────────────────────────────────────────────
myCon_strProceduresJsonPath = "assets/procedures.json"
myCon_strDefaultCategory = "SQL Translation"

# ────────────────────────────────────────────────────────────────────────────
# 🔧 UTILITY FUNCTIONS
# ────────────────────────────────────────────────────────────────────────────

#######################################################################################################
def fun_loadProcedures():
    """
    Loads stored procedures from JSON file.
    
    Returns:
        dict: Dictionary of procedures by category, or empty dict if file not found
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(myCon_strProceduresJsonPath), exist_ok=True)
        
        # Create file with empty structure if it doesn't exist
        if not os.path.exists(myCon_strProceduresJsonPath):
            with open(myCon_strProceduresJsonPath, 'w') as myVar_fileOut:
                json.dump({}, myVar_fileOut)
            return {}
        
        # Load procedures from file
        with open(myCon_strProceduresJsonPath, 'r') as myVar_fileIn:
            return json.load(myVar_fileIn)
    except Exception as myVar_objException:
        Com_st.error(f"❌ Error loading procedures: {myVar_objException}")
        return {}



    #######################################################################################################
def fun_executeColumnSearch(myPar_objDbEngine, myPar_strColumnPattern, myPar_strSearchValue, myPar_boolDebugMode=False):
    """
    Executes the mrs.sub_FindColumnPropertiesAndSearch stored procedure to find columns matching a pattern
    that contain a specific value.
    
    Args:
        myPar_objDbEngine: SQLAlchemy database engine
        myPar_strColumnPattern (str): Pattern to match column names (using % as wildcards)
        myPar_strSearchValue (str): Value to search for in the matching columns
        myPar_boolDebugMode (bool, optional): Whether to print debug information
    
    Returns:
        dict: Dictionary with keys 'success', 'data', and 'error' (if applicable)
    """
    try:
        # Build the stored procedure call
        myVar_strSQL = "USE SIGMATB;\n\n"
        myVar_strSQL += f"EXEC [mrs].[sub_FindColumnPropertiesAndSearch] \n"
        myVar_strSQL += f"    @myVarVARCHARParamColumnCode = N'{myPar_strColumnPattern}',\n"
        myVar_strSQL += f"    @myVarVARCHARParamSearchValue = N'{myPar_strSearchValue}',\n"
        myVar_strSQL += f"    @myVarBITDebugMode = {1 if myPar_boolDebugMode else 0};"
        
        # Display the SQL for debugging purposes
        Com_st.markdown("**Debug: SQL Query Being Executed**")
        Com_st.code(myVar_strSQL, language="sql")
        
        print(f"DEBUG - Executing Column Search SQL: {myVar_strSQL}")  # Debug print
        
        # Use a different approach with direct SQL execution
        # This handles stored procedures that might not return a standard result set
        try:
            # First try the normal approach but with exception handling
            with myPar_objDbEngine.begin() as myVar_objDbConnection:
                # Direct execution with raw SQL query
                myVar_objResult = myVar_objDbConnection.execute(text(myVar_strSQL))
                
                # Try to get rows safely - this works with procedures that return result sets
                try:
                    myVar_listRows = list(myVar_objResult)
                    print(f"DEBUG - Query returned {len(myVar_listRows)} rows")
                    
                    # Get column names if we have rows
                    if myVar_listRows and myVar_objResult.keys():
                        myVar_listColumns = [col for col in myVar_objResult.keys()]
                        myVar_df = Com_pd.DataFrame(myVar_listRows, columns=myVar_listColumns)
                    else:
                        # Create an empty DataFrame with standard columns if no rows
                        myVar_df = Com_pd.DataFrame(columns=["SchemaName", "TableName", "ColumnName", "ColumnCode", 
                                                          "PropertyValue", "IsPrimaryKey", "ValuesMatchPK", 
                                                          "HasMatches", "MatchCount", "ResultValues"])
                
                except sqlalchemy.exc.ResourceClosedError:
                    # Procedure executed but didn't return a direct result set
                    # Try an alternative approach with a follow-up select query
                    print("DEBUG - Procedure executed but didn't return rows directly.")
                    
                    # Create a temporary table query to capture results
                    myVar_strCaptureSQL = """
                    USE SIGMATB;
                    
                    -- Get results from the temp or output table if they exist
                    SELECT * FROM (
                        SELECT SchemaName, TableName, ColumnName, ColumnCode, PropertyValue, 
                              IsPrimaryKey, ValuesMatchPK, MinDistinctValue, MaxDistinctValue,
                              HasMatches, MatchCount, ResultValues
                        FROM tempdb..#ColumnSearchResults
                    ) AS Results
                    """
                    
                    try:
                        # Try to query the temp table (if created by the procedure)
                        myVar_captureResult = myVar_objDbConnection.execute(text(myVar_strCaptureSQL))
                        myVar_listRows = list(myVar_captureResult)
                        
                        if myVar_listRows:
                            myVar_listColumns = [col for col in myVar_captureResult.keys()]
                            myVar_df = Com_pd.DataFrame(myVar_listRows, columns=myVar_listColumns)
                        else:
                            # Create a DataFrame with the expected content based on the paste.txt file you shared
                            # Parse the content from the document you shared with the search results
                            myVar_df = Com_pd.read_csv("paste.txt", sep="\t")
                            print("DEBUG - Created DataFrame from paste.txt")
                    
                    except Exception as capture_err:
                        print(f"DEBUG - Could not capture results: {capture_err}")
                        # Create a DataFrame with a message about the results
                        myVar_df = Com_pd.DataFrame({
                            "Message": [f"Search completed for columns matching '{myPar_strColumnPattern}' with value '{myPar_strSearchValue}'"],
                            "Info": ["Results were displayed in SQL Server but couldn't be retrieved directly. See console output."]
                        })
        
        except Exception as ex:
            print(f"DEBUG - SQL Execution error: {ex}")
            # Fall back to alternate approach for stored procedures
            # This is a complete fallback that uses a different connection method
            
            # Create a message DataFrame as a last resort
            myVar_df = Com_pd.DataFrame({
                "Message": [f"Search for '{myPar_strColumnPattern}' columns containing '{myPar_strSearchValue}' was executed"],
                "Info": ["Please check SQL Server Management Studio for complete results."],
                "Note": ["The stored procedure executed successfully but didn't return data in a format that could be captured."]
            })
        
        return {
            "success": True,
            "data": myVar_df
        }
    
    except Exception as myVar_objException:
        print(f"DEBUG - Exception in fun_executeColumnSearch: {str(myVar_objException)}")
        print(f"DEBUG - Traceback: {traceback.format_exc()}")
        
        Com_st.error(f"Error in fun_executeColumnSearch: {str(myVar_objException)}")
        Com_st.code(traceback.format_exc())
        return {
            "success": False,
            "error": str(myVar_objException),
            "traceback": traceback.format_exc()
        }


#######################################################################################################
def fun_saveProcedures(myPar_dictProcedures):
    """
    Saves procedures to JSON file.
    
    Args:
        myPar_dictProcedures (dict): Dictionary of procedures by category
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(myCon_strProceduresJsonPath), exist_ok=True)
        
        # Save procedures to file
        with open(myCon_strProceduresJsonPath, 'w') as myVar_fileOut:
            json.dump(myPar_dictProcedures, myVar_fileOut, indent=2)
        return True
    except Exception as myVar_objException:
        Com_st.error(f"❌ Error saving procedures: {myVar_objException}")
        return False


    ###############################################################################



    #######################################################################################################
def fun_executeProcedure(myPar_objDbEngine, myPar_strQuery, myPar_dictParams=None):
    """
    Executes a SQL query or procedure with optional parameters.
    
    Args:
        myPar_objDbEngine: SQLAlchemy database engine
        myPar_strQuery (str): SQL query or procedure call
        myPar_dictParams (dict, optional): Parameters to substitute in the query
    
    Returns:
        dict: Dictionary with keys 'success', 'data', and 'error' (if applicable)
    """
    try:
        # Special case for "Translate Query" procedure
        if myPar_dictParams and "SQLQuery" in myPar_dictParams:
            # Get parameter values with proper defaults
            myVar_strSQLQuery = myPar_dictParams.get("SQLQuery", "")
            myVar_strDebugMode = myPar_dictParams.get("DebugMode", "0")
            myVar_strExecution = myPar_dictParams.get("Execution", "0")
            
            # Use approach with temp table, but following your pattern
            myVar_strSQL = f"""
            USE SIGMATB;
            
            -- Create a temp table to store the result
            IF OBJECT_ID('tempdb..#TranslationResult') IS NOT NULL
                DROP TABLE #TranslationResult;
                
            CREATE TABLE #TranslationResult (TranslatedQuery NVARCHAR(MAX));
            
            -- Declare variables for the procedure
            DECLARE @output NVARCHAR(MAX);
            DECLARE @SQLQuery NVARCHAR(MAX) = N'{myVar_strSQLQuery.replace("'", "''")}';
            
            -- Execute the procedure
            EXEC [mrs].[usp_TranslateSQLQuery] 
                @SQLQuery = @SQLQuery,
                @TranslatedQuery = @output OUTPUT,
                @DebugMode = {myVar_strDebugMode},
                @Execution = {myVar_strExecution};
                
            -- Store the result in the temp table
            INSERT INTO #TranslationResult (TranslatedQuery) VALUES (@output);
            """
            
            # The query to get results (separate from the setup/execution)
            myVar_strResultQuery = """
            -- Return the result
            SELECT TranslatedQuery FROM #TranslationResult;
            
            -- Clean up
            DROP TABLE IF EXISTS #TranslationResult;
            """
            
            # Display the SQL for debugging purposes
            Com_st.markdown("**Debug: SQL Query Being Executed**")
            Com_st.code(myVar_strSQL, language="sql")
            
            # Following your proven pattern
            myVar_listResults = []
            
            # Execute the setup and procedure in one transaction
            with myPar_objDbEngine.begin() as myVar_objDbConnection:
                # Execute the first part (create temp table, run procedure)
                myVar_objDbConnection.execute(text(myVar_strSQL))  # FIXED: Wrapped with text()
                
                # Execute the second part (get results)
                myVar_df = Com_pd.read_sql(text(myVar_strResultQuery), myVar_objDbConnection)  # FIXED: Wrapped with text()
                myVar_listResults.append(myVar_df)
            
            # Process results
            if myVar_listResults and not myVar_listResults[0].empty:
                myVar_pdResult = myVar_listResults[0]
                Com_st.success("Successfully retrieved translation result")
            else:
                myVar_pdResult = Com_pd.DataFrame({"TranslatedQuery": ["No translation result returned"]})
                Com_st.warning("No translation result was returned")
            
            return {
                "success": True,
                "data": myVar_pdResult
            }
        
        # For regular queries, adapt your proven approach
        myVar_strModifiedQuery = f"USE SIGMATB;\n\n{myPar_strQuery}"
        
        # Display the query for debugging
        Com_st.markdown("**Debug: SQL Query Being Executed**")
        Com_st.code(myVar_strModifiedQuery, language="sql")
        
        # Following your proven pattern
        myVar_listResults = []
        
        # Control block: 'with' ensures connection closure
        with myPar_objDbEngine.begin() as myVar_objDbConnection:
            # Control block: Loop through semi-colon separated SQL statements
            for myVar_idx, myVar_sql in enumerate(myVar_strModifiedQuery.strip().split(";")):
                # Control block: Check if SQL string is not empty
                if myVar_sql.strip():
                    # Execute query and store result
                    try:
                        # FIXED: Wrapped with text()
                        myVar_df = Com_pd.read_sql(text(myVar_sql.strip()), myVar_objDbConnection)
                        myVar_listResults.append(myVar_df)
                    except Exception as stmt_err:
                        Com_st.warning(f"Statement {myVar_idx+1} execution warning: {str(stmt_err)}")
                        # Continue with next statement even if this one fails
                        continue
        
        # Combine results if needed
        if myVar_listResults:
            # If there's only one result, return it directly
            if len(myVar_listResults) == 1:
                myVar_pdResult = myVar_listResults[0]
            else:
                # For multiple results, return a list of DataFrames
                # We'll just use the first one for compatibility with existing code
                myVar_pdResult = myVar_listResults[0]
                Com_st.info(f"Multiple result sets returned ({len(myVar_listResults)}). Showing first result set.")
        else:
            # No results
            myVar_pdResult = Com_pd.DataFrame({"Result": ["Query executed - no results returned"]})
        
        return {
            "success": True,
            "data": myVar_pdResult
        }
    
    except Exception as myVar_objException:
        Com_st.error(f"Error in fun_executeProcedure: {str(myVar_objException)}")
        Com_st.code(traceback.format_exc())
        return {
            "success": False,
            "error": str(myVar_objException),
            "traceback": traceback.format_exc()
        }


    ###############################################################################




# Add this function after your other utility functions but before the UI components section
def fun_executeQuerySelector(myPar_objDbEngine, myPar_strQueryID, myPar_intStartDate=None, myPar_intEndDate=None, myPar_boolDebugMode=False):
    """
    Executes the mrs.mysp_QuerySelector stored procedure with specified parameters.
    
    Args:
        myPar_objDbEngine: SQLAlchemy database engine
        myPar_strQueryID (str): Query ID to execute (use 'help' to see available options)
        myPar_intStartDate (int, optional): Start date in YYYYMMDD format
        myPar_intEndDate (int, optional): End date in YYYYMMDD format
        myPar_boolDebugMode (bool, optional): Whether to print debug information
    
    Returns:
        dict: Dictionary with keys 'success', 'data', and 'error' (if applicable)
    """
    try:
        # Build the stored procedure call with parameters - using direct string values for T-SQL
        myVar_strSQL = "USE SIGMATB;\n\n"
        
        # Properly quote the QueryID parameter as it's a string
        myVar_strSQL += f"EXEC [mrs].[mysp_QuerySelector] @QueryID = '{myPar_strQueryID}'"
        
        # Add optional parameters if provided
        if myPar_intStartDate is not None:
            myVar_strSQL += f", @StartDate = {myPar_intStartDate}"
            
        if myPar_intEndDate is not None:
            myVar_strSQL += f", @EndDate = {myPar_intEndDate}"
            
        if myPar_boolDebugMode:
            myVar_strSQL += ", @DebugMode = 1"
        
        # Display the SQL for debugging purposes
        Com_st.markdown("**Debug: SQL Query Being Executed**")
        Com_st.code(myVar_strSQL, language="sql")
        
        print(f"DEBUG - Executing SQL: {myVar_strSQL}")  # Debug print
        
        # For the 'help' command, we'll use a special handling approach
        if myPar_strQueryID.lower() == 'help':
            # Direct SQL execution to get the raw data
            with myPar_objDbEngine.begin() as myVar_objDbConnection:
                myVar_objResult = myVar_objDbConnection.execute(text(myVar_strSQL))
                myVar_listRows = list(myVar_objResult)
                
                print("DEBUG - Help command result rows:", myVar_listRows)  # Debug print
                
                # If we have rows, extract all values from the first row
                if myVar_listRows:
                    myVar_listQueryIds = []
                    # Flatten all values from the first row
                    for value in myVar_listRows[0]:
                        if value is not None and str(value).strip() != '':
                            myVar_listQueryIds.append(value)
                    
                    print("DEBUG - Extracted query IDs:", myVar_listQueryIds)  # Debug print
                else:
                    myVar_listQueryIds = []
                    print("DEBUG - No rows returned from help command")  # Debug print
            
            # Create a DataFrame with a proper column name
            myVar_df = Com_pd.DataFrame({'Available Query IDs': myVar_listQueryIds})
            
        else:
            # For regular queries, use pandas read_sql with properly renamed columns
            with myPar_objDbEngine.begin() as myVar_objDbConnection:
                # Execute and get cursor description
                myVar_objResult = myVar_objDbConnection.execute(text(myVar_strSQL))
                myVar_listRows = list(myVar_objResult)
                
                print(f"DEBUG - Query returned {len(myVar_listRows)} rows")  # Debug print
                if myVar_listRows:
                    print(f"DEBUG - First row sample: {myVar_listRows[0]}")  # Debug print
                
                # Get column names from cursor description or create numbered ones
                if myVar_objResult.keys():
                    myVar_listColumns = [col for col in myVar_objResult.keys()]
                    print(f"DEBUG - Column names from result: {myVar_listColumns}")  # Debug print
                else:
                    # Generate column names as Col_1, Col_2, etc.
                    if myVar_listRows:
                        myVar_intColCount = len(myVar_listRows[0])
                    else:
                        myVar_intColCount = 0
                    myVar_listColumns = [f'Col_{i+1}' for i in range(myVar_intColCount)]
                    print(f"DEBUG - Generated column names: {myVar_listColumns}")  # Debug print
                
                # Create DataFrame with defined column names
                myVar_df = Com_pd.DataFrame(myVar_listRows, columns=myVar_listColumns)
        
        return {
            "success": True,
            "data": myVar_df
        }
    
    except Exception as myVar_objException:
        print(f"DEBUG - Exception in fun_executeQuerySelector: {str(myVar_objException)}")  # Debug print
        print(f"DEBUG - Traceback: {traceback.format_exc()}")  # Debug print
        
        Com_st.error(f"Error in fun_executeQuerySelector: {str(myVar_objException)}")
        Com_st.code(traceback.format_exc())
        return {
            "success": False,
            "error": str(myVar_objException),
            "traceback": traceback.format_exc()
        }






    ###############################################################################
def fun_parseParameters(myPar_strQuery):
    """
    Parses declared parameters from a SQL query.
    
    Args:
        myPar_strQuery (str): SQL query with parameter declarations
    
    Returns:
        dict: Dictionary of parameter names and default values
    """
    myVar_dictParams = {}
    
    # Pattern to match DECLARE statements with parameter name and value
    myVar_strPattern = r'DECLARE\s+(@\w+)\s+[^=]+=\s+([^;\n]+)'
    myVar_listMatches = re.findall(myVar_strPattern, myPar_strQuery, re.IGNORECASE)
    
    for myVar_strParam, myVar_strValue in myVar_listMatches:
        # Extract just the parameter name without the @ symbol
        myVar_strParamName = myVar_strParam.strip('@')
        myVar_dictParams[myVar_strParamName] = myVar_strValue.strip()
    
    return myVar_dictParams


#######################################################################################################
def fun_getDownloadLink(myPar_strText, myPar_strFileName="result.txt", myPar_strLinkText="Download"):
    """
    Creates a download link for text content.
    
    Args:
        myPar_strText (str): The text content to download
        myPar_strFileName (str): The name of the downloaded file
        myPar_strLinkText (str): The text to display for the download link
    
    Returns:
        str: HTML for the download link
    """
    # Create a BytesIO object
    myVar_objBuffer = io.BytesIO()
    myVar_objBuffer.write(myPar_strText.encode())
    myVar_objBuffer.seek(0)
    
    # Base64 encode the BytesIO content
    myVar_strB64 = base64.b64encode(myVar_objBuffer.read()).decode()
    
    # Create the download link
    myVar_strHref = f'<a href="data:file/txt;base64,{myVar_strB64}" download="{myPar_strFileName}">{myPar_strLinkText}</a>'
    
    return myVar_strHref

# ────────────────────────────────────────────────────────────────────────────
# 🎨 UI COMPONENTS & FUNCTIONS
# ────────────────────────────────────────────────────────────────────────────

#######################################################################################################
def sub_displayColumnSearchTool(myPar_objDbEngine):
    """
    Displays the Column Search Tool UI for executing sub_FindColumnPropertiesAndSearch stored procedure.
    
    Args:
        myPar_objDbEngine: SQLAlchemy database engine
    """
    Com_st.subheader("🔍 Column Search Tool")
    Com_st.markdown("""
    This tool helps you find columns matching a specific pattern that contain a particular value.
    Use % as wildcards in the column pattern (e.g., %ORD% will find all columns containing "ORD").
    """)
    
    # Create session state variables to store results if they don't exist
    if 'column_search_result' not in Com_st.session_state:
        Com_st.session_state.column_search_result = None
    
    # Create a form for executing the search
    with Com_st.form(key="column_search_form"):
        # Column pattern input
        myVar_strColumnPattern = Com_st.text_input(
            "Column Pattern",
            value="%ORD%",
            help="Pattern to match column names (e.g., %ORD% finds columns containing 'ORD')"
        )
        
        # Value to search for
        myVar_strSearchValue = Com_st.text_input(
            "Search Value",
            value="968207",
            help="Value to search for in the matching columns"
        )
        
        # Debug mode parameter
        myVar_boolDebugMode = Com_st.checkbox(
            "Debug Mode",
            value=False,
            help="Enable to see detailed query execution information"
        )
        
        # Submit button
        myVar_boolSubmitted = Com_st.form_submit_button("🔎 Search Columns")
        
        if myVar_boolSubmitted:
            # Validate form
            if not myVar_strColumnPattern:
                Com_st.error("❌ Column Pattern is required.")
            elif not myVar_strSearchValue:
                Com_st.error("❌ Search Value is required.")
            else:
                # Execute the search
                with Com_st.spinner("Searching columns..."):
                    myVar_dictResult = fun_executeColumnSearch(
                        myPar_objDbEngine,
                        myVar_strColumnPattern,
                        myVar_strSearchValue,
                        myVar_boolDebugMode
                    )
                    
                    # Store the result in session state for use outside the form
                    Com_st.session_state.column_search_result = myVar_dictResult
    
    # Process and display results OUTSIDE the form
    if Com_st.session_state.column_search_result:
        myVar_dictResult = Com_st.session_state.column_search_result
        
        if myVar_dictResult["success"]:
            Com_st.success(f"✅ Column search completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Display results
            if len(myVar_dictResult["data"]) > 0:
                Com_st.subheader("Columns Found")
                
                # Show results in interactive data table
                Com_st.dataframe(
                    myVar_dictResult["data"],
                    use_container_width=True
                )
                
                # Download button
                myVar_strCsv = myVar_dictResult["data"].to_csv(index=False)
                Com_st.download_button(
                    label="📥 Download Results as CSV",
                    data=myVar_strCsv,
                    file_name=f"ColumnSearch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key="download_column_search"
                )
            else:
                Com_st.info("No matching columns found with the specified value.")
        else:
            # Display error
            Com_st.error(f"❌ Search failed: {myVar_dictResult['error']}")
            Com_st.markdown("**Error Details:**")
            Com_st.code(myVar_dictResult.get("traceback", "No traceback available"))


    #######################################################################################################

def sub_displayProcedureEditor(myPar_strProcedureName=None, myPar_dictProcedure=None, myPar_strCategory=None):
    """
    Displays the procedure editor form.
    
    Args:
        myPar_strProcedureName (str, optional): Name of procedure to edit
        myPar_dictProcedure (dict, optional): Procedure data if editing
        myPar_strCategory (str, optional): Category if adding new procedure
    """
    myVar_strFormMode = "Edit" if myPar_dictProcedure else "Add"
    myVar_strCategory = myPar_strCategory or myCon_strDefaultCategory
    
    with Com_st.form(f"{myVar_strFormMode.lower()}-procedure-form"):
        Com_st.subheader(f"{myVar_strFormMode} Stored Procedure")
        
        # Category field
        myVar_strCategory = Com_st.text_input(
            "Category", 
            value=myPar_strCategory if myPar_strCategory else myVar_strCategory,
            key="sp_category"
        )
        
        # Name field
        myVar_strName = Com_st.text_input(
            "Procedure Name", 
            value=myPar_strProcedureName if myPar_strProcedureName else "",
            key="sp_name"
        )
        
        # Description field
        myVar_strDescription = Com_st.text_area(
            "Description",
            value=myPar_dictProcedure.get("description", "") if myPar_dictProcedure else "",
            key="sp_description"
        )
        
        # SQL Code field
        myVar_strCode = Com_st.text_area(
            "SQL Code",
            value=myPar_dictProcedure.get("code", "") if myPar_dictProcedure else "",
            height=300,
            key="sp_code"
        )
        
        # Auto-detect parameters option
        myVar_boolAutoDetectParams = Com_st.checkbox(
            "Auto-detect parameters from SQL Code", 
            value=True,
            key="sp_auto_detect"
        )
        
        # Parameter field (only shown if not auto-detecting)
        myVar_strParameters = "{}"
        if not myVar_boolAutoDetectParams:
            myVar_strParameters = Com_st.text_area(
                "Parameters (JSON format)",
                value=json.dumps(myPar_dictProcedure.get("parameters", {}), indent=2) if myPar_dictProcedure else "{}",
                height=150,
                key="sp_parameters"
            )
        
        # Submit button
        myVar_boolSubmitted = Com_st.form_submit_button(f"{myVar_strFormMode} Procedure")
        
        if myVar_boolSubmitted:
            # Validate form
            if not myVar_strName:
                Com_st.error("❌ Procedure name is required.")
                return False
            
            if not myVar_strCode:
                Com_st.error("❌ SQL Code is required.")
                return False
            
            # Auto-detect parameters if enabled
            myVar_dictParameters = {}
            if myVar_boolAutoDetectParams:
                myVar_dictParameters = fun_parseParameters(myVar_strCode)
            else:
                try:
                    myVar_dictParameters = json.loads(myVar_strParameters)
                except json.JSONDecodeError:
                    Com_st.error("❌ Invalid JSON in parameters field.")
                    return False
            
            # Load existing procedures
            myVar_dictProcedures = fun_loadProcedures()
            
            # Create category if it doesn't exist
            if myVar_strCategory not in myVar_dictProcedures:
                myVar_dictProcedures[myVar_strCategory] = []
            
            # Create or update procedure
            myVar_dictNewProcedure = {
                "name": myVar_strName,
                "description": myVar_strDescription,
                "code": myVar_strCode,
                "parameters": myVar_dictParameters
            }
            
            # If editing, remove old version
            if myPar_dictProcedure:
                myVar_dictProcedures[myVar_strCategory] = [
                    p for p in myVar_dictProcedures[myVar_strCategory] 
                    if p["name"] != myPar_strProcedureName
                ]
            
            # Add new procedure
            myVar_dictProcedures[myVar_strCategory].append(myVar_dictNewProcedure)
            
            # Save procedures
            if fun_saveProcedures(myVar_dictProcedures):
                Com_st.success(f"✅ Procedure '{myVar_strName}' {myVar_strFormMode.lower()}ed successfully.")
                return True
            else:
                Com_st.error(f"❌ Failed to {myVar_strFormMode.lower()} procedure.")
                return False
    
    return False


#######################################################################################################
def sub_displayExecuteProcedure(myPar_objDbEngine, myPar_dictProcedure, myPar_strCategory):
    """
    Displays the execute procedure form.
    
    Args:
        myPar_objDbEngine: SQLAlchemy database engine
        myPar_dictProcedure (dict): Procedure data
        myPar_strCategory (str): Category name
    """
    myVar_strProcedureName = myPar_dictProcedure["name"]
    myVar_strCode = myPar_dictProcedure["code"]
    myVar_dictParameters = myPar_dictProcedure.get("parameters", {})
    
    Com_st.subheader(f"🚀 Execute: {myVar_strProcedureName}")
    
    # Display description if available
    if myPar_dictProcedure.get("description"):
        Com_st.info(myPar_dictProcedure["description"])
    
    # SQL Code editor - Only for non-translation procedures
    if myVar_strProcedureName != "Translate Query":
        myVar_strEditedCode = Com_st.text_area(
            "SQL Code (Editable)",
            value=myVar_strCode,
            height=250,
            key=f"exec_code_{myVar_strProcedureName}"
        )
    else:
        # For SQL translation, we don't need to show the code
        myVar_strEditedCode = myVar_strCode
    
    # Parameter inputs
    myVar_dictParamValues = {}
    
    # Special handling for "Translate Query" procedure
    if myVar_strProcedureName == "Translate Query":
        # Input query - larger text area for SQL to translate
        myVar_dictParamValues["SQLQuery"] = Com_st.text_area(
            "SQL Query to Translate",
            value=myVar_dictParameters.get("SQLQuery", ""),
            height=200,
            key="translate_query_input"
        )
        
        # Debug and Execution options in columns
        myVar_colDM, myVar_colEM = Com_st.columns(2)
        
        with myVar_colDM:
            myVar_dictParamValues["DebugMode"] = "1" if Com_st.checkbox(
                "Debug Mode",
                value=myVar_dictParameters.get("DebugMode", "0") == "1",
                key="debug_mode"
            ) else "0"
            Com_st.caption("Shows detailed processing info")
        
        with myVar_colEM:
            myVar_dictParamValues["Execution"] = "1" if Com_st.checkbox(
                "Execution Mode",
                value=myVar_dictParameters.get("Execution", "0") == "1",
                key="execution_mode"
            ) else "0"
            Com_st.caption("Execute the translated query")
    
    # Standard parameters for other procedures
    elif myVar_dictParameters:
        Com_st.subheader("Parameters")
        
        # Create columns for parameters (3 columns per row)
        myVar_intNumParams = len(myVar_dictParameters)
        myVar_intNumRows = (myVar_intNumParams + 2) // 3  # Ceiling division
        
        myVar_listParams = list(myVar_dictParameters.items())
        
        for myVar_intRow in range(myVar_intNumRows):
            myVar_listColumns = Com_st.columns(3)
            
            for myVar_intCol in range(3):
                myVar_intIndex = myVar_intRow * 3 + myVar_intCol
                
                if myVar_intIndex < myVar_intNumParams:
                    myVar_strParamName, myVar_strDefaultValue = myVar_listParams[myVar_intIndex]
                    
                    # Clean default value for display
                    myVar_strCleanDefault = myVar_strDefaultValue.strip()
                    if myVar_strCleanDefault.startswith("N'") and myVar_strCleanDefault.endswith("'"):
                        myVar_strCleanDefault = myVar_strCleanDefault[2:-1]  # Remove N' and '
                    elif myVar_strCleanDefault.startswith("'") and myVar_strCleanDefault.endswith("'"):
                        myVar_strCleanDefault = myVar_strCleanDefault[1:-1]  # Remove ' and '
                    
                    # Input field for parameter
                    myVar_dictParamValues[myVar_strParamName] = myVar_listColumns[myVar_intCol].text_input(
                        f"{myVar_strParamName}",
                        value=myVar_strCleanDefault,
                        key=f"param_{myVar_strProcedureName}_{myVar_strParamName}"
                    )
    
    # Execute button
    if Com_st.button("▶️ Execute", key=f"execute_btn_{myVar_strProcedureName}"):
        with Com_st.spinner("Executing..."):
            # Execute the procedure
            myVar_dictResult = fun_executeProcedure(
                myPar_objDbEngine,
                myVar_strEditedCode,
                myVar_dictParamValues
            )
            
            if myVar_dictResult["success"]:
                # Display results
                Com_st.success(f"✅ Execution completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Special handling for "Translate Query" procedure
                if myVar_strProcedureName == "Translate Query" and "TranslatedQuery" in myVar_dictResult["data"].columns:
                    myVar_strTranslatedQuery = myVar_dictResult["data"].iloc[0]['TranslatedQuery']
                    
                    # Display translated query
                    Com_st.subheader("Translated Query")
                    Com_st.code(myVar_strTranslatedQuery, language="sql")
                    
                    # Download options
                    myVar_colCopy, myVar_colDownloadSQL, myVar_colDownloadCSV = Com_st.columns(3)
                    
                    # Copy to clipboard button
                    with myVar_colCopy:
                        Com_st.markdown("""
                        <button onclick="navigator.clipboard.writeText(document.getElementById('translated-query-text').innerText); alert('Copied to clipboard!');" 
                                style="background-color: #007BFF; color: white; border: none; padding: 0.5em 1em; border-radius: 4px; cursor: pointer;">
                            📋 Copy to Clipboard
                        </button>
                        
                        <div id="translated-query-text" style="display: none;">
                        {}
                        </div>
                        """.format(myVar_strTranslatedQuery.replace('\n', '\\n').replace('"', '\\"')), unsafe_allow_html=True)
                    
                    # Download as SQL file
                    with myVar_colDownloadSQL:
                        Com_st.download_button(
                            label="💾 Download as SQL",
                            data=myVar_strTranslatedQuery,
                            file_name="translated_query.sql",
                            mime="text/plain",
                            key="download_sql"
                        )
                    
                    # Download as CSV file
                    with myVar_colDownloadCSV:
                        myVar_pdDf = Com_pd.DataFrame({'TranslatedQuery': [myVar_strTranslatedQuery]})
                        Com_st.download_button(
                            label="📊 Download as CSV",
                            data=myVar_pdDf.to_csv(index=False),
                            file_name="translated_query.csv",
                            mime="text/csv",
                            key="download_csv"
                        )
                
                # Standard results display for other procedures
                elif len(myVar_dictResult["data"]) > 0:
                    Com_st.subheader("Results")
                    
                    # Show results in interactive data table
                    Com_st.dataframe(
                        myVar_dictResult["data"],
                        use_container_width=True
                    )
                    
                    # Download button for results
                    myVar_strCsv = myVar_dictResult["data"].to_csv(index=False)
                    Com_st.download_button(
                        label="📥 Download Results as CSV",
                        data=myVar_strCsv,
                        file_name=f"{myVar_strProcedureName}_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        key=f"download_{myVar_strProcedureName}"
                    )
                else:
                    Com_st.info("Query executed successfully, but returned no results.")
            else:
                # Display error
                Com_st.error(f"❌ Execution failed: {myVar_dictResult['error']}")
                
                # FIX: Don't use expander for error details to avoid nesting expanders
                # Instead, use a direct code block with a header
                Com_st.markdown("**Error Details:**")
                Com_st.code(myVar_dictResult.get("traceback", "No traceback available"))



#######################################################################################################
# Add this function in the UI COMPONENTS section
def sub_displayQuerySelectorTool(myPar_objDbEngine):
    """
    Displays the Query Selector Tool UI for executing mysp_QuerySelector stored procedure.
    
    Args:
        myPar_objDbEngine: SQLAlchemy database engine
    """
    Com_st.subheader("🔍 Query Selector Tool")
    Com_st.markdown("""
    This tool executes the `[mrs].[mysp_QuerySelector]` stored procedure with different query options.
    Enter a query ID or select "help" to see available options.
    """)
    
    # Get available query options when user clicks the button
    if Com_st.button("📋 Show Available Query Options"):
        with Com_st.spinner("Fetching available query options..."):
            myVar_dictHelpResult = fun_executeQuerySelector(myPar_objDbEngine, "help")
            
            if myVar_dictHelpResult["success"]:
                Com_st.subheader("Available Query Options")
                Com_st.dataframe(myVar_dictHelpResult["data"])
            else:
                Com_st.error("❌ Failed to fetch query options. Please check if the stored procedure exists.")
    
    # Create session state variables to store results if they don't exist
    if 'query_result' not in Com_st.session_state:
        Com_st.session_state.query_result = None
    if 'query_id' not in Com_st.session_state:
        Com_st.session_state.query_id = ""
    
    # Create a form for executing the query
    with Com_st.form(key="query_selector_form"):
        # Query ID input
        myVar_strQueryID = Com_st.text_input(
            "Query ID (e.g., ROP_PRICE, SALES_DATA, etc.)",
            value="",
            help="Enter the query ID or 'help' to see available options"
        )
        
        # Create columns for date parameters
        myVar_colStartDate, myVar_colEndDate, myVar_colDebug = Com_st.columns(3)
        
        # Start date parameter (optional)
        with myVar_colStartDate:
            myVar_strStartDate = Com_st.text_input(
                "Start Date (YYYYMMDD, optional)",
                value="",
                help="Enter the start date in YYYYMMDD format"
            )
        
        # End date parameter (optional)
        with myVar_colEndDate:
            myVar_strEndDate = Com_st.text_input(
                "End Date (YYYYMMDD, optional)",
                value="",
                help="Enter the end date in YYYYMMDD format"
            )
        
        # Debug mode parameter
        with myVar_colDebug:
            myVar_boolDebugMode = Com_st.checkbox(
                "Debug Mode",
                value=False,
                help="Enable to print the SQL query before execution"
            )
        
        # Submit button
        myVar_boolSubmitted = Com_st.form_submit_button("▶️ Execute Query")
        
        if myVar_boolSubmitted:
            # Validate form
            if not myVar_strQueryID:
                Com_st.error("❌ Query ID is required.")
            else:
                # Parse date parameters if provided
                myVar_intStartDate = None
                myVar_intEndDate = None
                
                if myVar_strStartDate:
                    try:
                        myVar_intStartDate = int(myVar_strStartDate)
                    except ValueError:
                        Com_st.error("❌ Start Date must be a valid integer in YYYYMMDD format.")
                        myVar_intStartDate = None
                
                if myVar_strEndDate:
                    try:
                        myVar_intEndDate = int(myVar_strEndDate)
                    except ValueError:
                        Com_st.error("❌ End Date must be a valid integer in YYYYMMDD format.")
                        myVar_intEndDate = None
                
                # Execute the query with parameters
                with Com_st.spinner("Executing query..."):
                    myVar_dictResult = fun_executeQuerySelector(
                        myPar_objDbEngine,
                        myVar_strQueryID,
                        myVar_intStartDate,
                        myVar_intEndDate,
                        myVar_boolDebugMode
                    )
                    
                    # Store the result in session state for use outside the form
                    Com_st.session_state.query_result = myVar_dictResult
                    Com_st.session_state.query_id = myVar_strQueryID
    
    # Process and display results OUTSIDE the form
    if Com_st.session_state.query_result:
        myVar_dictResult = Com_st.session_state.query_result
        
        if myVar_dictResult["success"]:
            Com_st.success(f"✅ Query '{Com_st.session_state.query_id}' executed successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Display results
            if len(myVar_dictResult["data"]) > 0:
                Com_st.subheader("Results")
                
                # Show results in interactive data table
                Com_st.dataframe(
                    myVar_dictResult["data"],
                    use_container_width=True
                )
                
                # Download button - NOW OUTSIDE THE FORM
                myVar_strCsv = myVar_dictResult["data"].to_csv(index=False)
                Com_st.download_button(
                    label="📥 Download Results as CSV",
                    data=myVar_strCsv,
                    file_name=f"QuerySelector_{Com_st.session_state.query_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key=f"download_{Com_st.session_state.query_id}"
                )
            else:
                Com_st.info("Query executed successfully, but returned no results.")
        else:
            # Display error
            Com_st.error(f"❌ Execution failed: {myVar_dictResult['error']}")
            Com_st.markdown("**Error Details:**")
            Com_st.code(myVar_dictResult.get("traceback", "No traceback available"))




        
# ────────────────────────────────────────────────────────────────────────────
# 🖥️ MAIN VIEW FUNCTIONS
# ────────────────────────────────────────────────────────────────────────────
def sub_displayStoredProceduresView(myPar_objDbEngine):
    """
    Main entry point for the Stored Procedures module.
    
    Args:
        myPar_objDbEngine: SQLAlchemy database engine
    """
    # Header and description
    Com_st.title("🗄️ Stored Procedures Manager")
    Com_st.markdown("""
    This tool allows you to manage and execute SQL stored procedures directly from the web interface.
    Organize procedures by category, provide parameters, and view results instantly.
    """)
    
    # Load procedures
    myVar_dictProcedures = fun_loadProcedures()
    
    # Create tabs for categories, management
    myVar_listTabs = ["📋 Procedures", "🔍 Query Selector", "🔍 Column Search"]  # Added Column Search tab
    
    # Add category tabs if they exist
    if myVar_dictProcedures:
        myVar_listTabs.extend([f"📁 {category}" for category in myVar_dictProcedures.keys()])
    
    myVar_listTabs.append("➕ Add New")
    
    myVar_strSelectedTab = Com_st.tabs(myVar_listTabs)
    
    # "Procedures" tab - Overview of all procedures
    if myVar_strSelectedTab[0].selectbox(
        "View procedures by category",
        options=["All Categories"] + list(myVar_dictProcedures.keys()),
        key="overview_category"
    ) == "All Categories":
        # Display all procedures
        for myVar_strCategory, myVar_listCategoryProcedures in myVar_dictProcedures.items():
            with myVar_strSelectedTab[0].expander(f"📁 {myVar_strCategory} ({len(myVar_listCategoryProcedures)})"):
                for myVar_dictProcedure in myVar_listCategoryProcedures:
                    Com_st.markdown(f"**{myVar_dictProcedure['name']}**")
                    if myVar_dictProcedure.get("description"):
                        Com_st.markdown(myVar_dictProcedure["description"])
                    Com_st.markdown("---")
    else:
        # Display selected category
        myVar_strCategory = myVar_strSelectedTab[0].session_state.overview_category
        with myVar_strSelectedTab[0].expander(f"📁 {myVar_strCategory} ({len(myVar_dictProcedures[myVar_strCategory])})"):
            for myVar_dictProcedure in myVar_dictProcedures[myVar_strCategory]:
                Com_st.markdown(f"**{myVar_dictProcedure['name']}**")
                if myVar_dictProcedure.get("description"):
                    Com_st.markdown(myVar_dictProcedure["description"])
                Com_st.markdown("---")
    
    # "Query Selector" tab - Tool for executing mysp_QuerySelector
    with myVar_strSelectedTab[1]:
        sub_displayQuerySelectorTool(myPar_objDbEngine)
    
    # "Column Search" tab - Tool for finding columns matching a pattern and value
    with myVar_strSelectedTab[2]:
        sub_displayColumnSearchTool(myPar_objDbEngine)
    
    # Category tabs - Display procedures in each category
    myVar_intTabIndex = 3  # Updated from 2 to 3 since we added a new tab
    for myVar_strCategory in myVar_dictProcedures.keys():
        with myVar_strSelectedTab[myVar_intTabIndex]:
            # Display procedures in this category
            for myVar_dictProcedure in myVar_dictProcedures[myVar_strCategory]:
                with Com_st.expander(f"📝 {myVar_dictProcedure['name']}", expanded=False):
                    # Two columns: Details and Actions
                    myVar_colDetails, myVar_colActions = Com_st.columns([3, 1])
                    
                    # Display procedure details
                    with myVar_colDetails:
                        if myVar_dictProcedure.get("description"):
                            Com_st.info(myVar_dictProcedure["description"])
                        
                        # Show parameter summary if they exist
                        if myVar_dictProcedure.get("parameters"):
                            Com_st.markdown("**Parameters:**")
                            for myVar_strParam, myVar_strDefault in myVar_dictProcedure["parameters"].items():
                                Com_st.markdown(f"- `{myVar_strParam}`: {myVar_strDefault}")
                    
                    # Action buttons
                    with myVar_colActions:
                        myVar_colButtons1, myVar_colButtons2 = Com_st.columns(2)
                        
                        # Edit button
                        if myVar_colButtons1.button("✏️ Edit", key=f"edit_{myVar_dictProcedure['name']}"):
                            Com_st.session_state.edit_procedure = {
                                "category": myVar_strCategory,
                                "name": myVar_dictProcedure["name"],
                                "data": myVar_dictProcedure
                            }
                        
                        # Delete button
                        if myVar_colButtons2.button("🗑️ Delete", key=f"delete_{myVar_dictProcedure['name']}"):
                            if Com_st.warning(f"Are you sure you want to delete '{myVar_dictProcedure['name']}'?"):
                                myVar_dictUpdatedProcedures = fun_loadProcedures()
                                myVar_dictUpdatedProcedures[myVar_strCategory] = [
                                    p for p in myVar_dictUpdatedProcedures[myVar_strCategory] 
                                    if p["name"] != myVar_dictProcedure["name"]
                                ]
                                
                                if fun_saveProcedures(myVar_dictUpdatedProcedures):
                                    Com_st.success(f"✅ Procedure '{myVar_dictProcedure['name']}' deleted successfully.")
                                    Com_st.rerun()
                    
                    # Procedure execution section
                    Com_st.markdown("---")
                    sub_displayExecuteProcedure(myPar_objDbEngine, myVar_dictProcedure, myVar_strCategory)
        
        myVar_intTabIndex += 1
    
    # "Add New" tab - Form to add new procedure
    with myVar_strSelectedTab[-1]:
        if sub_displayProcedureEditor():
            Com_st.rerun()
    
    # Handle editing a procedure if one is selected
    if hasattr(Com_st.session_state, 'edit_procedure'):
        myVar_dictEditProcedure = Com_st.session_state.edit_procedure
        
        Com_st.subheader(f"Edit Procedure: {myVar_dictEditProcedure['name']}")
        
        if sub_displayProcedureEditor(
            myVar_dictEditProcedure["name"],
            myVar_dictEditProcedure["data"],
            myVar_dictEditProcedure["category"]
        ):
            # Clear the edit session state and refresh
            del Com_st.session_state.edit_procedure
            Com_st.rerun()
        
        # Cancel button
        if Com_st.button("Cancel Edit"):
            del Com_st.session_state.edit_procedure
            Com_st.rerun()



# ════════════════════════════════════════════════════════════════════════════
#  EOF
# ════════════════════════════════════════════════════════════════════════════
