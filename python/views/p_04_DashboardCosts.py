# ============================================================================
# 📦 IMPORTS
# ============================================================================
# Description: Import necessary libraries for the application.
# - streamlit (Com_st): For building the web interface.
# - pandas (Com_pd): For data manipulation and analysis.
# - sqlalchemy (create_engine): For database connection.
# - matplotlib.pyplot (Com_plt): For plotting (though less used here).
# - plotly.express (Com_px): For creating interactive plots easily.
# - plotly.graph_objects (Com_go): For more complex/custom interactive plots.
# - traceback: For detailed error logging.
# ----------------------------------------------------------------------------
import streamlit as Com_st
import pandas as Com_pd
from sqlalchemy import create_engine
import matplotlib.pyplot as Com_plt # Kept import even if not heavily used
import plotly.express as Com_px
import plotly.graph_objects as Com_go
import traceback # Added for better error display
from sqlalchemy import text

# ============================================================================
# 📜 CONSTANTS
# ============================================================================
# Description: Define constant values used throughout the script.
# - myCon_strDbServer: Database server address.
# - myCon_strDbDatabase: Database name.
# - myCon_strDbUsername: Database username.
# - myCon_strDbPassword: Database password (Consider using Streamlit secrets).
# ----------------------------------------------------------------------------

# ---------- Database connection parameters ----------
myCon_strDbServer = "database-3.c67ymu6q22o1.us-east-1.rds.amazonaws.com"
myCon_strDbDatabase = "SigmaTB"
myCon_strDbUsername = "admin"
# !! Warning: Hardcoding passwords is insecure. Use st.secrets for production. !!
myCon_strDbPassword = "Er1c41234$"

# ==============================================================================================================================================
# 🧱 FUNCTIONS & SUBPROCEDURES
# ==============================================================================================================================================
# Description: Define reusable functions for database connection, data fetching,
#              and UI display logic for various reports.
# ----------------------------------------------------------------------------

# Note before the function:
# This function establishes a connection to the MSSQL database using SQLAlchemy
# and pymssql based on the predefined constants. It returns the engine object.
def fun_connectToDb(myPar_strUser, myPar_strPassword, myPar_strServer, myPar_strDatabase):
    """
    Creates and returns a SQLAlchemy database engine object.

    Description:
        Uses the provided credentials and server information to create a
        database engine connecting to a Microsoft SQL Server database via
        the pymssql driver. Includes basic error handling for connection issues.

    Variables Used:
        - myPar_strUser (str): Database username.
        - myPar_strPassword (str): Database password.
        - myPar_strServer (str): Database server address.
        - myPar_strDatabase (str): Database name.

    Variables Returned:
        - myVar_objDbEngine (SQLAlchemy Engine): The created engine object, or None if connection fails.
    """
    # --- Local Variables ---
    # myVar_strConnectionString: The formatted connection string.
    # myVar_objDbEngine: The SQLAlchemy engine object.
    # myVar_objException: Stores caught exception object.

    try:
        # Construct the connection string
        myVar_strConnectionString = f"mssql+pytds://{myPar_strUser}:{myPar_strPassword}@{myPar_strServer}:1433/{myPar_strDatabase}"

        # Create the engine
        myVar_objDbEngine = create_engine(myVar_strConnectionString)
        # Test connection briefly to ensure it works
        with myVar_objDbEngine.connect() as myVar_objDbConnectionTest:
            pass # Connection successful if no exception
        # Return the created engine
        return myVar_objDbEngine
    except Exception as myVar_objException:
        # --- Error Handling ---
        # Log error if engine creation fails
        Com_st.error(f"❌ Database Connection Error: Failed to create engine.")
        Com_st.error(f"Error details: {myVar_objException}")
        # Return None to indicate failure
        return None

#********************************************************************************************************************************************************
#-- COST BY ORDER - ARCUST, OEDETAIL
#********************************************************************************************************************************************************
# Note before the subprocedure:
# Fetches and displays cost details for a specific order number entered by the user.
# Handles database query execution and displays results or errors.
def sub_displayCostByOrder(myPar_objDbEngine):
    """
    Displays UI elements to get an order number and shows the cost report for it.

    Description:
        Creates a text input for the order number and a button. When the button
        is clicked, it constructs and executes a SQL query to fetch cost details
        (joining ARCUST, OEOPNORD, OEDETAIL, SALESMAN, SLSDSCOV) for that order.
        Displays the results in a Streamlit DataFrame or shows warnings/errors.

    Variables Used:
        - myPar_objDbEngine (SQLAlchemy Engine): Database engine for connection.

    Variables Returned:
        - None (Displays UI directly).
    """
    # --- Local Variables ---
    # myVar_strOrderNumber: Holds the order number input by the user.
    # myVar_strSqlQuery: The SQL query string for fetching cost data.
    # myVar_objDbConnection: Active database connection.
    # myVar_pdDataFrameResult: DataFrame holding the query results.
    # myVar_objException: Stores caught exception object.

    # Input field for order number
    myVar_strOrderNumber = Com_st.text_input("Enter Order Number", value="965943", key="cost_order_input")

    # --- Button Click Logic ---
    # Control block: Executes the report logic if the button is clicked.
    if Com_st.button(f"Run Cost Report for Order {myVar_strOrderNumber}", key="cost_report_button"):
        # Control block: Validates that an order number was entered.
        if myVar_strOrderNumber:
            # Construct the SQL query
            # !! Warning: Using f-string directly with user input can lead to SQL injection.
            #    Use parameterized queries in production environments.
            myVar_strSqlQuery = f"""
                SELECT
                    OEDETAIL.ODDIST * 1000000 + OEDETAIL.ODORDR AS OrderID,
                    SALESMAN.SMNAME AS SalesmanName,
                    OEOPNORD.OOTYPE AS OrderType,
                    OEOPNORD.OOCDIS * 100000 + OEOPNORD.OOCUST AS DistributorCustomer,
                    ARCUST.CALPHA AS CustomerName,
                    OEOPNORD.OOICC * 1000000 + OEOPNORD.OOIYY * 10000 + OEOPNORD.OOIMM * 100 + OEOPNORD.OOIDD AS OrderDateKey,
                    OEDETAIL.ODITEM, OEDETAIL.ODSIZ1, OEDETAIL.ODSIZ2, OEDETAIL.ODSIZ3, OEDETAIL.ODCRTD AS [Size],
                    SLSDSCOV.DXDSC2 AS [Specification], OEDETAIL.ODTFTS AS Feet, OEDETAIL.ODTLBS AS Pounds,
                    OEDETAIL.ODTPCS AS Pieces, OEDETAIL.ODSLSX AS TotalSales, OEDETAIL.ODFRTS AS FreightCharges,
                    OEDETAIL.ODCSTX AS MaterialCost, OEDETAIL.ODPRCC AS UNKNOWNPrice, OEDETAIL.ODADCC AS AdditionalCharges,
                    OEDETAIL.ODWCCS AS WeightCost, ARCUST.CSTAT AS CustomerState, ARCUST.CCTRY AS CustomerCountry
                FROM ARCUST
                INNER JOIN OEOPNORD ON OEOPNORD.OOCDIS = ARCUST.CDIST AND OEOPNORD.OOCUST = ARCUST.CCUST
                INNER JOIN SALESMAN ON OEOPNORD.OOISMD = SALESMAN.SMDIST AND OEOPNORD.OOISMN = SALESMAN.SMSMAN
                INNER JOIN OEDETAIL ON OEDETAIL.ODDIST = OEOPNORD.OODIST AND OEDETAIL.ODORDR = OEOPNORD.OOORDR
                INNER JOIN SLSDSCOV ON OEDETAIL.ODDIST = SLSDSCOV.DXDIST AND OEDETAIL.ODORDR = SLSDSCOV.DXORDR AND OEDETAIL.ODMLIN = SLSDSCOV.DXMLIN
                WHERE OEDETAIL.ODORDR = {myVar_strOrderNumber} -- Potential SQL injection risk here
                """
            # --- Database Query Execution ---
            # Control block: try...except handles errors during database interaction.
            try:
                # Control block: 'with' ensures connection is closed.
                with myPar_objDbEngine.begin() as myVar_objDbConnection:
                    # Execute query and load results
                    myVar_pdDataFrameResult = Com_pd.read_sql(myVar_strSqlQuery, myVar_objDbConnection)

                # --- Display Results ---
                # Control block: 'if' checks if the result DataFrame is empty.
                if myVar_pdDataFrameResult.empty:
                   Com_st.warning("⚠️ No results found for this order number.")
                else:
                   Com_st.success("✅ Cost data loaded successfully.")
                   # Display the resulting data
                   Com_st.dataframe(myVar_pdDataFrameResult)

            except Exception as myVar_objException:
               # --- Error Handling ---
               Com_st.error(f"❌ Error retrieving cost data: {myVar_objException}")
               Com_st.code(traceback.format_exc())

        else:
            # Handle case where no order number was entered
            Com_st.warning("Please enter an Order Number.")

