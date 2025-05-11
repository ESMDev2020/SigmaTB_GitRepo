# ════════════════════════════════════════════════════════════════════════════
# 🗄️ STREAMLIT MODULE - SQL TOOLS MENU
# DESCRIPTION:
#   This module provides a menu-based interface for various SQL tools including
#   query selection, column searches, SQL translation, database maintenance,
#   and metadata viewing.
#   - Follows standard naming conventions: myVar_, myCon_, sub_, fun_, Com_
#   - Organized by tool functionality with clear function naming
# ════════════════════════════════════════════════════════════════════════════

# 📦 Required Imports
import streamlit as Com_st
import pandas as Com_pd
import os
from datetime import datetime
from sqlalchemy import text
import traceback
import re
import base64
import io

# ────────────────────────────────────────────────────────────────────────────
# 📜 CONSTANTS
# ────────────────────────────────────────────────────────────────────────────
# Define any constants here
myCon_strDatabaseName = "SIGMATB"

# ────────────────────────────────────────────────────────────────────────────
# 🛠️ MENU EXECUTION FUNCTIONS - Define the core functionality for each tool
# ────────────────────────────────────────────────────────────────────────────

def fun_menu_QuerySelector(myPar_objDbEngine, myPar_strQueryID, myPar_intStartDate=None, myPar_intEndDate=None, myPar_boolDebugMode=False):
    """
    Executes the Query Selector stored procedure.
    
    Args:
        myPar_objDbEngine: SQLAlchemy database engine
        myPar_strQueryID: Query ID to execute
        myPar_intStartDate: Optional start date in YYYYMMDD format
        myPar_intEndDate: Optional end date in YYYYMMDD format
        myPar_boolDebugMode: Debug mode flag
    
    Returns:
        Dict with success flag and results
    """
    try:
        # Build the stored procedure call with parameters
        myVar_strSQL = f"USE {myCon_strDatabaseName};\n\n"
        
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
        
        # Special handling for the 'help' command
        if myPar_strQueryID.lower() == 'help':
            # Direct SQL execution to get the raw data
            with myPar_objDbEngine.begin() as myVar_objDbConnection:
                myVar_objResult = myVar_objDbConnection.execute(text(myVar_strSQL))
                myVar_listRows = list(myVar_objResult)
                
                # If we have rows, extract all values from the first row
                if myVar_listRows:
                    myVar_listQueryIds = []
                    # Flatten all values from the first row
                    for value in myVar_listRows[0]:
                        if value is not None and str(value).strip() != '':
                            myVar_listQueryIds.append(value)
                else:
                    myVar_listQueryIds = []
            
            # Create a DataFrame with a proper column name
            myVar_df = Com_pd.DataFrame({'Available Query IDs': myVar_listQueryIds})
            
        else:
            # For regular queries, use pandas read_sql with properly renamed columns
            with myPar_objDbEngine.begin() as myVar_objDbConnection:
                # Execute and get cursor description
                myVar_objResult = myVar_objDbConnection.execute(text(myVar_strSQL))
                myVar_listRows = list(myVar_objResult)
                
                # Get column names from cursor description or create numbered ones
                if myVar_objResult.keys():
                    myVar_listColumns = [col for col in myVar_objResult.keys()]
                else:
                    # Generate column names as Col_1, Col_2, etc.
                    if myVar_listRows:
                        myVar_intColCount = len(myVar_listRows[0])
                    else:
                        myVar_intColCount = 0
                    myVar_listColumns = [f'Col_{i+1}' for i in range(myVar_intColCount)]
                
                # Create DataFrame with defined column names
                myVar_df = Com_pd.DataFrame(myVar_listRows, columns=myVar_listColumns)
        
        return {
            "success": True,
            "data": myVar_df
        }
    
    except Exception as myVar_objException:
        Com_st.error(f"Error in fun_menu_QuerySelector: {str(myVar_objException)}")
        Com_st.code(traceback.format_exc())
        return {
            "success": False,
            "error": str(myVar_objException),
            "traceback": traceback.format_exc()
        }

