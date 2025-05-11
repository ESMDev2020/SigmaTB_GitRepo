# =============================
# IMPORTS
# =============================
import streamlit as myCom_Streamlit
import pandas as myVar_pd
import matplotlib.pyplot as myCom_plt
import seaborn as myCom_sns
import altair as myCom_alt
from sqlalchemy import create_engine
import traceback # Added for error details

# =============================
# CONSTANTS: Database connection Parameters (Used for local testing connection)
# =============================
myCon_strServer = "database-3.c67ymu6q22o1.us-east-1.rds.amazonaws.com"
myCon_strDatabase = "SigmaTB"
myCon_strUser = "admin"
# !! Warning: Hardcoding passwords is insecure. Use st.secrets for production. !!
myCon_strPassword = "Er1c41234$"

# --- REMOVED GLOBAL ENGINE CREATION ---
# The engine is now expected to be passed into the functions.
# myCon_dbEngine = create_engine(f"mssql+pymssql://{myCon_strUser}:{myCon_strPassword}@{myCon_strServer}:1433/{myCon_strDatabase}")


# =============================
# CONSTANTS: Section titles (Used for local testing)
# =============================
myCon_listTitles = [
    "🔍 Item Being Reviewed",
    "📈 IA / MP / SO Summary (Last 13 Months)",
    "📦 Inventory On Hand vs Reserved",
    "🔪 Usage and Vendor",
    "🗓 Depletion Forecast",
    "🧪 Family Breakdown (if any)" # Note: Query might need adjustment for family logic
]