#********************************************************************************************************************************************************
#-- SHIPMENT QUERY BY ORDER
#********************************************************************************************************************************************************
# Note before the subprocedure:
# Fetches and displays shipment details for a specific order number.
# Formats the output if only one record is found, otherwise displays a table.
def sub_displayShipmentByOrder(myPar_objDbEngine):
    """
    Displays UI elements to get an order number and shows shipment details.

    Description:
        Creates a text input for the order number and a button. When clicked,
        queries the SHIPMAST table for the specified order. If a single record
        is found, it displays the fields in a multi-column layout. If multiple
        records are found, displays them in a DataFrame. Handles errors.

    Variables Used:
        - myPar_objDbEngine (SQLAlchemy Engine): Database engine for connection.

    Variables Returned:
        - None (Displays UI directly).
    """
    # --- Local Variables ---
    # myVar_strOrderNumberShip: Holds the order number input by the user.
    # myVar_strSqlQuery: The SQL query string for fetching shipment data.
    # myVar_objDbConnection: Active database connection.
    # myVar_pdDataFrameResult: DataFrame holding the query results.
    # myVar_dictRecord: Dictionary representing a single shipment record.
    # myVar_listKeys: List of keys (column names) from the record.
    # myVar_intIndex: Outer loop counter for column layout.
    # myVar_intInnerIndex: Inner loop counter for column layout.
    # myVar_strKey: Current key (column name) being processed.
    # myVar_listColsLayout: List of Streamlit columns for layout.
    # myVar_objException: Stores caught exception object.

    # Input field for order number
    myVar_strOrderNumberShip = Com_st.text_input(
        "Enter Order Number for Shipment Details",
        value="965943",
        key="shipping_order_input"
    )

    # --- Button Click Logic ---
    # Control block: Executes the report logic if the button is clicked.
    if Com_st.button(f"Run Shipment Report for Order {myVar_strOrderNumberShip}", key="shipment_report_button"):
        # Control block: Validates that an order number was entered.
        if myVar_strOrderNumberShip:
            # --- Database Query Execution ---
            # Control block: try...except handles errors during database interaction.
            try:
                # Construct the SQL query
                # !! Warning: Potential SQL injection risk with f-string. Use parameterization.
                myVar_strSqlQuery = f"""
                    SELECT S.SHDIST as "District Number", S.SHORDN as "Sales Order", S.SHCORD as "Customer Order", S.SHITEM as "Item",
                           S.SHIPCC as "Shipment Century", S.SHIPYY, S.SHIPMM, S.SHIPDD, S.SHBQTY as "Base quantity", S.SHTLBS,
                           S.SHCUST as "Customer number", S.SHORYY as "Original order year", S.SHORMM, S.SHORDD, S.SHIVYY as "Invoice year",
                           S.SHIVMM, S.SHIVDD, S.SHMSLS as "Material sales", S.SHMSLD as "Final sales", S.SHFSLS as "Final issued sales",
                           S.SHMCSS as "Material cost", S.SHSLSS as "Sales ledger", S.SHSWGS as "swaged sales", S.SHADPC as "additional processing",
                           S.SHFRGH as "freight cost", S.SHTRCK as "truck route", S.SHSHTO as "customer ship to", S.SHBCTY as "Bill to country",
                           S.SHSCTY as "Ship to country", S.SHTMPS as "temp ship to", S.SHDSTO as "Orig cust dist", S.SHCSTO as "Orig cust",
                           S.SHSMDO as "Orig sism dist", S.SHSLMO as "Orig Slsmn", S.SHICMP as "Inv comp", S.SHADR1 as "Address 1",
                           S.SHADR2, S.SHADR3, S.SHCITY as "City 25 pos", S.SHSTAT as "State", S.SHZIP as "Zip"
                    FROM [dbo].[SHIPMAST] S WHERE S.SHORDN = {myVar_strOrderNumberShip}
                """
                # Control block: 'with' ensures connection is closed.
                with myPar_objDbEngine.begin() as myVar_objDbConnection:
                    # Execute query and load results
                    myVar_pdDataFrameResult = Com_pd.read_sql(myVar_strSqlQuery, myVar_objDbConnection)

                # --- Display Results ---
                # Control block: 'if' checks if the result DataFrame is empty.
                if myVar_pdDataFrameResult.empty:
                    Com_st.warning("⚠️ No shipment results found for this order number.")
                else:
                    Com_st.success("✅ Shipment data loaded successfully.")
                    # Control block: 'with' creates an expandable section for details.
                    with Com_st.expander("📦 View Shipment Details", expanded=True):
                        # Control block: 'if' checks if exactly one record was returned.
                        if len(myVar_pdDataFrameResult) == 1:
                            # Format single record display
                            myVar_dictRecord = myVar_pdDataFrameResult.iloc[0].to_dict()
                            myVar_listKeys = list(myVar_dictRecord.keys())
                            # Control block: Outer loop iterates through keys in steps of 5 for layout.
                            for myVar_intIndex in range(0, len(myVar_listKeys), 5):
                                # Create 5 columns for layout
                                myVar_listColsLayout = Com_st.columns(5)
                                # Control block: Inner loop iterates through keys for the current row of columns.
                                for myVar_intInnerIndex, myVar_strKey in enumerate(myVar_listKeys[myVar_intIndex:myVar_intIndex+5]):
                                    # Control block: 'with' places content in the correct column.
                                    with myVar_listColsLayout[myVar_intInnerIndex]:
                                        Com_st.markdown(f"**{myVar_strKey}**") # Display key/column name
                                        Com_st.text(myVar_dictRecord[myVar_strKey]) # Display value
                        else:
                            # Display DataFrame if multiple records found
                            Com_st.dataframe(myVar_pdDataFrameResult)

            except Exception as myVar_objException:
               # --- Error Handling ---
               Com_st.error(f"❌ Error retrieving shipment data: {myVar_objException}")
               Com_st.code(traceback.format_exc())
        else:
             # Handle case where no order number was entered
             Com_st.warning("Please enter an Order Number.")