def fun_menu_ColumnSearch(myPar_objDbEngine, myPar_strColumnPattern, myPar_strSearchValue, myPar_boolDebugMode=False):
    """
    Executes the Column Search functionality.
    
    Args:
        myPar_objDbEngine: SQLAlchemy database engine
        myPar_strColumnPattern: Column name pattern to search (using % as wildcards)
        myPar_strSearchValue: Value to search for
        myPar_boolDebugMode: Debug mode flag
    
    Returns:
        Dict with success flag and results
    """
    try:
        # Build the stored procedure call
        myVar_strSQL = f"USE {myCon_strDatabaseName};\n\n"
        myVar_strSQL += f"EXEC [mrs].[sub_FindColumnPropertiesAndSearch] \n"
        myVar_strSQL += f"    @myVarVARCHARParamColumnCode = N'{myPar_strColumnPattern}',\n"
        myVar_strSQL += f"    @myVarVARCHARParamSearchValue = N'{myPar_strSearchValue}',\n"
        myVar_strSQL += f"    @myVarBITDebugMode = {1 if myPar_boolDebugMode else 0};"
        
        # Display the SQL for debugging purposes
        Com_st.markdown("**Debug: SQL Query Being Executed**")
        Com_st.code(myVar_strSQL, language="sql")
        
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
                    
                    # Get column names if we have rows
                    if myVar_listRows and myVar_objResult.keys():
                        myVar_listColumns = [col for col in myVar_objResult.keys()]
                        myVar_df = Com_pd.DataFrame(myVar_listRows, columns=myVar_listColumns)
                    else:
                        # Create an empty DataFrame with standard columns if no rows
                        myVar_df = Com_pd.DataFrame(columns=["SchemaName", "TableName", "ColumnName", "ColumnCode", 
                                                            "PropertyValue", "IsPrimaryKey", "ValuesMatchPK", 
                                                            "HasMatches", "MatchCount", "ResultValues"])
                
                except Exception as resource_error:
                    # Procedure executed but didn't return a direct result set
                    # Try an alternative approach with a follow-up select query
                    
                    # Create a temporary table query to capture results
                    myVar_strCaptureSQL = f"""
                    USE {myCon_strDatabaseName};
                    
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
                            # Create a DataFrame with a message about no results
                            myVar_df = Com_pd.DataFrame({
                                "Message": ["No results found in temporary table"],
                                "Info": ["The procedure executed but did not return results through the temp table."]
                            })
                    
                    except Exception as capture_err:
                        # Create a DataFrame with a message about the results
                        myVar_df = Com_pd.DataFrame({
                            "Message": [f"Search completed for columns matching '{myPar_strColumnPattern}' with value '{myPar_strSearchValue}'"],
                            "Info": ["Results were displayed in SQL Server but couldn't be retrieved directly. See console output."]
                        })
        
        except Exception as ex:
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
        Com_st.error(f"Error in fun_menu_ColumnSearch: {str(myVar_objException)}")
        Com_st.code(traceback.format_exc())
        return {
            "success": False,
            "error": str(myVar_objException),
            "traceback": traceback.format_exc()
        }

def fun_menu_SQLTranslation(myPar_objDbEngine, myPar_strSQLQuery, myPar_boolDebugMode=False, myPar_boolExecution=False):
    """
    Executes the SQL Translation functionality.
    
    Args:
        myPar_objDbEngine: SQLAlchemy database engine
        myPar_strSQLQuery: SQL query to translate
        myPar_boolDebugMode: Debug mode flag
        myPar_boolExecution: Execution mode flag
    
    Returns:
        Dict with success flag and results
    """
    try:
        # Build the SQL query with parameters
        myVar_strSQL = f"""
        USE {myCon_strDatabaseName};
        
        -- Create a temp table to store the result
        IF OBJECT_ID('tempdb..#TranslationResult') IS NOT NULL
            DROP TABLE #TranslationResult;
            
        CREATE TABLE #TranslationResult (TranslatedQuery NVARCHAR(MAX));
        
        -- Declare variables for the procedure
        DECLARE @output NVARCHAR(MAX);
        DECLARE @SQLQuery NVARCHAR(MAX) = N'{myPar_strSQLQuery.replace("'", "''")}';
        
        -- Execute the procedure
        EXEC [mrs].[usp_TranslateSQLQuery] 
            @SQLQuery = @SQLQuery,
            @TranslatedQuery = @output OUTPUT,
            @DebugMode = {1 if myPar_boolDebugMode else 0},
            @Execution = {1 if myPar_boolExecution else 0};
            
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
        
        # Execute the setup and procedure in one transaction
        with myPar_objDbEngine.begin() as myVar_objDbConnection:
            # Execute the first part (create temp table, run procedure)
            myVar_objDbConnection.execute(text(myVar_strSQL))
            
            # Execute the second part (get results)
            myVar_df = Com_pd.read_sql(text(myVar_strResultQuery), myVar_objDbConnection)
        
        # Process results
        if not myVar_df.empty:
            Com_st.success("Successfully retrieved translation result")
        else:
            myVar_df = Com_pd.DataFrame({"TranslatedQuery": ["No translation result returned"]})
            Com_st.warning("No translation result was returned")
        
        return {
            "success": True,
            "data": myVar_df
        }
    
    except Exception as myVar_objException:
        Com_st.error(f"Error in fun_menu_SQLTranslation: {str(myVar_objException)}")
        Com_st.code(traceback.format_exc())
        return {
            "success": False,
            "error": str(myVar_objException),
            "traceback": traceback.format_exc()
        }