# =============================
# FUNCTION: Report by ITEM
# =============================
# Note before the function:
# Fetches multiple datasets related to a specific item ID from the database.
def generate_item_report(myPar_objDbEngine, myPar_strItemId: str):
    """
    Fetches various details for a specific item ID by running multiple SQL queries.

    Description:
        Takes a database engine and an item ID. Constructs a multi-part SQL query
        to retrieve item description, usage summary, inventory levels, vendor info,
        depletion forecast, and potential family data. Executes queries and returns
        results as a list of dictionaries.

    Variables Used:
        - myPar_objDbEngine (SQLAlchemy Engine): The database engine passed from the caller.
        - myPar_strItemId (str): The item ID to generate the report for.

    Variables Returned:
        - dict: A dictionary containing:
            - "success" (bool): True if successful, False on error.
            - "data" (list): A list of dictionaries, each representing a result set (if success).
            - "error" (str): Error message string (if success is False).
    """
    # --- Local Variables ---
    # myVar_strQuery: The multi-part SQL query string.
    # myVar_listResults: List to hold result DataFrames.
    # myVar_objDbConnection: Active database connection.
    # myVar_idx: Loop index.
    # myVar_sql: Single SQL statement from the split query.
    # myVar_df: DataFrame holding results of a single SQL statement.
    # myVar_err: Caught exception object.

    # !! Warning: Using f-string directly with item_id can lead to SQL injection if not properly validated upstream.
    myVar_strQuery = f"""
        SELECT [Size Text], Description, SMO FROM e_ROPData WHERE Item = {myPar_strItemId};

        WITH Months AS (
            SELECT FORMAT(DATEADD(MONTH, -n, CAST(GETDATE() AS DATE)), 'yyyy-MM') AS Month
            FROM (SELECT TOP 13 ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) - 1 AS n FROM sys.all_objects) AS x
        ),
        Aggregated AS (
            SELECT FORMAT(DATEFROMPARTS(2000 + IHTRYY, IHTRMM, 1), 'yyyy-MM') AS Month,
                   CASE WHEN CONVERT(VARCHAR(10), IHTRNT) = 'IA' THEN IHTQTY
                        WHEN CONVERT(VARCHAR(10), IHTRNT) IN ('OW', 'OR') THEN IHTQTY
                        WHEN CONVERT(VARCHAR(10), IHTRNT) = 'IN' THEN IHTQTY
                        ELSE 0 END AS Qty,
                   CONVERT(VARCHAR(10), IHTRNT) AS Type
            FROM e_UsageData WHERE IHITEM = {myPar_strItemId} AND DATEFROMPARTS(2000 + IHTRYY, IHTRMM, 1) >= DATEADD(MONTH, -13, CAST(GETDATE() AS DATE))
        )
        SELECT m.Month,
               CASE WHEN SUM(CASE WHEN a.Type = 'IA' THEN a.Qty ELSE 0 END) = 0 THEN '-' ELSE FORMAT(SUM(CASE WHEN a.Type = 'IA' THEN a.Qty ELSE 0 END), 'N2') END AS [IA (Inventory Adjustments)],
               CASE WHEN SUM(CASE WHEN a.Type IN ('OW', 'OR') THEN a.Qty ELSE 0 END) = 0 THEN '-' ELSE FORMAT(SUM(CASE WHEN a.Type IN ('OW', 'OR') THEN a.Qty ELSE 0 END), 'N2') END AS [MP (Material Processed)],
               CASE WHEN SUM(CASE WHEN a.Type = 'IN' THEN a.Qty ELSE 0 END) = 0 THEN '-' ELSE FORMAT(SUM(CASE WHEN a.Type = 'IN' THEN a.Qty ELSE 0 END), 'N2') END AS [SO (Sales Orders)]
        FROM Months m LEFT JOIN Aggregated a ON m.Month = a.Month GROUP BY m.Month ORDER BY m.Month;

        SELECT [OnHand], [Rsrv], [OnHand] - [Rsrv] AS [Available Inv] FROM e_ROPData WHERE Item = {myPar_strItemId};

        SELECT 'Usage and Vendor' AS [Title], [#/ft], [UOM], [$/ft], [con/wk], [Vndr] FROM e_ROPData WHERE Item = {myPar_strItemId};

        SELECT 'When and how much' AS [Question], [OnHand] - [Rsrv] AS [Available Inv], ([#/ft] * ([OnHand] - [Rsrv])) AS [Pounds],
               [$/ft] * ([OnHand] - [Rsrv]) AS [Dollars], ([OnHand] - [Rsrv]) / NULLIF([con/wk], 0) AS [Weeks], -- Avoid division by zero
               CASE WHEN [con/wk] IS NOT NULL AND [con/wk] <> 0 THEN DATEADD(WEEK, CAST(([OnHand] - [Rsrv]) / [con/wk] AS INT), CAST(GETDATE() AS DATE)) ELSE NULL END AS [Expected Depletion Date] -- Safer DateAdd
        FROM e_ROPData WHERE Item = {myPar_strItemId};

        -- Family Breakdown Query - Review and adjust logic as needed for your definition of "family"
        SELECT r.Item, (r.OnHand - r.Rsrv) AS [Available], r.OnPO, r.[#/ft],
               COALESCE(us.total_usage, 0) AS total_usage, -- Renamed
               r.[con/wk] AS [wk use], -- Renamed
               r.description, r.[Size Text] as "Size"
        FROM e_ROPData r LEFT JOIN (
            SELECT IHITEM, SUM(IHTQTY) AS total_usage FROM e_usagedata
            -- WHERE e_usagedata.IHITEM = e_usagedata.column4 -- This condition seems unusual, verify schema relationship
            WHERE IHITEM = {myPar_strItemId} -- Likely only want usage for the item itself unless family defined differently
            GROUP BY IHITEM
        ) us ON r.Item = us.IHITEM WHERE r.Item = {myPar_strItemId};
    """
    # Control block: try...except for database operations.
    try:
        myVar_listResults = []
        # Use the passed-in engine parameter here
        # Control block: 'with' ensures connection closure.
        with myPar_objDbEngine.begin() as myVar_objDbConnection:
             # Control block: Loop through semi-colon separated SQL statements.
            for myVar_idx, myVar_sql in enumerate(myVar_strQuery.strip().split(";")):
                 # Control block: Check if SQL string is not empty.
                if myVar_sql.strip():
                    # Execute query and store result
                    myVar_df = myVar_pd.read_sql(myVar_sql.strip(), myVar_objDbConnection)
                    myVar_listResults.append(myVar_df)
        # Return success and data converted to dictionaries
        return {"success": True, "data": [df.to_dict(orient='records') for df in myVar_listResults]}
    except Exception as myVar_err:
        # Return failure and error message
        return {"success": False, "error": str(myVar_err)}