#********************************************************************************************************************************************************
#-- MATERIAL PROCESSING BY ORDER GLTRANS, GLACCT
#********************************************************************************************************************************************************
# Note before the subprocedure:
# Fetches and displays Material Processing (MP) details related to an order number
# by searching the GLTRANS and GLACCT tables based on a LIKE match in GLREF.
def sub_displayMPByOrder(myPar_objDbEngine):
    """
    Displays UI elements to get an order number and shows related GL transactions.

    Description:
        Creates a text input for the order number and a button. When clicked,
        queries the GLTRANS and GLACCT tables for transactions where the GLREF
        field contains the entered order number (using LIKE) and the account
        type (GARP3) is 500 or 600. Displays results in a DataFrame or shows errors.

    Variables Used:
        - myPar_objDbEngine (SQLAlchemy Engine): Database engine for connection.

    Variables Returned:
        - None (Displays UI directly).
    """
    # --- Local Variables ---
    # myVar_strOrderNumberMP: Holds the order number input by the user.
    # myVar_strPattern: LIKE pattern for the SQL query.
    # myVar_strSqlQuery: The SQL query string for fetching GL data.
    # myVar_objDbConnection: Active database connection.
    # myVar_pdDataFrameResult: DataFrame holding the query results.
    # myVar_objException: Stores caught exception object.

    # Input field for order number
    myVar_strOrderNumberMP = Com_st.text_input("Enter Order Number for MP Details", value="965943", key="MP_order_input")
    Com_st.caption(f"Note: This searches for GL Reference LIKE '%{myVar_strOrderNumberMP}%'") # Clarify search method

    # --- Button Click Logic ---
    # Control block: Executes the report logic if the button is clicked.
    if Com_st.button(f"Run MP Report for Order {myVar_strOrderNumberMP}", key="mp_report_button"):
         # Control block: Validates that an order number was entered.
        if myVar_strOrderNumberMP:
            # --- Database Query Execution ---
            # Control block: try...except handles errors during database interaction.
            try:
                # Construct the SQL query using LIKE with escaped %
                # Using parameters is highly recommended for security. Example (SQLAlchemy):
                # from sqlalchemy import text
                # query = text("""SELECT ... WHERE GLREF LIKE :pattern AND GLA.GARP3 IN (500,600) ...""")
                # df = pd.read_sql(query, conn, params={"pattern": f"%{order_number_MP}%"})
                # For now, sticking to f-string with basic escaping for LIKE as requested.
                myVar_strPattern = f"%{myVar_strOrderNumberMP}%" # Define pattern separately
                # Escape single quotes within the pattern itself for safety in f-string
                myVar_strEscapedPattern = myVar_strPattern.replace("'", "''")
                myVar_strSqlQuery = text("""
                    SELECT GLDESC AS Title_GLDESC, GLAMT, GLA.GARP3 as GARP3_FS, GLAPPL AS GLAPPL_APP,
                        GLA.GACDES AS GACDES_AccountDescription, FORMAT(GLCOMP, '00') + ' ' + FORMAT(GLDIST, '00') + ' ' + FORMAT(GLCSTC, '00') AS [CO DS CS],
                        GLT.GLACCT AS GLAccount_GLACCT, GLREF AS GLREF_Reference, GLAPPL + RIGHT('00000000' + CAST(GLBTCH AS VARCHAR), 8) + '-0001' AS Reference,
                        FORMAT(GLPPYY, '00') + ' ' + FORMAT(GLPERD, '00') AS Period, GLDESC AS Transaction_GLDESC, GLPGM AS GLPGM_Prgm,
                        GLUSER AS GLUSER, GLAPTR AS GLAPTR_Related, GLTRN# AS [GLTRN#], GLTRNT AS [GLTRNT_Tran],
                        GLTYPE AS GLTYPE, GLDIST AS GLDIST, GLREF AS GLREF_Document, GLCRDB, GLT.GLACCT AS GLACCT_FS,
                        GLRECD AS Ext, TRY_CAST(CAST(GLRFYY AS VARCHAR(4)) + '-' + RIGHT('00' + CAST(GLRFMM AS VARCHAR(2)), 2) + '-' + RIGHT('00' + CAST(GLRFDD AS VARCHAR(2)), 2) AS DATE) AS Posting,
                        NULL AS System, FORMAT(GLCUST, '00 00000') AS Custmr
                    FROM GLTRANS GLT
                    LEFT JOIN GLACCT GLA ON GLT.GLACCT = GLA.GACCT
                    WHERE GLREF LIKE :pattern
                    AND GLA.GARP3 IN (500,600)
                    GROUP BY GLRECD, GLCOMP, GLDIST, GLCSTC, GLT.GLACCT, GLDESC, GLPPYY, GLPERD, GLAPPL, GLBTCH, GLPGM,
                            GLUSER, GLAPTR, GLTRN#, GLTRNT, GLTYPE, GLREF, GLRFYY, GLRFMM, GLRFDD, GLCUST, GLCRDB, GLAMT,
                            GLA.GACDES, GLA.GARP3
                    ORDER BY GLTRN#
                """)

                # Control block: 'with' ensures connection is closed.
                with myPar_objDbEngine.begin() as myVar_objDbConnection:
                    # Execute query and load results
                    myVar_pdDataFrameResult = Com_pd.read_sql(myVar_strSqlQuery, myVar_objDbConnection, params={'pattern': myVar_strPattern})

                # --- Display Results ---
                # Control block: 'if' checks if the result DataFrame is empty.
                if myVar_pdDataFrameResult.empty:
                   Com_st.warning("⚠️ No MP results found matching this order number reference.")
                else:
                   Com_st.success("✅ MP data loaded successfully.")
                   # Display the resulting data
                   Com_st.dataframe(myVar_pdDataFrameResult)

            except Exception as myVar_objException:
               # --- Error Handling ---
               Com_st.error(f"❌ Error retrieving MP data: {myVar_objException}")
               Com_st.code(traceback.format_exc())
        else:
             # Handle case where no order number was entered
             Com_st.warning("Please enter an Order Number.")