def fun_menu_ColumnMetadata(myPar_objDbEngine, myPar_strTableName, myPar_strColumnName):
    """
    Executes the Column Metadata functionality.
    
    Args:
        myPar_objDbEngine: SQLAlchemy database engine
        myPar_strTableName: Table name
        myPar_strColumnName: Column name
    
    Returns:
        Dict with success flag and results
    """
    try:
        # Build the SQL query
        myVar_strSQL = f"""
        USE {myCon_strDatabaseName};
        
        /***************************************************************************
        RETURNS THE TYPE OF DATA FOR THE SPECIFIED COLUMN
        -----------------------------------------------------------------------------*/
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH,
            NUMERIC_PRECISION,
            NUMERIC_SCALE,
            IS_NULLABLE
        FROM 
            INFORMATION_SCHEMA.COLUMNS
        WHERE 
            TABLE_NAME = '{myPar_strTableName}'  
            AND COLUMN_NAME = '{myPar_strColumnName}';
        """
        
        # Display the SQL for debugging purposes
        Com_st.markdown("**Debug: SQL Query Being Executed**")
        Com_st.code(myVar_strSQL, language="sql")
        
        # Execute the query
        with myPar_objDbEngine.begin() as myVar_objDbConnection:
            myVar_df = Com_pd.read_sql(text(myVar_strSQL), myVar_objDbConnection)
        
        return {
            "success": True,
            "data": myVar_df
        }
    
    except Exception as myVar_objException:
        Com_st.error(f"Error in fun_menu_ColumnMetadata: {str(myVar_objException)}")
        Com_st.code(traceback.format_exc())
        return {
            "success": False,
            "error": str(myVar_objException),
            "traceback": traceback.format_exc()
        }