# =============================
# FUNCTION: Show Full ROP Table
# =============================
# Note before the function:
# Fetches the entire content of the 'e_ROP' table.
def get_rop_table(myPar_objDbEngine):
    """
    Fetches all data from the e_ROP table.

    Description:
        Takes a database engine, connects, and executes a simple SELECT * query
        on the e_ROP table. Returns the data as a list of dictionaries.

    Variables Used:
        - myPar_objDbEngine (SQLAlchemy Engine): The database engine passed from the caller.

    Variables Returned:
        - dict: A dictionary containing:
            - "success" (bool): True if successful, False on error.
            - "data" (list): List of dictionaries representing table rows (if success).
            - "error" (str): Error message string (if success is False).
    """
    # --- Local Variables ---
    # myVar_objDbConnection: Active database connection.
    # myVar_df: DataFrame holding query results.
    # myVar_err: Caught exception object.

    # Control block: try...except for database operations.
    try:
        # Use the passed-in engine parameter here
        # Control block: 'with' ensures connection closure.
        with myPar_objDbEngine.begin() as myVar_objDbConnection:
            myVar_df = myVar_pd.read_sql("SELECT * FROM e_ROP", myVar_objDbConnection)
        return {"success": True, "data": myVar_df.to_dict(orient='records')}
    except Exception as myVar_err:
        return {"success": False, "error": str(myVar_err)}

# =============================
# FUNCTION: Count ROP by Group
# =============================
# Note before the function:
# Counts entries in the 'e_ROP' table, grouped by 'Column3'.
def count_rop_by_group(myPar_objDbEngine):
    """
    Counts ROP entries grouped by the 'Type' (Column3).

    Description:
        Takes a database engine, connects, and executes a query that counts
        records in the e_ROP table, grouping by the distinct values in Column3.
        Returns the counts as a list of dictionaries.

    Variables Used:
        - myPar_objDbEngine (SQLAlchemy Engine): The database engine passed from the caller.

    Variables Returned:
        - dict: A dictionary containing:
            - "success" (bool): True if successful, False on error.
            - "data" (list): List of dictionaries with 'Type' and 'Total' (if success).
            - "error" (str): Error message string (if success is False).
    """
    # --- Local Variables ---
    # myVar_strSqlQuery: SQL query string.
    # myVar_objDbConnection: Active database connection.
    # myVar_df: DataFrame holding query results.
    # myVar_err: Caught exception object.

    # Control block: try...except for database operations.
    try:
         # Define the SQL query
        myVar_strSqlQuery = """
            SELECT RTRIM(CAST(Column3 AS VARCHAR(MAX))) AS Type, COUNT(*) AS Total
            FROM e_ROP WHERE Column3 IS NOT NULL
            GROUP BY RTRIM(CAST(Column3 AS VARCHAR(MAX))) ORDER BY Total DESC;
        """
        # Use the passed-in engine parameter here
        # Control block: 'with' ensures connection closure.
        with myPar_objDbEngine.begin() as myVar_objDbConnection:
            myVar_df = myVar_pd.read_sql(myVar_strSqlQuery, myVar_objDbConnection)
        return {"success": True, "data": myVar_df.to_dict(orient='records')}
    except Exception as myVar_err:
        return {"success": False, "error": str(myVar_err)}