###############################################################
# CREDIT MEMOS Where are the 25k of credits on the income statement
###############################################################
# Note before the subprocedure:
# Analyzes credit memos from GLTRANS for February Year 25, showing totals
# by customer and displaying a pie chart of the credit distribution.
def sub_displayCreditMemos(myPar_objDbEngine):
    """
    Runs a report to analyze credit memos for a specific period (Feb, Year 25).

    Description:
        Executes a query aggregating credit memo amounts (GLAPPL='CR') from
        GLTRANS for Feb/Yr25, grouped by customer. It also joins to get total sales
        for ratio calculation. Displays the aggregated data in a DataFrame and
        shows a Plotly pie chart visualizing the credit distribution by customer.

    Variables Used:
        - myPar_objDbEngine (SQLAlchemy Engine): Database engine for connection.

    Variables Returned:
        - None (Displays UI directly).
    """
    # --- Local Variables ---
    # myVar_strSqlQuery: The SQL query string for fetching credit memo data.
    # myVar_objDbConnection: Active database connection.
    # myVar_pdDataFrameResult: DataFrame holding the query results.
    # myVar_pxFigure: Plotly Express pie chart object.
    # myVar_objException: Stores caught exception object.

    # --- Button Click Logic ---
    # Control block: Executes the report logic if the button is clicked.
    if Com_st.button("Run Credit Memos Report (Feb Yr 25)", key="credit_memo_button"):
        # Define the SQL query for credit memo analysis
        myVar_strSqlQuery = """
            SELECT
                ARCUST.CALPHA AS CustomerName, COUNT(DISTINCT GLT.GLTRN#) AS CreditOrderCount,
                SUM(GLT.GLAMT) AS TotalCredits, ISNULL(Sales.TotalSales, 0) AS TotalSales,
                CASE WHEN ISNULL(Sales.TotalSales, 0) = 0 THEN NULL ELSE ROUND(SUM(GLT.GLAMT) * 1.0 / Sales.TotalSales, 2) END AS CreditRatio
            FROM GLTRANS GLT
            LEFT JOIN GLACCT GLA ON GLT.GLACCT = GLA.GACCT
            LEFT JOIN ARCUST ON GLT.GLCUST = ARCUST.CCUST
            LEFT JOIN (
                SELECT GLCUST, SUM(GLAMT) AS TotalSales FROM GLTRANS
                LEFT JOIN GLACCT ON GLTRANS.GLACCT = GLACCT.GACCT
                WHERE GLAPPL IN ('IN') AND GARP3 BETWEEN 500 AND 599 AND GLPYY = 25 AND GLPMM = 2
                GROUP BY GLCUST
            ) AS Sales ON GLT.GLCUST = Sales.GLCUST
            WHERE GLT.GLAPPL IN ('CR') AND GLA.GARP3 IN (500, 600) AND GLT.GLPYY = 25 AND GLT.GLPMM = 2
            GROUP BY ARCUST.CALPHA, Sales.TotalSales ORDER BY TotalCredits DESC;
        """
        # --- Database Query Execution ---
        # Control block: try...except handles errors during database interaction.
        try:
            # Control block: 'with' ensures connection is closed.
            with myPar_objDbEngine.begin() as myVar_objDbConnection:
                # Execute query and load results
                myVar_pdDataFrameResult = Com_pd.read_sql(myVar_strSqlQuery, myVar_objDbConnection)

            # --- Display Results ---
            # Control block: 'if' checks if the result DataFrame is empty.
            if myVar_pdDataFrameResult.empty:
               Com_st.warning("⚠️ No credit memo results found for this period.")
            else:
               Com_st.success("✅ February credit memo data loaded successfully.")
               # Display the aggregated data
               Com_st.dataframe(myVar_pdDataFrameResult)

               # --- Generate Pie Chart ---
               # Control block: 'if' checks if necessary columns exist for the chart.
               if "CustomerName" in myVar_pdDataFrameResult.columns and "TotalCredits" in myVar_pdDataFrameResult.columns:
                    Com_st.subheader("💰 Interactive Credit Distribution by Customer")
                    # Create the pie chart using Plotly Express
                    myVar_pxFigure = Com_px.pie(
                        myVar_pdDataFrameResult,
                        names="CustomerName", values="TotalCredits",
                        title="Credit % by Customer (Feb Yr 25)",
                        hole=0.3 # Donut chart style
                    )
                    # Update chart traces for better labels and hover info
                    myVar_pxFigure.update_traces(textinfo='percent+label', hovertemplate='%{label}: $%{value:,.2f}')
                    # Display the chart
                    Com_st.plotly_chart(myVar_pxFigure, use_container_width=True)
               else:
                    # Handle missing columns for chart generation
                    Com_st.info("Pie chart could not be generated: missing 'CustomerName' or 'TotalCredits' columns.")

        except Exception as myVar_objException:
           # --- Error Handling ---
           Com_st.error(f"❌ Error retrieving credit memo data: {myVar_objException}")
           Com_st.code(traceback.format_exc())