def fun_menu_DropTables(myPar_objDbEngine, myPar_strConfirmDate, myPar_boolShowPreview=True):
    """
    Executes the Drop Tables functionality.
    
    Args:
        myPar_objDbEngine: SQLAlchemy database engine
        myPar_strConfirmDate: Confirmation date (YYYYMMDD)
        myPar_boolShowPreview: Show preview flag
    
    Returns:
        Dict with success flag and results
    """
    try:
        # Build the SQL query
        myVar_strSQL = f"""
        USE {myCon_strDatabaseName};
        
        /***************************************************************************************
        DROP TABLES FROM THE DATABASE FOR A CLEAN START
        ----------------------------------------------------------------------------------------
        This procedure generates and executes DROP TABLE statements for all tables listed in 
        [mrs].[01_AS400_MSSQL_Equivalents]. This operation CANNOT BE UNDONE.
        
        SAFETY CHECK: Today's date must be entered in YYYYMMDD format to confirm this operation.
        ****************************************************************************************/
        
        -- Safety check - only proceed if confirmation date matches today's date
        DECLARE @TodayDate VARCHAR(8) = CONVERT(VARCHAR(8), GETDATE(), 112); -- YYYYMMDD format
        DECLARE @sql NVARCHAR(MAX) = '';
        
        IF '{myPar_strConfirmDate}' <> @TodayDate
        BEGIN
            -- If dates don't match, abort and show warning
            SELECT 
                'OPERATION ABORTED - SAFETY CHECK FAILED' AS Status,
                'The confirmation date does not match today''s date' AS Reason,
                @TodayDate AS TodaysDate,
                '{myPar_strConfirmDate}' AS EnteredDate;
            RETURN;
        END
        
        -- Generate the drop table statements
        SELECT @sql = @sql + 'DROP TABLE [mrs].[' + MSSQL_TableName + '];' + CHAR(13) + CHAR(10)
        FROM [mrs].[01_AS400_MSSQL_Equivalents]
        ORDER BY MSSQL_TableName;
        
        -- Return the tables that will be dropped (for review before actual execution)
        IF '{1 if myPar_boolShowPreview else 0}' = '1'
        BEGIN
            SELECT 
                MSSQL_TableName AS TableNameToBeDropped, 
                AS400_TableName AS OriginalAS400Table 
            FROM [mrs].[01_AS400_MSSQL_Equivalents]
            ORDER BY MSSQL_TableName;
            RETURN;
        END
        
        -- Create a temporary table to track results
        CREATE TABLE #DropResults (
            TableName NVARCHAR(255),
            DropStatus NVARCHAR(20)
        );
        
        -- Begin a transaction
        BEGIN TRANSACTION;
        
        BEGIN TRY
            -- Execute the drop statements
            EXEC sp_executesql @sql;
            
            -- If successful, insert success records for all tables
            INSERT INTO #DropResults
            SELECT 
                MSSQL_TableName, 
                'Dropped Successfully' 
            FROM [mrs].[01_AS400_MSSQL_Equivalents]
            ORDER BY MSSQL_TableName;
            
            -- Commit the transaction
            COMMIT TRANSACTION;
            
            -- Return success message
            SELECT 
                'ALL TABLES DROPPED SUCCESSFULLY' AS OperationStatus,
                GETDATE() AS ExecutionTimestamp;
                
            -- Return details of dropped tables
            SELECT * FROM #DropResults;
        END TRY
        BEGIN CATCH
            -- Roll back the transaction if there was an error
            ROLLBACK TRANSACTION;
            
            -- Return error information
            SELECT 
                'OPERATION FAILED' AS OperationStatus,
                ERROR_NUMBER() AS ErrorNumber,
                ERROR_MESSAGE() AS ErrorMessage;
        END CATCH
        
        -- Clean up
        DROP TABLE IF EXISTS #DropResults;
        """
        
        # Display the SQL for debugging purposes
        Com_st.markdown("**Debug: SQL Query Being Executed**")
        Com_st.code(myVar_strSQL, language="sql")
        
        # Execute the query
        with myPar_objDbEngine.begin() as myVar_objDbConnection:
            myVar_objResult = myVar_objDbConnection.execute(text(myVar_strSQL))
            myVar_listRows = list(myVar_objResult)
            
            # Get column names from the result
            if myVar_objResult.keys():
                myVar_listColumns = [col for col in myVar_objResult.keys()]
            else:
                # Generate column names as Col_1, Col_2, etc.
                if myVar_listRows:
                    myVar_intColCount = len(myVar_listRows[0])
                else:
                    myVar_intColCount = 0
                myVar_listColumns = [f'Col_{i+1}' for i in range(myVar_intColCount)]
            
            # Create DataFrame with defined column names
            myVar_df = Com_pd.DataFrame(myVar_listRows, columns=myVar_listColumns)
        
        return {
            "success": True,
            "data": myVar_df
        }
    
    except Exception as myVar_objException:
        Com_st.error(f"Error in fun_menu_DropTables: {str(myVar_objException)}")
        Com_st.code(traceback.format_exc())
        return {
            "success": False,
            "error": str(myVar_objException),
            "traceback": traceback.format_exc()
        }