# =============================
# FUNCTION: Summary Dashboard Data
# =============================
# Note before the function:
# Fetches data from 'e_ROPData', processes it, and calculates summary statistics.
def get_summary_dashboard_data(myPar_objDbEngine):
    """
    Calculates summary statistics based on the e_ROPData table.

    Description:
        Takes a database engine, fetches data from e_ROPData, renames columns,
        calculates derived fields like 'Weeks Left' and 'Reorder Flag', and
        computes overall summary metrics (total items, items below threshold,
        average weeks, total stock, total on PO). Returns summary and full data.

    Variables Used:
        - myPar_objDbEngine (SQLAlchemy Engine): The database engine passed from the caller.

    Variables Returned:
        - dict: A dictionary containing:
            - "success" (bool): True if successful, False on error.
            - "summary" (dict): Dictionary of summary metrics (if success).
            - "full_data" (list): List of dictionaries for the processed data (if success).
            - "error" (str): Error message string (if success is False).
    """
    # --- Local Variables ---
    # myVar_objDbConnection: Active database connection.
    # myVar_df: DataFrame holding query results and processed data.
    # myVar_dictSummary: Dictionary holding the calculated summary statistics.
    # myVar_err: Caught exception object.

    # Control block: try...except for database and processing operations.
    try:
        # Use the passed-in engine parameter here
        # Control block: 'with' ensures connection closure.
        with myPar_objDbEngine.begin() as myVar_objDbConnection:
            myVar_df = myVar_pd.read_sql("SELECT * FROM e_ROPData", myVar_objDbConnection)

        # --- Data Processing ---
        # Control block: Check if data was loaded before processing.
        if not myVar_df.empty:
            myVar_df = myVar_df.rename(columns={
                "OnHand": "In Stock (ft)", "OnPO": "PO Incoming (ft)",
                "#/ft": "Feet per Unit", "con/wk": "Usage/Week", "FastPathSort": "Grade"
            })

            # Ensure numeric types and handle errors
            myVar_df['Usage/Week'] = myVar_pd.to_numeric(myVar_df['Usage/Week'], errors='coerce')
            myVar_df['In Stock (ft)'] = myVar_pd.to_numeric(myVar_df['In Stock (ft)'], errors='coerce')
            myVar_df['PO Incoming (ft)'] = myVar_pd.to_numeric(myVar_df['PO Incoming (ft)'], errors='coerce')


            # Filter out invalid usage after conversion
            myVar_df = myVar_df[myVar_df["Usage/Week"].notnull() & (myVar_df["Usage/Week"] > 0)].copy()

            # Proceed with calculations only if data remains after filtering
            if not myVar_df.empty:
                myVar_df.loc[:, "Weeks Left"] = (myVar_df["In Stock (ft)"] / myVar_df["Usage/Week"]).round(1)
                myVar_df.loc[:, "Reorder Flag"] = myVar_df["Weeks Left"].apply(
                    lambda w: "✅ No" if myVar_pd.notnull(w) and w > 26 else ("⚠️ Caution" if myVar_pd.notnull(w) and 12 < w <= 26 else "❌ Yes")
                )
                myVar_df.loc[:, "Origin"] = myVar_df["Description"].apply(lambda x: "China" if isinstance(x, str) and "++" in x else "Other")

                # Calculate summary statistics
                myVar_dictSummary = {
                    "Total Active Items": len(myVar_df),
                    "Items Below 12 Weeks": int((myVar_df['Weeks Left'] < 12).sum()), # Cast to int
                    "Avg Inventory Weeks": round(myVar_df['Weeks Left'].mean(), 1) if not myVar_df['Weeks Left'].empty else 0.0, # Handle potential empty series
                    "Total Feet On Hand": myVar_df['In Stock (ft)'].sum(),
                    "Total PO Feet In Transit": myVar_df['PO Incoming (ft)'].sum()
                }
                return {"success": True, "summary": myVar_dictSummary, "full_data": myVar_df.to_dict(orient='records')}
            else:
                 return {"success": False, "error": "No active items found after initial processing."}
        else:
             return {"success": False, "error": "No data found in e_ROPData table."}

    except Exception as myVar_err:
        return {"success": False, "error": str(myVar_err)}