###############################################################
# $380K LOST - WHERE ARE THE $380K COSTS
###############################################################
# Note before the subprocedure:
# Investigates costs recorded in GLTRANS with GLTRN# = 0 for February Year 25,
# potentially indicating costs not tied to specific transactions. Displays
# results and pie charts by vendor description and cost category.
def sub_displayUntransactionedCosts(myPar_objDbEngine):
    """
    Runs a report to find costs potentially not linked to transactions (GLTRN#=0).

    Description:
        Executes a query on GLTRANS/GLACCT for Feb/Yr25 targeting accounts in
        ranges 500-530 and 600-610 where GLTRN# is 0 and description length is not 6.
        It aggregates amounts, adjusting for credit/debit. Displays the raw results
        and then generates two Plotly pie charts: one showing costs by vendor
        (using GLDESC) and another by cost category (GACDES).

    Variables Used:
        - myPar_objDbEngine (SQLAlchemy Engine): Database engine for connection.

    Variables Returned:
        - None (Displays UI directly).
    """
    # --- Local Variables ---
    # myVar_strSqlQuery: The SQL query string.
    # myVar_objDbConnection: Active database connection.
    # myVar_pdDataFrameRaw: DataFrame holding the initial query results.
    # myVar_pdDataFramePie: Filtered DataFrame for pie charts (negative amounts).
    # myVar_pxFigureVendor: Plotly pie chart for costs by vendor.
    # myVar_pxFigureCategory: Plotly pie chart for costs by category.
    # myVar_objException: Stores caught exception object.

    # --- Button Click Logic ---
    # Control block: Executes the report logic if the button is clicked.
    if Com_st.button("Run Untransactioned Costs Report (Feb Yr 25)", key="untransactioned_cost_button"):
        # Define the SQL query
        myVar_strSqlQuery = """
            SELECT LTRIM(RTRIM(GLT.GLDESC)) AS GLDESC, GLA.GACDES, SUM(CASE WHEN GLCRDB = 'C' THEN +GLAMT WHEN GLCRDB = 'D' THEN -GLAMT ELSE 0 END) AS AdjustedAmount
            FROM GLTRANS GLT LEFT JOIN GLACCT GLA ON GLT.GLACCT = GLA.GACCT
            WHERE GLA.GARP3 IN (500, 530, 600, 610) AND GLT.[GLTRN#] = 0 AND GLT.GLPYY = 25 AND GLT.GLPMM = 2 AND LEN(LTRIM(RTRIM(GLT.GLDESC))) <> 6
            GROUP BY LTRIM(RTRIM(GLT.GLDESC)), GLA.GACDES;
        """
        # --- Database Query Execution ---
        # Control block: try...except handles errors during database interaction.
        try:
            # Control block: 'with' ensures connection is closed.
            with myPar_objDbEngine.begin() as myVar_objDbConnection:
                # Execute query and load results
                myVar_pdDataFrameRaw = Com_pd.read_sql(myVar_strSqlQuery, myVar_objDbConnection)

            # --- Display Results ---
            # Control block: 'if' checks if the result DataFrame is empty.
            if myVar_pdDataFrameRaw.empty:
                Com_st.warning("⚠️ No untransactioned cost results found for this period.")
                # Exit the subprocedure if no data
                return

            Com_st.success("✅ Untransactioned cost data loaded successfully.")
            # Display the raw aggregated data
            Com_st.dataframe(myVar_pdDataFrameRaw)

            # --- Prepare Data for Charts ---
            # Filter for cost entries (negative AdjustedAmount) and make values positive for chart
            myVar_pdDataFramePie = myVar_pdDataFrameRaw[myVar_pdDataFrameRaw["AdjustedAmount"] < 0].copy()
            # Control block: 'if' checks if there's data to plot after filtering.
            if not myVar_pdDataFramePie.empty:
                 myVar_pdDataFramePie.loc[:, "AdjustedAmount"] = myVar_pdDataFramePie["AdjustedAmount"].abs()
            else:
                 Com_st.warning("⚠️ No cost-related values (negative adjusted amounts) found to chart.")
                 # Exit the subprocedure if no cost data
                 return # Stop further execution in this function call

            # --- Generate Pie Charts ---
            # Chart 1: Costs by Vendor Description
            Com_st.subheader("📊 Costs by Vendor Description (GLDESC)")
            myVar_pxFigureVendor = Com_px.pie(
                myVar_pdDataFramePie, names="GLDESC", values="AdjustedAmount",
                title="Costs by Vendor Description", hole=0.3
            )
            myVar_pxFigureVendor.update_traces(textinfo='percent+label', hovertemplate='%{label}: $%{value:,.2f}')
            Com_st.plotly_chart(myVar_pxFigureVendor, use_container_width=True)

            # Chart 2: Costs by Cost Category Description
            Com_st.subheader("📊 Costs by Cost Category (GACDES)")
            myVar_pxFigureCategory = Com_px.pie(
                myVar_pdDataFramePie, names="GACDES", values="AdjustedAmount",
                title="Costs by Category Description", hole=0.3
            )
            myVar_pxFigureCategory.update_traces(textinfo='percent+label', hovertemplate='%{label}: $%{value:,.2f}')
            Com_st.plotly_chart(myVar_pxFigureCategory, use_container_width=True)

        except Exception as myVar_objException:
           # --- Error Handling ---
           Com_st.error(f"❌ Error retrieving untransactioned cost data: {myVar_objException}")
           Com_st.code(traceback.format_exc())