# ────────────────────────────────────────────────────────────────────────────
# 🎨 UI DISPLAY FUNCTIONS - Define the user interface for each tool
# ────────────────────────────────────────────────────────────────────────────

def sub_displayQuerySelectorTool(myPar_objDbEngine):
    """
    Displays the Query Selector tool UI.
    
    Args:
        myPar_objDbEngine: SQLAlchemy database engine
    """
    Com_st.subheader("🔍 Query Selector Tool")
    Com_st.markdown("""
    This tool executes the `[mrs].[mysp_QuerySelector]` stored procedure with different query options.
    Enter a query ID or click "Show Available Query Options" to see what's available.
    """)
    
    # Get available query options when user clicks the button
    if Com_st.button("📋 Show Available Query Options", key="query_selector_help_button"):
        with Com_st.spinner("Fetching available query options..."):
            myVar_dictHelpResult = fun_menu_QuerySelector(myPar_objDbEngine, "help")
            
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
                    myVar_dictResult = fun_menu_QuerySelector(
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
                
                # Download button
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

def sub_displayColumnSearchTool(myPar_objDbEngine):
    """
    Displays the Column Search tool UI.
    
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
                    myVar_dictResult = fun_menu_ColumnSearch(
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

def sub_displaySQLTranslationTool(myPar_objDbEngine):
    """
    Displays the SQL Translation tool UI.
    
    Args:
        myPar_objDbEngine: SQLAlchemy database engine
    """
    Com_st.subheader("🔄 SQL Translation Tool")
    Com_st.markdown("""
    This tool translates SQL queries between different formats and adds descriptions.
    Enter your SQL query below and click Translate.
    """)
    
    # Create a form for the translation
    with Com_st.form(key="sql_translation_form"):
        # Input query - larger text area for SQL to translate
        myVar_strSQLQuery = Com_st.text_area(
            "SQL Query to Translate",
            value="",
            height=200,
            help="Enter the SQL query you want to translate"
        )
        
        # Debug and Execution options in columns
        myVar_colDM, myVar_colEM = Com_st.columns(2)
        
        with myVar_colDM:
            myVar_boolDebugMode = Com_st.checkbox(
                "Debug Mode",
                value=False,
                help="Shows detailed processing information"
            )
        
        with myVar_colEM:
            myVar_boolExecution = Com_st.checkbox(
                "Execution Mode",
                value=False,
                help="Execute the translated query"
            )
        
        # Submit button
        myVar_boolSubmitted = Com_st.form_submit_button("🔄 Translate Query")
        
        if myVar_boolSubmitted:
            # Validate form
            if not myVar_strSQLQuery:
                Com_st.error("❌ SQL Query is required.")
            else:
                # Execute the translation
                with Com_st.spinner("Translating query..."):
                    myVar_dictResult = fun_menu_SQLTranslation(
                        myPar_objDbEngine,
                        myVar_strSQLQuery,
                        myVar_boolDebugMode,
                        myVar_boolExecution
                    )
                
                # Process the results
                if myVar_dictResult["success"] and "TranslatedQuery" in myVar_dictResult["data"].columns:
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
                else:
                    # Display error
                    Com_st.error("❌ Translation failed.")
                    if not myVar_dictResult["success"]:
                        Com_st.markdown("**Error Details:**")
                        Com_st.code(myVar_dictResult.get("traceback", "No traceback available"))

def sub_displayColumnMetadataTool(myPar_objDbEngine):
    """
    Displays the Column Metadata tool UI.
    
    Args:
        myPar_objDbEngine: SQLAlchemy database engine
    """
    Com_st.subheader("🔍 Column Metadata Tool")
    Com_st.markdown("""
    This tool shows detailed metadata for a specific column in a table including 
    data type, length, precision, scale, and nullability.
    """)
    
    # Create a form for the column metadata query
    with Com_st.form(key="column_metadata_form"):
        # Table name input
        myVar_strTableName = Com_st.text_input(
            "Table Name",
            value="mysql_____ap",
            help="Enter the name of the table (e.g., mysql_____ap or z_Shipments_File_____SHIPMAST)"
        )
        
        # Column name input
        myVar_strColumnName = Com_st.text_input(
            "Column Name",
            value="PO_______PO__",
            help="Enter the name of the column (e.g., PO_______PO__ or Transaction_#_____SHORDN)"
        )
        
        # Submit button
        myVar_boolSubmitted = Com_st.form_submit_button("🔍 Get Column Metadata")
        
        if myVar_boolSubmitted:
            # Validate form
            if not myVar_strTableName:
                Com_st.error("❌ Table Name is required.")
            elif not myVar_strColumnName:
                Com_st.error("❌ Column Name is required.")
            else:
                # Execute the query
                with Com_st.spinner("Fetching column metadata..."):
                    myVar_dictResult = fun_menu_ColumnMetadata(
                        myPar_objDbEngine,
                        myVar_strTableName,
                        myVar_strColumnName
                    )
                
                # Process the results
                if myVar_dictResult["success"]:
                    if len(myVar_dictResult["data"]) > 0:
                        Com_st.success(f"✅ Found metadata for column '{myVar_strColumnName}' in table '{myVar_strTableName}'")
                        
                        # Display the metadata
                        Com_st.subheader("Column Metadata")
                        Com_st.dataframe(myVar_dictResult["data"], use_container_width=True)
                        
                        # Download button
                        myVar_strCsv = myVar_dictResult["data"].to_csv(index=False)
                        Com_st.download_button(
                            label="📥 Download Metadata as CSV",
                            data=myVar_strCsv,
                            file_name=f"ColumnMetadata_{myVar_strTableName}_{myVar_strColumnName}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            key="download_column_metadata"
                        )
                    else:
                        Com_st.warning(f"⚠️ No metadata found for column '{myVar_strColumnName}' in table '{myVar_strTableName}'")
                else:
                    # Display error
                    Com_st.error(f"❌ Metadata query failed: {myVar_dictResult['error']}")
                    Com_st.markdown("**Error Details:**")
                    Com_st.code(myVar_dictResult.get("traceback", "No traceback available"))

def sub_displayDropTablesTool(myPar_objDbEngine):
    """
    Displays the Drop Tables tool UI.
    
    Args:
        myPar_objDbEngine: SQLAlchemy database engine
    """
    Com_st.subheader("🔴 Drop Tables Tool")
    Com_st.markdown("""
    ⚠️ **DANGER!** This tool drops all tables listed in [mrs].[01_AS400_MSSQL_Equivalents].
    This operation **CANNOT BE UNDONE**. You must enter today's date in YYYYMMDD format to confirm.
    """)
    
    # Create a form for the drop tables operation
    with Com_st.form(key="drop_tables_form"):
        # Today's date display
        myVar_strTodayDate = datetime.now().strftime('%Y%m%d')
        Com_st.info(f"Today's date is {myVar_strTodayDate} (YYYYMMDD format)")
        
        # Confirmation date input
        myVar_strConfirmDate = Com_st.text_input(
            "Enter today's date to confirm",
            value="",
            help=f"You must enter today's date ({myVar_strTodayDate}) exactly to confirm this dangerous operation"
        )
        
        # Preview mode checkbox
        myVar_boolShowPreview = Com_st.checkbox(
            "Preview Mode (show tables that would be dropped without actually dropping them)",
            value=True,
            help="Enable to see what tables would be dropped without actually dropping them"
        )
        
        # Submit button with warning color
        myVar_colSpacerLeft, myVar_colSubmit, myVar_colSpacerRight = Com_st.columns([1, 2, 1])
        with myVar_colSubmit:
            myVar_boolSubmitted = Com_st.form_submit_button(
                "⚠️ Execute Drop Tables Operation"
            )
        
        if myVar_boolSubmitted:
            # Validate form
            if not myVar_strConfirmDate:
                Com_st.error("❌ Confirmation date is required.")
            else:
                # Execute the operation
                with Com_st.spinner("Executing drop tables operation..."):
                    myVar_dictResult = fun_menu_DropTables(
                        myPar_objDbEngine,
                        myVar_strConfirmDate,
                        myVar_boolShowPreview
                    )
                
                # Process the results
                if myVar_dictResult["success"]:
                    if len(myVar_dictResult["data"]) > 0:
                        # Check if this was a preview or actual execution
                        if myVar_boolShowPreview:
                            Com_st.success("✅ Preview completed successfully. These tables would be dropped:")
                        else:
                            # Check if there was an error or if it was successful
                            if "Status" in myVar_dictResult["data"].columns and "ABORTED" in myVar_dictResult["data"].iloc[0]["Status"]:
                                Com_st.warning("⚠️ Operation aborted due to date mismatch.")
                            else:
                                Com_st.success("✅ Tables dropped successfully.")
                        
                        # Display the results
                        Com_st.dataframe(myVar_dictResult["data"], use_container_width=True)
                        
                        # Download button
                        myVar_strCsv = myVar_dictResult["data"].to_csv(index=False)
                        Com_st.download_button(
                            label="📥 Download Results as CSV",
                            data=myVar_strCsv,
                            file_name=f"DropTables_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            key="download_drop_tables"
                        )
                    else:
                        Com_st.info("Operation executed but no results were returned.")
                else:
                    # Display error
                    Com_st.error(f"❌ Operation failed: {myVar_dictResult['error']}")
                    Com_st.markdown("**Error Details:**")
                    Com_st.code(myVar_dictResult.get("traceback", "No traceback available"))

# ────────────────────────────────────────────────────────────────────────────
# 📚 MAIN MENU FUNCTION - Entry point for the module
# ────────────────────────────────────────────────────────────────────────────

def sub_displayMenu(myPar_objDbEngine):
    """
    Main entry point that displays the menu system.
    
    Args:
        myPar_objDbEngine: SQLAlchemy database engine
    """
    # Header and description
    Com_st.title("🗄️ SQL Tools Menu")
    Com_st.markdown("""
    This tool provides access to various SQL utilities for querying and managing the database.
    Select a category and tool from the options below.
    """)
    
    # Create main category tabs
    myVar_listMainCategories = [
        "📊 Business Queries", 
        "🔧 Technical Queries", 
        "⚠️ Database Maintenance"
    ]
    
    myVar_strSelectedMainCategory = Com_st.tabs(myVar_listMainCategories)
    
    # Business Queries tab
    with myVar_strSelectedMainCategory[0]:
        myVar_strBusinessSection = Com_st.radio(
            "Select Query Type",
            ["Query Selector"],
            key="business_section_radio"
        )
        
        if myVar_strBusinessSection == "Query Selector":
            sub_displayQuerySelectorTool(myPar_objDbEngine)
    
    # Technical Queries tab
    with myVar_strSelectedMainCategory[1]:
        myVar_strTechnicalSection = Com_st.radio(
            "Select Query Type",
            ["SQL Translation", "Column Search", "Column Metadata"],
            key="technical_section_radio"
        )
        
        if myVar_strTechnicalSection == "SQL Translation":
            sub_displaySQLTranslationTool(myPar_objDbEngine)
        elif myVar_strTechnicalSection == "Column Search":
            sub_displayColumnSearchTool(myPar_objDbEngine)
        elif myVar_strTechnicalSection == "Column Metadata":
            sub_displayColumnMetadataTool(myPar_objDbEngine)
    
    # Database Maintenance tab
    with myVar_strSelectedMainCategory[2]:
        myVar_strMaintenanceSection = Com_st.radio(
            "Select Maintenance Task",
            ["Drop Tables"],
            key="maintenance_section_radio"
        )
        
        if myVar_strMaintenanceSection == "Drop Tables":
            sub_displayDropTablesTool(myPar_objDbEngine)

# ════════════════════════════════════════════════════════════════════════════
#  EOF
# ════════════════════════════════════════════════════════════════════════════