# =============================
# STREAMLIT UI (for local testing)
# =============================
# Control block: Runs only when script is executed directly.
if __name__ == "__main__":
    myCom_Streamlit.title("ROP Reports Module - Local Test")
    myCom_Streamlit.markdown("Testing callable functions for ROP reports.")
    myCom_Streamlit.markdown("---")

    # --- Create a LOCAL engine instance FOR TESTING ONLY ---
    myVar_strTestConnectionString = f"mssql+pymssql://{myCon_strUser}:{myCon_strPassword}@{myCon_strServer}:1433/{myCon_strDatabase}"
    myVar_objTestDbEngine = None
    try:
        myVar_objTestDbEngine = create_engine(myVar_strTestConnectionString)
        with myVar_objTestDbEngine.connect() as myVar_objTestDbConnection: # Test connection
             myCom_Streamlit.success("🔌 Local Test DB Engine Connected Successfully.")
    except Exception as myVar_objTestEngErr:
        myCom_Streamlit.error(f"❌ Failed to create Local Test DB Engine: {myVar_objTestEngErr}")
        myCom_Streamlit.stop() # Stop if test engine fails

    # --- Test Item Report ---
    myCom_Streamlit.header("Test: Item Report")
    myVar_strItemId_ui = myCom_Streamlit.text_input("Enter Item Number for Report", value="50002", key="test_item_input")
    # Control block: Test button for Item Report
    if myCom_Streamlit.button("Run Item Report Test", key="test_item_button"):
        # Call function, PASSING the test engine
        myVar_dictReportData = generate_item_report(myVar_objTestDbEngine, myVar_strItemId_ui)
        # Control block: Check function success flag.
        if myVar_dictReportData["success"]:
            myCom_Streamlit.success("✅ Item Report Generated!")
            # Control block: Loop through result sets if successful.
            for myVar_idx, item_data in enumerate(myVar_dictReportData["data"]):
                # Convert dictionary back to DataFrame for display
                myVar_dfDisplay = myVar_pd.DataFrame(item_data)
                # Get title or generate default
                myVar_strTitle = myCon_listTitles[myVar_idx] if myVar_idx < len(myCon_listTitles) else f"Result {myVar_idx + 1}"
                myCom_Streamlit.subheader(myVar_strTitle)
                myCom_Streamlit.dataframe(myVar_dfDisplay)

            # Simplified chart example for testing display
            # Control block: Check if enough data exists for chart.
            if len(myVar_dictReportData["data"]) >= 3:
                myVar_pdInventoryData = myVar_pd.DataFrame(myVar_dictReportData["data"][2])
                 # Control block: Check if inventory data is not empty.
                if not myVar_pdInventoryData.empty and "OnHand" in myVar_pdInventoryData.columns and "Rsrv" in myVar_pdInventoryData.columns and "Available Inv" in myVar_pdInventoryData.columns:
                    # Basic chart data creation
                    myVar_pdChartData = myVar_pd.DataFrame({
                        "Metric": ["OnHand", "Reserved", "Available"],
                        "Value": [
                            float(myVar_pdInventoryData.at[0, "OnHand"]),
                            float(-myVar_pdInventoryData.at[0, "Rsrv"]),
                            float(myVar_pdInventoryData.at[0, "Available Inv"])
                        ]
                    })
                    myCom_Streamlit.subheader(f"🌍 Item {myVar_strItemId_ui} Overview Chart")
                    # Create Altair chart
                    myVar_altBarChart = myCom_alt.Chart(myVar_pdChartData).mark_bar().encode(
                        x=myCom_alt.X("Metric", title="Metric"),
                        y=myCom_alt.Y("Value", title="Feet", scale=myCom_alt.Scale(zero=True)),
                        color=myCom_alt.Color("Metric", legend=None)
                    ).properties(width=500, height=300)
                    myCom_Streamlit.altair_chart(myVar_altBarChart) # Display chart
                else:
                    myCom_Streamlit.warning("Could not generate item chart due to missing columns in result set 2.")
        else:
             # Display error if function failed
            myCom_Streamlit.error(f"❌ Error generating report: {myVar_dictReportData['error']}")

    myCom_Streamlit.markdown("---")

    # --- Test ROP Table ---
    myCom_Streamlit.header("Test: Full ROP Table")
     # Control block: Test button for ROP Table.
    if myCom_Streamlit.button("Show ROP Table Test", key="test_rop_table_button"):
        # Call function, PASSING the test engine
        myVar_dictRopTableData = get_rop_table(myVar_objTestDbEngine)
        # Control block: Check function success flag.
        if myVar_dictRopTableData["success"]:
            myCom_Streamlit.subheader("Full ROP Table")
            myCom_Streamlit.dataframe(myVar_pd.DataFrame(myVar_dictRopTableData["data"])) # Display data
        else:
            myCom_Streamlit.error(f"❌ Error fetching ROP Table: {myVar_dictRopTableData['error']}") # Display error

    myCom_Streamlit.markdown("---")

    # --- Test ROP Count by Group ---
    myCom_Streamlit.header("Test: ROP Count by Group")
    # Control block: Test button for ROP Count.
    if myCom_Streamlit.button("Count ROP by group Test", key="test_rop_count_button"):
         # Call function, PASSING the test engine
        myVar_dictRopCountData = count_rop_by_group(myVar_objTestDbEngine)
        # Control block: Check function success flag.
        if myVar_dictRopCountData["success"]:
            myCom_Streamlit.subheader("ROP Count by Group")
            myCom_Streamlit.dataframe(myVar_pd.DataFrame(myVar_dictRopCountData["data"])) # Display data
        else:
            myCom_Streamlit.error(f"❌ Error fetching ROP Count: {myVar_dictRopCountData['error']}") # Display error

    myCom_Streamlit.markdown("---")

    # --- Test Summary Dashboard Data ---
    myCom_Streamlit.header("Test: Summary Dashboard Data")
    # Control block: Test button for Summary Data.
    if myCom_Streamlit.button("Show Summary Dashboard Test", key="test_summary_button"):
        # Call function, PASSING the test engine
        myVar_dictSummaryData = get_summary_dashboard_data(myVar_objTestDbEngine)
        # Control block: Check function success flag.
        if myVar_dictSummaryData["success"]:
            myCom_Streamlit.subheader("📋 Summary Metrics")
            # Control block: Loop through summary dictionary items.
            for myVar_strLabel, myVar_objValue in myVar_dictSummaryData["summary"].items():
                myCom_Streamlit.metric(label=myVar_strLabel, value=myVar_objValue) # Display metrics

            # Convert full data back to DataFrame for display/plotting
            myVar_pdFullDf = myVar_pd.DataFrame(myVar_dictSummaryData["full_data"])

            # Display plots (example using matplotlib/seaborn from original test block)
            # Control block: Check if needed columns exist before plotting
            if all(col in myVar_pdFullDf.columns for col in ["Grade", "Weeks Left", "Reorder Flag", "Origin"]):
                myCom_Streamlit.subheader("📊 Inventory Weeks by Grade")
                myVar_fig1, myVar_ax1 = myCom_plt.subplots(figsize=(8, 5)) # Create figure and axes
                myCom_sns.barplot(data=myVar_pdFullDf, x="Grade", y="Weeks Left", hue="Reorder Flag", ax=myVar_ax1)
                myVar_ax1.set_title("Inventory Weeks by Grade")
                myCom_plt.tight_layout()
                myCom_Streamlit.pyplot(myVar_fig1) # Display matplotlib figure

                myCom_Streamlit.subheader("🌍 Stock by Origin")
                # Calculate value counts for pie chart
                myVar_pdOriginCounts = myVar_pdFullDf["Origin"].value_counts()
                myVar_fig2, myVar_ax2 = myCom_plt.subplots(figsize=(6, 6)) # Create figure and axes
                myVar_ax2.pie(myVar_pdOriginCounts, labels=myVar_pdOriginCounts.index, autopct='%1.1f%%', startangle=140)
                myVar_ax2.set_ylabel('') # Remove y-label for pie chart
                myVar_ax2.set_title("Stock by Origin")
                myCom_plt.tight_layout()
                myCom_Streamlit.pyplot(myVar_fig2) # Display matplotlib figure
            else:
                myCom_Streamlit.warning("Could not generate summary plots due to missing columns (Grade, Weeks Left, Reorder Flag, or Origin).")


            # Display full data table
            myCom_Streamlit.subheader("📄 Full Processed ROPData Table")
            myCom_Streamlit.dataframe(myVar_pdFullDf)
        else:
            myCom_Streamlit.error(f"❌ Failed to load summary dashboard data: {myVar_dictSummaryData['error']}") # Display error

# =============================
#  EOF
# =============================