###############################################################
# SALES REPORT FROM OEDETAIL AND OEOPNORD
###############################################################
# Note before the subprocedure:
# Generates a sales report summarizing totals by customer and salesman for
# February Year 25 using OE tables. Displays the aggregated data and a
# company-wide waterfall chart showing the breakdown from sales to gross profit.
def sub_displaySalesReportFromOE(myPar_objDbEngine):
    """
    Runs a sales report based on OE tables for a specific period (Feb, Year 25).

    Description:
        Executes a query joining ARCUST, OEOPNORD, SALESMAN, OEDETAIL, SLSDSCOV
        to aggregate sales, freight, costs, etc., grouped by customer and salesman
        for Feb/Yr25. Displays the aggregated results in a DataFrame. Calculates
        company-wide totals and displays a Plotly Waterfall chart visualizing
        the breakdown from total sales to gross profit.

    Variables Used:
        - myPar_objDbEngine (SQLAlchemy Engine): Database engine for connection.

    Variables Returned:
        - None (Displays UI directly).
    """
    # --- Local Variables ---
    # myVar_strSqlQuery: The SQL query string.
    # myVar_objDbConnection: Active database connection.
    # myVar_pdDataFrameResult: DataFrame holding the aggregated sales results.
    # myVar_pdSeriesTotals: Series holding the sum of numeric columns.
    # myVar_floatSales, myVar_floatFreight, ...: Float values for waterfall chart.
    # myVar_floatGrossProfit: Calculated gross profit.
    # myVar_listStrLabels: Labels for the waterfall chart axes.
    # myVar_listFloatRawValues: Raw values for waterfall chart calculation.
    # myVar_listStrTextValues: Formatted text values for display on chart.
    # myVar_goFigureWaterfall: Plotly graph object for the waterfall chart.
    # myVar_objException: Stores caught exception object.

    # --- Button Click Logic ---
    # Control block: Executes the report logic if the button is clicked.
    if Com_st.button("Run Sales Report (OE Tables - Feb Yr 25)", key="sales_report_oe_button"):
        # Define the SQL query
        myVar_strSqlQuery = """
            SELECT ARCUST.CALPHA AS CustomerName, SALESMAN.SMNAME AS SalesmanName, SUM(OEDETAIL.ODSLSX) AS TotalSales,
                   SUM(OEDETAIL.ODFRTS) AS TotalFreightCharges, SUM(OEDETAIL.ODCSTX) AS TotalMaterialCost,
                   SUM(OEDETAIL.ODPRCC) AS TotalProcessingPrice, SUM(OEDETAIL.ODADCC) AS TotalAdditionalCharges,
                   SUM(OEDETAIL.ODWCCS) AS TotalWeightCost
            FROM ARCUST INNER JOIN OEOPNORD ON OEOPNORD.OOCDIS = ARCUST.CDIST AND OEOPNORD.OOCUST = ARCUST.CCUST
            INNER JOIN SALESMAN ON OEOPNORD.OOISMD = SALESMAN.SMDIST AND OEOPNORD.OOISMN = SALESMAN.SMSMAN
            INNER JOIN OEDETAIL ON OEDETAIL.ODDIST = OEOPNORD.OODIST AND OEDETAIL.ODORDR = OEOPNORD.OOORDR
            INNER JOIN SLSDSCOV ON OEDETAIL.ODDIST = SLSDSCOV.DXDIST AND OEDETAIL.ODORDR = SLSDSCOV.DXORDR AND OEDETAIL.ODMLIN = SLSDSCOV.DXMLIN
            WHERE OEOPNORD.OOIYY = 25 AND OEOPNORD.OOIMM = 2
            GROUP BY ARCUST.CALPHA, SALESMAN.SMNAME
        """
        # --- Database Query Execution ---
        # Control block: try...except handles errors during database interaction.
        try:
            # Control block: 'with' ensures connection is closed.
            with myPar_objDbEngine.begin() as myVar_objDbConnection:
                # Execute query and load results
                myVar_pdDataFrameResult = Com_pd.read_sql(myVar_strSqlQuery, myVar_objDbConnection)

            # --- Display Results ---
            # Control block: 'if' checks if the result DataFrame is empty.
            if myVar_pdDataFrameResult.empty:
               Com_st.warning("⚠️ No sales report results found for this period.")
            else:
                Com_st.success("✅ Sales report data loaded successfully.")
                # Display aggregated data
                Com_st.dataframe(myVar_pdDataFrameResult)

                # --- Calculate Totals for Waterfall ---
                # Sum numeric columns to get company-wide totals, fill NaNs with 0
                myVar_pdSeriesTotals = myVar_pdDataFrameResult.sum(numeric_only=True).fillna(0)

                # Extract individual totals as floats
                myVar_floatSales = float(myVar_pdSeriesTotals.get("TotalSales", 0))
                myVar_floatFreight = float(myVar_pdSeriesTotals.get("TotalFreightCharges", 0))
                myVar_floatMaterial = float(myVar_pdSeriesTotals.get("TotalMaterialCost", 0))
                myVar_floatProcessing = float(myVar_pdSeriesTotals.get("TotalProcessingPrice", 0))
                myVar_floatAdditional = float(myVar_pdSeriesTotals.get("TotalAdditionalCharges", 0))
                myVar_floatWeight = float(myVar_pdSeriesTotals.get("TotalWeightCost", 0))

                # Calculate Gross Profit
                myVar_floatGrossProfit = (myVar_floatSales - myVar_floatFreight - myVar_floatMaterial -
                                          myVar_floatProcessing - myVar_floatAdditional - myVar_floatWeight)

                # --- Generate Waterfall Chart ---
                Com_st.subheader("📊 Company-Wide Sales Waterfall (From OE Report)")

                # Define labels and values for the chart
                myVar_listStrLabels = ["Sales", "Freight", "Material", "Processing", "Additional", "Weight", "Gross Profit"]
                myVar_listFloatRawValues = [ # Store raw values for calculations and hover
                    myVar_floatSales, -myVar_floatFreight, -myVar_floatMaterial,
                    -myVar_floatProcessing, -myVar_floatAdditional, -myVar_floatWeight,
                    myVar_floatGrossProfit
                ]
                # Create text labels scaled to millions
                myVar_listStrTextValues = [f"${v / 1_000_000:.2f}M" for v in myVar_listFloatRawValues]

                # Create the waterfall figure
                myVar_goFigureWaterfall = Com_go.Figure(Com_go.Waterfall(
                    name="OE Total", orientation="v",
                    measure=["relative", "relative", "relative", "relative", "relative", "relative", "total"], # GP is total
                    x=myVar_listStrLabels,
                    y=myVar_listFloatRawValues[:-1], # Provide values excluding the final total for measure='total'
                    textposition="outside",
                    text=myVar_listStrTextValues,
                     # Use customdata to store raw values for hover
                    customdata=myVar_listFloatRawValues,
                    hovertemplate='%{x}: $%{customdata:,.2f}<extra></extra>' # Format hover
                ))
                # Update layout
                myVar_goFigureWaterfall.update_layout(
                    title="💰 Net Sales Breakdown (in Millions)",
                    waterfallgap=0.3,
                    yaxis_title="Amount ($M)"
                )
                # Display chart
                Com_st.plotly_chart(myVar_goFigureWaterfall, use_container_width=True)

        except Exception as myVar_objException:
           # --- Error Handling ---
           Com_st.error(f"❌ Error retrieving OE sales report data: {myVar_objException}")
           Com_st.code(traceback.format_exc())

# Note before the function:
# Safely extracts a summed amount for a specific GARP3 code from the GL summary DataFrame.
def fun_safeGetGlAmount(myPar_pdDataFrameGl, myPar_intGarpCode):
    """
    Safely extracts the 'AdjustedAmount' for a given GARP3 code from a DataFrame.

    Description:
        Filters the input DataFrame for rows matching the specified GARP3 code.
        If a matching row is found, extracts the 'AdjustedAmount' value.
        Returns the float value or 0.0 if no match is found or the value is invalid.

    Variables Used:
        - myPar_pdDataFrameGl (pandas.DataFrame): DataFrame containing summarized GL data with 'GARP3' and 'AdjustedAmount' columns.
        - myPar_intGarpCode (int): The GARP3 code to filter by.

    Variables Returned:
        - myVar_floatAmount (float): The extracted amount or 0.0.
    """
    # --- Local Variables ---
    # myVar_pdSeriesRow: Pandas Series representing the filtered row(s).
    # myVar_floatAmount: The extracted float amount.

    # Filter DataFrame for the specified GARP3 code
    myVar_pdSeriesRow = myPar_pdDataFrameGl.loc[myPar_pdDataFrameGl["GARP3"] == myPar_intGarpCode, "AdjustedAmount"]
    # --- Value Extraction ---
    # Control block: 'if' checks if any matching row was found.
    if not myVar_pdSeriesRow.empty:
        try:
            # Attempt to get the first value and convert to float
            myVar_floatAmount = float(myVar_pdSeriesRow.values[0])
            return myVar_floatAmount
        except (ValueError, TypeError):
             # Handle potential conversion errors
             return 0.0
    else:
        # Return 0.0 if no matching code found
        return 0.0

################################################################
# SALES REPORT COMPARING SALES DEPARTMENT TO GL
################################################################
# Note before the subprocedure:
# Compares sales and cost data derived from the OE tables against corresponding
# summary figures from the General Ledger (GL) for February Year 25.
# Displays results from both sources and corresponding charts (Waterfall for OE, Bar for GL).
def sub_compareSalesVsGL(myPar_objDbEngine):
    """
    Compares Sales Report (OE) data with General Ledger (GL) summary data.

    Description:
        Executes two queries: one identical to the OE Sales Report, and another
        summarizing GL amounts by GARP3 code for relevant account types (500s/600s)
        for Feb/Yr25. Displays the OE sales data and its waterfall chart.
        Displays the GL summary data (using helper function `fun_safeGetGlAmount`)
        and a bar chart visualizing the GL breakdown. Handles errors for each part.

    Variables Used:
        - myPar_objDbEngine (SQLAlchemy Engine): Database engine for connection.

    Variables Returned:
        - None (Displays UI directly).
    """
    # --- Local Variables ---
    # myVar_strQuerySales: SQL query for OE sales data.
    # myVar_strQueryGL: SQL query for GL summary data.
    # myVar_objDbConnection: Active database connection.
    # myVar_pdDataFrameSales: DataFrame for OE sales results.
    # myVar_pdDataFrameGL: DataFrame for GL summary results.
    # myVar_pdSeriesTotalsSales: Series holding summed OE sales data.
    # myVar_listFloatSalesValues: List of values for OE waterfall chart.
    # myVar_floatGrossProfitSales: Calculated gross profit from OE data.
    # myVar_goFigureSales: Plotly waterfall chart for OE data.
    # myVar_floatSalesGL, myVar_floatReturnsGL, ...: GL amounts extracted using helper function.
    # myVar_floatTotalSalesGL: Calculated total sales from GL data.
    # myVar_floatGrossProfitGL: Calculated gross profit from GL data.
    # myVar_listStrLabelsGL: Labels for GL bar chart.
    # myVar_listFloatValuesGL: Values for GL bar chart.
    # myVar_goFigureGL: Plotly bar chart for GL data.
    # myVar_objException: Stores caught exception object.

    # --- Button Click Logic ---
    # Control block: Executes the report logic if the button is clicked.
    if Com_st.button("Run Sales vs GL Comparison Report (Feb Yr 25)", key="sales_vs_gl_button"):

        # --- Define Queries ---
        # Query 1: OE Sales Data (Same as sub_displaySalesReportFromOE)
        myVar_strQuerySales = """
            SELECT ARCUST.CALPHA AS CustomerName, SALESMAN.SMNAME AS SalesmanName, SUM(OEDETAIL.ODSLSX) AS TotalSales,
                   SUM(OEDETAIL.ODFRTS) AS TotalFreightCharges, SUM(OEDETAIL.ODCSTX) AS TotalMaterialCost,
                   SUM(OEDETAIL.ODPRCC) AS TotalProcessingPrice, SUM(OEDETAIL.ODADCC) AS TotalAdditionalCharges,
                   SUM(OEDETAIL.ODWCCS) AS TotalWeightCost
            FROM ARCUST INNER JOIN OEOPNORD ON OEOPNORD.OOCDIS = ARCUST.CDIST AND OEOPNORD.OOCUST = ARCUST.CCUST
            INNER JOIN SALESMAN ON OEOPNORD.OOISMD = SALESMAN.SMDIST AND OEOPNORD.OOISMN = SALESMAN.SMSMAN
            INNER JOIN OEDETAIL ON OEDETAIL.ODDIST = OEOPNORD.OODIST AND OEDETAIL.ODORDR = OEOPNORD.OOORDR
            INNER JOIN SLSDSCOV ON OEDETAIL.ODDIST = SLSDSCOV.DXDIST AND OEDETAIL.ODORDR = SLSDSCOV.DXORDR AND OEDETAIL.ODMLIN = SLSDSCOV.DXMLIN
            WHERE OEOPNORD.OOIYY = 25 AND OEOPNORD.OOIMM = 2
            GROUP BY ARCUST.CALPHA, SALESMAN.SMNAME
        """
        # Query 2: GL Summary Data
        myVar_strQueryGL = """
            SELECT GLA.GARP3, SUM(CASE WHEN GLCRDB = 'C' THEN +GLAMT WHEN GLCRDB = 'D' THEN -GLAMT ELSE 0 END) AS AdjustedAmount
            FROM GLTRANS GLT LEFT JOIN GLACCT GLA ON GLT.GLACCT = GLA.GACCT
            WHERE GLA.GARP3 IN (500, 530, 600, 610) AND GLT.GLPYY = 25 AND GLT.GLPMM = 2
            GROUP BY GLA.GARP3
        """
        # --- Database Query Execution ---
        # Control block: try...except handles errors during database interaction.
        try:
            # Control block: 'with' ensures connection is closed.
            with myPar_objDbEngine.begin() as myVar_objDbConnection:
                # Execute queries and load results
                myVar_pdDataFrameSales = Com_pd.read_sql(myVar_strQuerySales, myVar_objDbConnection)
                myVar_pdDataFrameGL = Com_pd.read_sql(myVar_strQueryGL, myVar_objDbConnection)

            # --- Process and Display Sales Report (OE) Data ---
            # Control block: 'if' checks if the sales DataFrame is empty.
            if not myVar_pdDataFrameSales.empty:
                Com_st.success("✅ Sales Report (OE) data loaded.")
                Com_st.dataframe(myVar_pdDataFrameSales) # Display table

                # Calculate totals and prepare for waterfall chart
                myVar_pdSeriesTotalsSales = myVar_pdDataFrameSales.sum(numeric_only=True).fillna(0)
                myVar_listFloatSalesValues = [
                    float(myVar_pdSeriesTotalsSales.get("TotalSales", 0)),
                    -float(myVar_pdSeriesTotalsSales.get("TotalFreightCharges", 0)),
                    -float(myVar_pdSeriesTotalsSales.get("TotalMaterialCost", 0)),
                    -float(myVar_pdSeriesTotalsSales.get("TotalProcessingPrice", 0)),
                    -float(myVar_pdSeriesTotalsSales.get("TotalAdditionalCharges", 0)),
                    -float(myVar_pdSeriesTotalsSales.get("TotalWeightCost", 0))
                ]
                myVar_floatGrossProfitSales = sum(myVar_listFloatSalesValues)
                myVar_listFloatWaterfallYValues = myVar_listFloatSalesValues # Values for y-axis

                # Generate and display waterfall chart
                Com_st.subheader("📊 Sales Report (OE) - Waterfall Breakdown")
                myVar_goFigureSales = Com_go.Figure(Com_go.Waterfall(
                    name="OE Total", orientation="v",
                    measure=["relative"] * 6 + ["total"],
                    x=["Sales", "Freight", "Material", "Processing", "Additional", "Weight", "Gross Profit"],
                    y=myVar_listFloatWaterfallYValues, # Let Plotly calculate total for 'total' measure
                    text=[f"${v / 1_000_000:.2f}M" for v in myVar_listFloatWaterfallYValues + [myVar_floatGrossProfitSales]],
                    customdata=myVar_listFloatWaterfallYValues + [myVar_floatGrossProfitSales], # Add GP for hover
                    hovertemplate='%{x}: $%{customdata:,.2f}<extra></extra>',
                    textposition="outside"
                ))
                myVar_goFigureSales.update_layout(title="Sales Report (OE) Breakdown", yaxis_title="Amount ($)")
                Com_st.plotly_chart(myVar_goFigureSales, use_container_width=True)
                Com_st.metric("Gross Profit (from OE Report)", f"${myVar_floatGrossProfitSales:,.2f}")
                Com_st.markdown("---") # Separator
            else:
                Com_st.warning("⚠️ No data found in Sales Report (OE) for this period.")
                Com_st.markdown("---") # Separator

            # --- Process and Display General Ledger (GL) Data ---
            # Control block: 'if' checks if the GL DataFrame is empty.
            if not myVar_pdDataFrameGL.empty:
                Com_st.success("✅ General Ledger (GL) summary loaded.")
                # Optional: Display raw GL summary table
                # Com_st.dataframe(myVar_pdDataFrameGL)

                # Extract specific GL amounts using helper function
                myVar_floatSalesGL = fun_safeGetGlAmount(myVar_pdDataFrameGL, 500)
                myVar_floatReturnsGL = fun_safeGetGlAmount(myVar_pdDataFrameGL, 530) # Typically negative in GL data
                myVar_floatCogsGL = fun_safeGetGlAmount(myVar_pdDataFrameGL, 600)     # Typically negative in GL data
                myVar_floatFreightGL = fun_safeGetGlAmount(myVar_pdDataFrameGL, 610) # Typically negative in GL data

                # Calculate derived GL values
                myVar_floatTotalSalesGL = myVar_floatSalesGL + myVar_floatReturnsGL # Returns are usually credits (negative value for calc)
                myVar_floatGrossProfitGL = myVar_floatTotalSalesGL + myVar_floatCogsGL + myVar_floatFreightGL # Costs are usually debits (negative value for calc)

                # Prepare labels and values for GL bar chart
                myVar_listStrLabelsGL = ["Sales", "Returns", "Total Sales", "COGS", "Freight", "Gross Profit"]
                myVar_listFloatValuesGL = [
                    myVar_floatSalesGL, myVar_floatReturnsGL, myVar_floatTotalSalesGL,
                    myVar_floatCogsGL, myVar_floatFreightGL, myVar_floatGrossProfitGL
                ]

                # Display GL values for verification
                # Com_st.write("🧾 Debug - GL Values:", dict(zip(myVar_listStrLabelsGL, myVar_listFloatValuesGL)))

                # Generate and display GL bar chart
                Com_st.subheader("📊 General Ledger - Bar Chart Breakdown")
                myVar_goFigureGL = Com_go.Figure(Com_go.Bar(
                    x=myVar_listStrLabelsGL, y=myVar_listFloatValuesGL,
                    text=[f"${v / 1_000_000:.2f}M" for v in myVar_listFloatValuesGL], # Text labels in millions
                    textposition="outside",
                    marker_color=[ # Color coding based on typical impact
                        "green",   # Sales
                        "orange",  # Returns (negative impact on net sales)
                        "blue",    # Total Sales
                        "red",     # COGS
                        "red",     # Freight
                        "blue"     # Gross Profit
                    ]
                ))
                myVar_goFigureGL.update_layout(
                    title="General Ledger Breakdown (Feb Yr 25)",
                    yaxis_title="Amount ($)", xaxis_title="Category"
                )
                Com_st.plotly_chart(myVar_goFigureGL, use_container_width=True)
                Com_st.metric("Gross Profit (from GL Report)", f"${myVar_floatGrossProfitGL:,.2f}")

            else:
                Com_st.warning("⚠️ No data found in General Ledger (GL) for this period.")

        except Exception as myVar_objException:
           # --- Error Handling ---
           Com_st.error(f"❌ Error during Sales vs GL comparison: {myVar_objException}")
           Com_st.code(traceback.format_exc())


# ============================================================================
# 🚀 STREAMLIT UI (for local testing or as a single-page app)
# ============================================================================
# Description: This block sets up the main UI structure for testing or running
#              this script directly. It allows selecting which report function
#              to execute.
# ----------------------------------------------------------------------------

# Control block: Ensures this code runs only when the script is executed directly.
if __name__ == "__main__":

    # --- Attempt to Connect to Database ---
    # Create the DB engine by calling the function
    myVar_objDbEngine = fun_connectToDb(
        myCon_strDbUsername, myCon_strDbPassword, myCon_strDbServer, myCon_strDbDatabase
    )

    # --- Main Application Logic ---
    # Control block: Only proceed if the database engine was created successfully.
    if myVar_objDbEngine:
        # --- Sidebar Navigation ---
        # Use sidebar radio buttons to select which report section to display
        Com_st.sidebar.title("📊 Report Navigation")
        myVar_strSelectedReport = Com_st.sidebar.radio(
            "Choose a Report:",
            options=[
                "Cost by Order",
                "Shipment by Order",
                "MP by Order",
                "Credit Memos (Feb Yr 25)",
                "Untransactioned Costs (Feb Yr 25)",
                "Sales Report (OE - Feb Yr 25)",
                "Sales vs GL Comparison (Feb Yr 25)"
            ],
            key="main_report_selection"
        )

        # --- Main Panel Display ---
        # Control block: Conditional execution based on sidebar selection.
        # Set title and call the corresponding subprocedure.

        if myVar_strSelectedReport == "Cost by Order":
            Com_st.title("💰 Cost Dashboard by Order") # Set title before calling
            Com_st.markdown("---")
            # Call the subprocedure, passing the engine
            sub_displayCostByOrder(myVar_objDbEngine)

        elif myVar_strSelectedReport == "Shipment by Order":
            Com_st.title("📦 Shipment Dashboard by Order") # Set title before calling
            Com_st.markdown("---")
            # Call the subprocedure, passing the engine
            sub_displayShipmentByOrder(myVar_objDbEngine)

        elif myVar_strSelectedReport == "MP by Order":
            Com_st.title("🏭 MP Dashboard by Order") # Set title before calling
            Com_st.markdown("---")
            # Call the subprocedure, passing the engine
            sub_displayMPByOrder(myVar_objDbEngine)

        elif myVar_strSelectedReport == "Credit Memos (Feb Yr 25)":
            Com_st.title("📉 Credit Memos Analysis (Feb Yr 25)") # Set title before calling
            Com_st.markdown("---")
            # Call the subprocedure, passing the engine
            sub_displayCreditMemos(myVar_objDbEngine)

        elif myVar_strSelectedReport == "Untransactioned Costs (Feb Yr 25)":
            Com_st.title("💸 Untransactioned Costs Analysis (Feb Yr 25)") # Set title before calling
            Com_st.markdown("---")
            # Call the subprocedure, passing the engine
            sub_displayUntransactionedCosts(myVar_objDbEngine)

        elif myVar_strSelectedReport == "Sales Report (OE - Feb Yr 25)":
            Com_st.title("📈 Sales Report (OE Tables - Feb Yr 25)") # Set title before calling
            Com_st.markdown("---")
            # Call the subprocedure, passing the engine
            sub_displaySalesReportFromOE(myVar_objDbEngine)

        elif myVar_strSelectedReport == "Sales vs GL Comparison (Feb Yr 25)":
            Com_st.title("⚖️ Sales (OE) vs GL Comparison (Feb Yr 25)") # Set title before calling
            Com_st.markdown("---")
            # Call the subprocedure, passing the engine
            sub_compareSalesVsGL(myVar_objDbEngine)

    else:
        # Display error if database connection failed at startup
        Com_st.error("Application cannot start because the database connection failed. Please check credentials and server accessibility.")

# ============================================================================
#  EOF
# ============================================================================