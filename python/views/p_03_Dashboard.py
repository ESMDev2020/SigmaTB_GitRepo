# p_03_Dashboard.py

# ============================================================================
# 📦 IMPORTS
# ============================================================================
# Description: Import necessary libraries for the application.
# - streamlit (Com_st): For building the web interface.
# - pandas (Com_pd): For data manipulation and analysis.
# - matplotlib.pyplot (Com_plt): For plotting (less used here).
# - seaborn (Com_sns): For statistical data visualization.
# - altair (Com_alt): For interactive statistical visualizations.
# - sqlalchemy (create_engine): For database connection type hint (engine passed in).
# - traceback: For detailed error logging.
# ----------------------------------------------------------------------------
import streamlit as Com_st
import pandas as Com_pd
# import matplotlib.pyplot as Com_plt # Not used in this final version
# import seaborn as Com_sns # Not used in this final version
import altair as Com_alt
from sqlalchemy import create_engine # For type hinting Engine object
import traceback
from sqlalchemy import text

# ============================================================================
# 📜 CONSTANTS
# ============================================================================
# Description: Define constant values used within this module.
# - myCon_listStrQueryTitles: Titles for displaying results of item-specific queries.
# ----------------------------------------------------------------------------

# ---------- Titles for each query result set when showing item details ----------
myCon_listStrQueryTitles = [
    "🔍 Item Being Reviewed",
    "📈 IA / MP / SO Summary (Last 13 Months)",
    "📦 Inventory On Hand vs Reserved",
    "🔪 Usage and Vendor",
    "🗓 Depletion Forecast",
    "🧪 Inventory + PO",
    "🧪 Purchase Orders",
    "🧪 Family Breakdown (if any)"
]

# --- Database connection constants and engine are removed ---
# --- The engine object (myPar_objDbEngine) is expected to be passed into sub_displayMainDashboardView ---

# ============================================================================
# 🧱 FUNCTIONS & SUBPROCEDURES
# ============================================================================
# Description: Define reusable helper functions and the main display subprocedures
#              corresponding to the logical sections of the dashboard.
# ----------------------------------------------------------------------------

# Note before the function: Helper to safely convert DataFrame cell value to float.
def fun_safeFloat(myPar_pdDataFrame, myPar_strColName, myPar_floatDefault=0.0):
    """ Safely extracts and converts value from DataFrame cell to float. """
    # --- Local Variables ---
    # myVar_objValue, myVar_floatValue
    try:
        myVar_objValue = myPar_pdDataFrame.at[0, myPar_strColName]
        # Use Com_pd alias here
        myVar_floatValue = float(myVar_objValue) if Com_pd.notnull(myVar_objValue) else myPar_floatDefault
        return myVar_floatValue
    except Exception:
        return myPar_floatDefault

#==============================================================================
# ================== SECTION 2: ITEM REPORT DISPLAY LOGIC ====================
#==============================================================================
# Note before the subprocedure:
# Displays the detailed report for a specific item ID.
# Accepts Item ID as string/int (optional), validates/converts to int internally.
def sub_displayItemReport(myPar_objDbEngine, myPar_intItemId: int = None): # Type hint is int=None
    """
    Fetches, formats, and displays the detailed report for a specific item ID.
    Prompts for input if ID not provided. Validates input is an integer.

    Variables Used:
        - myPar_objDbEngine (SQLAlchemy Engine): Database engine.
        - myPar_intItemId (int, optional): The parameter passed (could be None, str, int).
        - myCon_listStrQueryTitles (list): Global titles list.
    Variables Returned:
        - None (Displays UI directly).
    """
    # --- Local Variables ---
    # myVar_strItemIdProvided: Holds the initial ID input (string or None).
    # myVar_strItemIdFromInput: Holds ID from text_input if parameter was None (string).
    # myVar_intItemIdToUse: Holds the final validated Item ID as an integer.
    # myVar_strSqlItemReportQuery: The multi-part SQL query string.
    # myVar_listPdDataframesResults: List to store DataFrames from each query part.
    # myVar_objDbConnection: Active database connection object.
    # myVar_strSqlSingleQuery: Individual SQL query string from the split multi-part query.
    # myVar_pdDataframeCurrentResult: DataFrame holding results of a single query part.
    # myVar_intIndex: Loop counter for iterating through results/titles.
    # myVar_strResultTitle: Title for the current result section.
    # myVar_pdDataframeInventory: DataFrame specific to inventory data.
    # myVar_pdDataframeUsageVendor: DataFrame specific to usage/vendor data.
    # myVar_pdDataframeExtra: DataFrame specific to extra inventory/PO details.
    # myVar_floatOnhand, myVar_floatReserved, ... : Floats for chart data calculation.
    # myVar_listStrMetricLabels: Labels for the overview chart bars.
    # myVar_listFloatMetricValues: Values for the overview chart bars.
    # myVar_pdDataframeChartData: DataFrame formatted for the Altair chart.
    # myVar_altChartItemOverview: The generated Altair bar chart object.
    # myVar_errReport: Stores any exception caught during report generation.
    # myVar_fmtErr, myVar_keyErr: Stores exceptions during formatting.
    # e: General exception object

    myVar_intItemIdToUse = None # Initialize the target integer ID as None

    # --- Determine and Validate Item ID ---
    myVar_strItemIdProvided = None # Initialize string holder

    # Control Block: Handle the case where the parameter is None (prompt user)
    if myPar_intItemId is None:
        Com_st.subheader("Enter Item ID for Report")
        # Get input as string
        myVar_strItemIdFromInput = Com_st.text_input( # Assign to myVar_strItemIdFromInput
            "Item ID:",
            key="item_report_direct_input_Corrected", # Use a consistent key
            help="Enter the Item ID (numbers only)."
        )
        # If user entered something, that's the string we need to process
        if myVar_strItemIdFromInput:
            myVar_strItemIdProvided = myVar_strItemIdFromInput # Assign the input string
        # else: User hasn't entered anything yet after being prompted. Will be handled later.

    # Control Block: Handle the case where a parameter *was* passed
    else:
        # Convert the passed parameter to string first for consistent handling
        try:
            myVar_strItemIdProvided = str(myPar_intItemId).strip()
        except Exception as e:
            Com_st.warning(f"Could not convert passed parameter '{myPar_intItemId}' to string: {e}. Cannot proceed.")
            myVar_strItemIdProvided = None # Treat as invalid if conversion fails

    # --- Try converting the determined input string (if any) to int ---
    # Control Block: Only proceed if we have *some* string input (either from param or text_input)
    if myVar_strItemIdProvided is not None and myVar_strItemIdProvided.strip():
        try:
            # Attempt conversion to integer
            myVar_intItemIdToUse = int(myVar_strItemIdProvided) # Assign integer to myVar_intItemIdToUse
            # Optional: Add validation like checking if positive
            if myVar_intItemIdToUse <= 0:
                 Com_st.warning(f"Item ID '{myVar_strItemIdProvided}' must be positive. Please correct.")
                 myVar_intItemIdToUse = None # Invalidate if non-positive

        except ValueError:
            # Handle conversion error if input string is not a valid integer
            Com_st.error(f"❌ Invalid Item ID format: '{myVar_strItemIdProvided}'. Please enter numbers only.")
            myVar_intItemIdToUse = None # Invalidate on error
        except Exception as e:
            # Catch other potential errors
            Com_st.error(f"Error processing Item ID '{myVar_strItemIdProvided}': {e}")
            myVar_intItemIdToUse = None # Invalidate on error

    # --- Provide feedback or proceed with report ---
    # Control Block: Check if we ended up with a valid integer ID
    if myVar_intItemIdToUse is not None:
        # We have a valid integer ID, proceed to generate the report
        Com_st.markdown("---")
        Com_st.subheader(f"🔍 Detailed Report for Item: {myVar_intItemIdToUse}") # Show the integer ID
        try:
            # --- Construct SQL Query using myVar_intItemIdToUse ---
            # REMEMBER TO INCLUDE THE SQL JOIN FIX (TRY_CAST) HERE IF NOT ALREADY DONE
            # !! IMPORTANT: Ensure your full SQL queries are included here !!
            myVar_strSqlItemReportQuery = f"""
                SELECT [Size Text], Description, SMO FROM e_ROPData WHERE Item = {myVar_intItemIdToUse};

                WITH Months AS ( SELECT FORMAT(DATEADD(MONTH, -n, CAST(GETDATE() AS DATE)), 'yyyy-MM') AS Month FROM (SELECT TOP 13 ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) - 1 AS n FROM sys.all_objects) AS x), Aggregated AS ( SELECT FORMAT(DATEFROMPARTS(2000 + IHTRYY, IHTRMM, 1), 'yyyy-MM') AS Month, CASE WHEN CONVERT(VARCHAR(10), IHTRNT) = 'IA' THEN IHTQTY WHEN CONVERT(VARCHAR(10), IHTRNT) IN ('OW', 'OR') THEN IHTQTY WHEN CONVERT(VARCHAR(10), IHTRNT) = 'IN' THEN IHTQTY ELSE 0 END AS Qty, CONVERT(VARCHAR(10), IHTRNT) AS Type FROM e_UsageData WHERE IHITEM = {myVar_intItemIdToUse} AND DATEFROMPARTS(2000 + IHTRYY, IHTRMM, 1) >= DATEADD(MONTH, -13, CAST(GETDATE() AS DATE))) SELECT m.Month, CASE WHEN SUM(CASE WHEN a.Type = 'IA' THEN a.Qty ELSE 0 END) = 0 THEN '-' ELSE FORMAT(SUM(CASE WHEN a.Type = 'IA' THEN a.Qty ELSE 0 END), 'N2') END AS [IA (Inventory Adjustments)], CASE WHEN SUM(CASE WHEN a.Type IN ('OW', 'OR') THEN a.Qty ELSE 0 END) = 0 THEN '-' ELSE FORMAT(SUM(CASE WHEN a.Type IN ('OW', 'OR') THEN a.Qty ELSE 0 END), 'N2') END AS [MP (Material Processed)], CASE WHEN SUM(CASE WHEN a.Type = 'IN' THEN a.Qty ELSE 0 END) = 0 THEN '-' ELSE FORMAT(SUM(CASE WHEN a.Type = 'IN' THEN a.Qty ELSE 0 END), 'N2') END AS [SO (Sales Orders)] FROM Months m LEFT JOIN Aggregated a ON m.Month = a.Month GROUP BY m.Month ORDER BY m.Month;

                SELECT [OnHand], [Rsrv], [OnHand] - [Rsrv] AS [Available Inv] FROM e_ROPData WHERE Item = {myVar_intItemIdToUse};

                SELECT 'Usage and Vendor' AS [Title], [#/ft], [UOM], [$/ft], [con/wk], [Vndr] FROM e_ROPData WHERE Item = {myVar_intItemIdToUse};

                SELECT 'When and how much' AS [Question], [OnHand] - [Rsrv] AS [Available Inv], ([#/ft] * ([OnHand] - [Rsrv])) AS [Pounds], [$/ft] * ([OnHand] - [Rsrv]) AS [Dollars], ([OnHand] - [Rsrv]) / NULLIF([con/wk], 0) AS [Weeks], CASE WHEN [con/wk] IS NOT NULL AND [con/wk] <> 0 THEN DATEADD(WEEK, CAST(([OnHand] - [Rsrv]) / [con/wk] AS INT), CAST(GETDATE() AS DATE)) ELSE NULL END AS [Expected Depletion Date] FROM e_ROPData WHERE Item = {myVar_intItemIdToUse};

                SELECT
                    -- Handle OnPO (TEXT type) safely using TRY_CAST, default 0.0
                    ISNULL(TRY_CAST(CAST(e_ROPData.[OnPO] AS VARCHAR(MAX)) AS FLOAT), 0.0) AS [OnPO],

                    -- Handle remnants (Assuming it MIGHT be text - CHECK SCHEMA). Default 0.0
                    ISNULL(TRY_CAST(CAST(e_TagData.remnants AS VARCHAR(MAX)) AS FLOAT), 0.0) AS remnants,

                    -- Level (NUMERIC) - select directly
                    e_ROPData.[Level],

                    -- PO Weeks calculation (using direct NUMERIC con/wk and safe OnPO)
                    CASE
                        -- Check NUMERIC con/wk directly for NULL and non-zero
                        WHEN e_ROPData.[con/wk] IS NOT NULL AND e_ROPData.[con/wk] <> 0
                        THEN ISNULL(TRY_CAST(CAST(e_ROPData.[OnPO] AS VARCHAR(MAX)) AS FLOAT), 0.0) -- Safe OnPO value
                            / e_ROPData.[con/wk] -- Direct division with NUMERIC con/wk
                        ELSE NULL -- Return NULL if con/wk is NULL or zero
                    END AS [PO Weeks],

                    -- New Depletion Date (using direct NUMERIC columns and safe OnPO)
                    CASE
                        -- Check NUMERIC con/wk directly for NULL and non-zero
                        WHEN e_ROPData.[con/wk] IS NOT NULL AND e_ROPData.[con/wk] <> 0
                        THEN DATEADD(
                            WEEK,
                            -- Explicitly CAST the result of the division (weeks) to INT for DATEADD
                            CAST(
                                ( -- Calculate Total Available Inventory
                                    ISNULL(e_ROPData.[OnHand], 0.0) -- OnHand (NUMERIC) - Use ISNULL for safety
                                - ISNULL(e_ROPData.[Rsrv], 0.0) -- Rsrv (NUMERIC) - Use ISNULL for safety
                                + ISNULL(TRY_CAST(CAST(e_ROPData.[OnPO] AS VARCHAR(MAX)) AS FLOAT), 0.0) -- Safe OnPO value
                                )
                                / e_ROPData.[con/wk] -- Direct division by NUMERIC con/wk
                            AS INT), -- Cast result to INT for DATEADD
                            GETDATE()
                            )
                        ELSE NULL -- Return NULL if con/wk is NULL or zero
                    END AS [New Depletion Date]
                FROM
                    e_ROPData -- Item is INT
                LEFT JOIN
                    e_TagData -- item is INT
                    ON e_ROPData.Item = e_TagData.item -- Correct JOIN (INT = INT)
                WHERE
                    e_ROPData.Item = {myVar_intItemIdToUse};

                SELECT e_POData.due, e_POData.[Due Date], e_POData.Vendor, e_POData.PO, e_POData.Ordered, e_POData.Received FROM e_POData WHERE e_POData.Item = {myVar_intItemIdToUse};

                SELECT r.Item, (r.OnHand - r.Rsrv) AS [Available], r.OnPO, r.[#/ft], COALESCE(us.total_usage, 0) AS total_usage, r.[con/wk] AS [wk use], r.description, r.[Size Text] as "Size" FROM e_ROPData r LEFT JOIN ( SELECT IHITEM, SUM(IHTQTY) AS total_usage FROM e_UsageData WHERE IHITEM = {myVar_intItemIdToUse} GROUP BY IHITEM ) us ON r.Item = us.IHITEM WHERE r.Item = {myVar_intItemIdToUse};
            """

            # --- Execute Queries & Display Results ---
            myVar_listPdDataframesResults = []
            with myPar_objDbEngine.begin() as myVar_objDbConnection:
                for myVar_strSqlSingleQuery in myVar_strSqlItemReportQuery.strip().split(";"):
                     if myVar_strSqlSingleQuery.strip():
                          myVar_pdDataframeCurrentResult = Com_pd.read_sql(myVar_strSqlSingleQuery.strip(), myVar_objDbConnection)
                          myVar_listPdDataframesResults.append(myVar_pdDataframeCurrentResult)
            Com_st.success(f"✅ Item {myVar_intItemIdToUse} detail data loaded!")

            # Display loop... chart logic... table formatting...
            for myVar_intIndex, myVar_pdDataframeCurrentResult in enumerate(myVar_listPdDataframesResults):
                 myVar_strResultTitle = myCon_listStrQueryTitles[myVar_intIndex] if myVar_intIndex < len(myCon_listStrQueryTitles) else f"Result {myVar_intIndex + 1}"
                 # Generate Overview Chart
                 if (myVar_intIndex == 1 and len(myVar_listPdDataframesResults) >= 6 and
                     not myVar_listPdDataframesResults[2].empty and not myVar_listPdDataframesResults[3].empty and
                     not myVar_listPdDataframesResults[5].empty):
                     myVar_pdDataframeInventory = myVar_listPdDataframesResults[2]
                     myVar_pdDataframeUsageVendor = myVar_listPdDataframesResults[3]
                     myVar_pdDataframeExtra = myVar_listPdDataframesResults[5]
                     myVar_floatOnhand=fun_safeFloat(myVar_pdDataframeInventory,"OnHand"); myVar_floatReserved=fun_safeFloat(myVar_pdDataframeInventory,"Rsrv"); myVar_floatAvailable=fun_safeFloat(myVar_pdDataframeInventory,"Available Inv"); myVar_floatRemnants=fun_safeFloat(myVar_pdDataframeExtra,"remnants"); myVar_floatOnpo=fun_safeFloat(myVar_pdDataframeExtra,"OnPO"); myVar_floatConwk=fun_safeFloat(myVar_pdDataframeUsageVendor,"con/wk")
                     myVar_listStrMetricLabels=["OnHand","Reserved","Available","Remnants","OnPO","- Usage/Wk","Avg Usage (26 Wk)"]; myVar_listFloatMetricValues=[myVar_floatOnhand,-myVar_floatReserved,myVar_floatAvailable,myVar_floatRemnants,myVar_floatOnpo,-myVar_floatConwk if myVar_floatConwk is not None else 0, -(myVar_floatConwk * 26) if myVar_floatConwk is not None else 0]
                     myVar_pdDataframeChartData=Com_pd.DataFrame({"Metric":myVar_listStrMetricLabels,"Value":myVar_listFloatMetricValues})
                     Com_st.subheader(f"🌍 Item {myVar_intItemIdToUse} Overview Chart")
                     myVar_altChartItemOverview=Com_alt.Chart(myVar_pdDataframeChartData).mark_bar().encode(x=Com_alt.X("Metric",title="Metric",sort=myVar_listStrMetricLabels),y=Com_alt.Y("Value",title="Feet",scale=Com_alt.Scale(zero=True)),color=Com_alt.Color("Metric",legend=None),tooltip=["Metric","Value"]).properties(width=700,height=350)
                     Com_st.altair_chart(myVar_altChartItemOverview, use_container_width=True)

                 # Format and Display Table
                 Com_st.subheader(myVar_strResultTitle)
                 try:
                     if myVar_strResultTitle == "🧪 Inventory + PO":
                         if "New Depletion Date" in myVar_pdDataframeCurrentResult.columns: myVar_pdDataframeCurrentResult["New Depletion Date"] = Com_pd.to_datetime(myVar_pdDataframeCurrentResult["New Depletion Date"], errors='coerce').dt.date
                     elif myVar_strResultTitle == "🧪 Purchase Orders":
                         if "Due Date" in myVar_pdDataframeCurrentResult.columns: myVar_pdDataframeCurrentResult["Due Date"] = Com_pd.to_datetime(myVar_pdDataframeCurrentResult["Due Date"].astype(str), format="%Y%m%d", errors="coerce").dt.date
                         if "Received" in myVar_pdDataframeCurrentResult.columns: myVar_pdDataframeCurrentResult["Received"] = Com_pd.to_datetime(myVar_pdDataframeCurrentResult["Received"].astype(str), format="%Y%m%d", errors='coerce').dt.date
                         if "Ordered" in myVar_pdDataframeCurrentResult.columns: myVar_pdDataframeCurrentResult["Ordered"] = myVar_pdDataframeCurrentResult["Ordered"].apply(lambda x: f"{x:,.0f}" if Com_pd.notnull(x) and isinstance(x, (int, float)) else "")
                     elif myVar_strResultTitle == "🧪 Family Breakdown (if any)":
                         if "total_usage" in myVar_pdDataframeCurrentResult.columns: myVar_pdDataframeCurrentResult["total_usage"] = myVar_pdDataframeCurrentResult["total_usage"].apply(lambda x: f"{x:,.2f}" if Com_pd.notnull(x) and isinstance(x, (int, float)) else "")
                         if "wk use" in myVar_pdDataframeCurrentResult.columns: myVar_pdDataframeCurrentResult["wk use"] = myVar_pdDataframeCurrentResult["wk use"].apply(lambda x: f"{x:,.2f}" if Com_pd.notnull(x) and isinstance(x, (int, float)) else "")
                     Com_st.dataframe(myVar_pdDataframeCurrentResult)
                 except KeyError as myVar_keyErr: Com_st.warning(f"Fmt Skip: Col {myVar_keyErr}"); Com_st.dataframe(myVar_pdDataframeCurrentResult)
                 except Exception as myVar_fmtErr: Com_st.warning(f"Fmt Err: {myVar_fmtErr}"); Com_st.dataframe(myVar_pdDataframeCurrentResult)

        except Exception as myVar_errReport:
            Com_st.error(f"❌ Failed to run report for item {myVar_intItemIdToUse}: {myVar_errReport}")
            Com_st.code(traceback.format_exc())

    # Control Block: This case happens if parameter was None AND user input was blank or invalid
    elif myPar_intItemId is None:
        # Only show the prompt message if we actually asked the user (parameter was None)
        # and they haven't provided valid input yet.
        Com_st.info("👆 Please enter a valid numeric Item ID above.")

    # Control Block: This case handles if a parameter was passed but was invalid (e.g., text)
    # The error message was already shown inside the conversion try-except block above.
    # else: # (myVar_intItemIdToUse is None but myPar_intItemId was not None)
    #    pass # Error already displayed during the conversion attempt


#==============================================================================
# ================== SECTION 1: MAIN DASHBOARD DISPLAY =======================
#==============================================================================
# Note before the subprocedure:
# This is the main function for the ROP Dashboard page. It loads data,
# displays summaries, filters, charts, tables, and the item report trigger.
def sub_displayMainDashboardView(myPar_objDbEngine):
    """
    Loads data and displays the primary ROP inventory dashboard view.

    Variables Used:
        - myPar_objDbEngine (SQLAlchemy Engine): Database engine passed from caller.
    Variables Returned:
        - None (Displays UI directly).
    """
    # --- Local Variables ---
    # myVar_pdDataFrameRopData: The main processed ROP data.
    # myVar_pdDataFrameRawData: Raw data loaded from DB.
    # myVar_objDbConnection: DB connection.
    # myVar_errLoad: Exception object.
    # myVar_col1, myVar_col2, ...: Layout columns.
    # myVar_intTotalActive, ...: Summary metrics.
    # myVar_listOptionsReorder, ... myVar_listReorderFilter, ...: Filter variables.
    # myVar_pdDataFrameFilteredData: Filtered data.
    # myVar_altSelectionHighlight, myVar_altChartInventory: Altair objects.
    # myVar_listAllColumns, myVar_listDefaultColumns: Table column config.
    # myVar_strItemIdInput: Item ID from text input (string).
    # myVar_objException: General exception object.

    # --- Initialize Session State ---
    # Control block: Initialize session state if needed for this page.
    if "selected_item" not in Com_st.session_state:
        Com_st.session_state.selected_item = "50002" # Default item

    # --- Load and Prepare Data ---
    myVar_pdDataFrameRopData = None # Initialize
    try:
        Com_st.write("Reading ROP Data...") # Progress indicator
        with myPar_objDbEngine.begin() as myVar_objDbConnection:
            myVar_pdDataFrameRawData = Com_pd.read_sql("SELECT * FROM e_ROPData", myVar_objDbConnection)

        # --- Data Processing ---
        if not myVar_pdDataFrameRawData.empty:
            myVar_pdDataFrameRopData = myVar_pdDataFrameRawData.rename(columns={
                "OnHand": "In Stock (ft)", "OnPO": "PO Incoming (ft)",
                "lbs/ft": "Pounds per", "con/wk": "Usage/Week", "FastPathSort": "Grade"
            })
            num_cols = ['In Stock (ft)', 'PO Incoming (ft)', 'Usage/Week']
            for col in num_cols:
                if col in myVar_pdDataFrameRopData.columns:
                    myVar_pdDataFrameRopData[col] = Com_pd.to_numeric(myVar_pdDataFrameRopData[col], errors='coerce')
                else:
                    myVar_pdDataFrameRopData[col] = 0.0 # Assign default if column missing
            # Drop rows where essential numeric conversions failed or usage is missing
            myVar_pdDataFrameRopData = myVar_pdDataFrameRopData.dropna(subset=['Usage/Week', 'In Stock (ft)'])

            # --- Feature Engineering ---
            if not myVar_pdDataFrameRopData.empty:
                mask_usage_positive = myVar_pdDataFrameRopData['Usage/Week'] > 0
                myVar_pdDataFrameRopData['Weeks Left'] = 999.0 # Default large value
                # Calculate only where usage is positive
                myVar_pdDataFrameRopData.loc[mask_usage_positive, 'Weeks Left'] = (myVar_pdDataFrameRopData.loc[mask_usage_positive, 'In Stock (ft)'] / myVar_pdDataFrameRopData.loc[mask_usage_positive, 'Usage/Week']).round(1)
                myVar_pdDataFrameRopData["Reorder Flag"] = myVar_pdDataFrameRopData["Weeks Left"].apply(lambda w: "✅ No" if w > 26 else ("⚠️ Caution" if 12 < w <= 26 else "❌ Yes"))
                myVar_pdDataFrameRopData["Origin"] = myVar_pdDataFrameRopData["Description"].apply(lambda x: "China" if isinstance(x, str) and "++" in x else "Other")
                # Use Com_pd alias here for consistency within this module
                myVar_pdDataFrameRopData["Item Status"] = myVar_pdDataFrameRopData["Usage/Week"].apply(lambda x: "Active" if Com_pd.notnull(x) and x > 0 else "Inactive")
                Com_st.write("✓ ROP Data Processed.")
            else:
                Com_st.warning("⚠️ No valid data remaining after cleaning.")
                myVar_pdDataFrameRopData = None # Ensure it's None if processing fails
        else:
            Com_st.warning("⚠️ No data found in e_ROPData table.")
            myVar_pdDataFrameRopData = None # Ensure it's None if load fails

    except Exception as myVar_errLoad:
        Com_st.error(f"❌ Error loading/processing ROP data: {myVar_errLoad}")
        Com_st.code(traceback.format_exc())
        myVar_pdDataFrameRopData = None # Ensure it's None on error

    # --- Display Dashboard UI (only if data is available) ---
    # Control block: Check if data loading/processing was successful.
    if myVar_pdDataFrameRopData is not None:
        # Summary Metrics Display
        Com_st.write("## Summary Metrics")
        myVar_col1, myVar_col2, myVar_col3 = Com_st.columns(3)
        myVar_intTotalActive = len(myVar_pdDataFrameRopData)
        myVar_intItemsBelow12Wk = int((myVar_pdDataFrameRopData['Weeks Left'] < 12).sum())
        # Calculate average excluding the default large value
        myVar_floatAvgWeeksLeft = myVar_pdDataFrameRopData['Weeks Left'][myVar_pdDataFrameRopData['Weeks Left'] != 999.0].mean()
        myVar_col1.metric("Total Active Items", f"{myVar_intTotalActive:,}")
        myVar_col2.metric("Items < 12 Weeks", f"{myVar_intItemsBelow12Wk:,}")
        myVar_col3.metric("Avg Inv Weeks Left", f"{myVar_floatAvgWeeksLeft:,.1f}" if Com_pd.notnull(myVar_floatAvgWeeksLeft) else "N/A")
        myVar_col4, myVar_col5 = Com_st.columns(2)
        myVar_floatTotalOnHand = myVar_pdDataFrameRopData['In Stock (ft)'].sum()
        myVar_floatTotalOnPO = myVar_pdDataFrameRopData['PO Incoming (ft)'].sum()
        myVar_col4.metric("Feet On Hand", f"{myVar_floatTotalOnHand:,.0f}")
        myVar_col5.metric("PO Feet In Transit", f"{myVar_floatTotalOnPO:,.0f}")
        Com_st.markdown("---")

        # FILTERS
        with Com_st.expander("🔍 Filter Options", expanded=False):
            myVar_listOptionsReorder = sorted(myVar_pdDataFrameRopData["Reorder Flag"].dropna().unique().tolist())
            myVar_listReorderFilter = Com_st.multiselect("Reorder Flag", options=myVar_listOptionsReorder, default=myVar_listOptionsReorder)
            myVar_strVndrCol = "Vndr"
            if myVar_strVndrCol in myVar_pdDataFrameRopData.columns:
                 myVar_listOptionsType = sorted(myVar_pdDataFrameRopData[myVar_strVndrCol].dropna().unique().tolist())
                 myVar_listTypeFilter = Com_st.multiselect("Vendor", options=myVar_listOptionsType, default=myVar_listOptionsType)
            else: Com_st.caption("(Vendor filter not available)"); myVar_listTypeFilter = []
            myVar_listOptionsStatus = sorted(myVar_pdDataFrameRopData["Item Status"].dropna().unique().tolist())
            myVar_listStatusFilter = Com_st.multiselect("Item Status", options=myVar_listOptionsStatus, default=myVar_listOptionsStatus)

        # Apply filters
        myVar_pdDataFrameFilteredData = myVar_pdDataFrameRopData.copy()
        if myVar_listReorderFilter: myVar_pdDataFrameFilteredData = myVar_pdDataFrameFilteredData[myVar_pdDataFrameFilteredData["Reorder Flag"].isin(myVar_listReorderFilter)]
        if myVar_strVndrCol in myVar_pdDataFrameFilteredData.columns and myVar_listTypeFilter: myVar_pdDataFrameFilteredData = myVar_pdDataFrameFilteredData[myVar_pdDataFrameFilteredData[myVar_strVndrCol].isin(myVar_listTypeFilter)]
        if myVar_listStatusFilter: myVar_pdDataFrameFilteredData = myVar_pdDataFrameFilteredData[myVar_pdDataFrameFilteredData["Item Status"].isin(myVar_listStatusFilter)]
        Com_st.write(f"Displaying **{len(myVar_pdDataFrameFilteredData)}** items after filtering.")
        Com_st.markdown("---")

        # INTERACTIVE ALTAIR CHART
        Com_st.write("## Inventory Weeks Left (Interactive)")
        myVar_altSelectionHighlight = Com_alt.selection_single(on='mouseover', fields=['Item'], nearest=True)
        # Calculate max weeks for scale, excluding potential default large value
        finite_weeks_filt = myVar_pdDataFrameFilteredData.loc[myVar_pdDataFrameFilteredData['Weeks Left'] != 999.0, 'Weeks Left']
        max_weeks_scale = 52 if finite_weeks_filt.empty else max(52, finite_weeks_filt.max() * 1.1) # Default scale min 52 weeks

        myVar_altChartInventory = Com_alt.Chart(myVar_pdDataFrameFilteredData).mark_bar().encode(
            x=Com_alt.X("Item:N", sort='-y', title="Item"),
            y=Com_alt.Y("Weeks Left:Q", title="Weeks Left", scale=Com_alt.Scale(domain=[0, max_weeks_scale])),
            color=Com_alt.Color("Reorder Flag:N", scale=Com_alt.Scale(domain=["❌ Yes", "⚠️ Caution", "✅ No"], range=["#e45756", "#f5a623", "#54a24b"]), legend=Com_alt.Legend(title="Reorder Flag")),
            tooltip=["Item", "Description", "Weeks Left", "Reorder Flag", "In Stock (ft)", "Usage/Week"]
        ).add_selection(myVar_altSelectionHighlight).properties(height=400).interactive()
        Com_st.altair_chart(myVar_altChartInventory, use_container_width=True)
        Com_st.markdown("---")

        # INTERACTIVE TABLE
        Com_st.write("## Full Inventory Data (Filtered & Sorted)")
        myVar_pdDataFrameFilteredData_display = myVar_pdDataFrameFilteredData.sort_values(by=["Weeks Left"], ascending=[True])
        myVar_listAllColumns = list(myVar_pdDataFrameFilteredData_display.columns)
        myVar_listDefaultColumns = [myVar_col for myVar_col in ["Item", "Reorder Flag", "Weeks Left", "In Stock (ft)", "Rsrv", "PO Incoming (ft)", "Usage/Week", "Level", "TotCons", "Size Text", "Description", "Vndr", "$/ft", "Grade", "Origin", "Item Status", "Comment"] if myVar_col in myVar_listAllColumns]
        Com_st.dataframe(myVar_pdDataFrameFilteredData_display[myVar_listDefaultColumns])
        Com_st.markdown("---")

        # .........................................................................................
        # REPORT BY ITEM BUTTON / TRIGGER SECTION
        # .........................................................................................
        Com_st.write("## Detailed Report by Item")
        # Text input uses session state for default value
        myVar_strItemIdInput = Com_st.text_input(
            "Enter Item Number for Detailed Report:",
            value=Com_st.session_state.get("selected_item", "50002"),
            key="item_id_input_dashboard_page" # Unique key
        )
        # Control block: Button click triggers the item report subprocedure
        if Com_st.button(f"Generate Report for Item {myVar_strItemIdInput}", key="generate_report_button_dashboard_page"):
            # Pass the *string* from text input to the subprocedure
            # The subprocedure `sub_displayItemReport` will handle validation and conversion
            sub_displayItemReport(myPar_objDbEngine, myVar_strItemIdInput)
            # Note: No explicit error checking needed here for digit because sub_displayItemReport handles it

    else:
        # Handles case where initial data load failed
        Com_st.error("❌ Dashboard cannot be displayed. Failed to load initial ROP data.")

    # --- Update Session State from URL ---
    # Needs to be outside the "if myVar_pdDataFrameRopData is not None" block
    # so it can potentially update the default text input value even if data load fails
    myVar_dictQueryParams = Com_st.query_params
    if "selected_item" in myVar_dictQueryParams:
        if Com_st.session_state.get("selected_item") != myVar_dictQueryParams["selected_item"]: # Use .get for safety
            Com_st.session_state.selected_item = myVar_dictQueryParams["selected_item"]
            # Com_st.rerun() # Optional: uncomment if you want immediate update

# ============================================================================
# ⚠️ LOCAL TESTING BLOCK (No changes needed here from previous version)
# ============================================================================
if __name__ == "__main__":
    Com_st.sidebar.warning("Running p03_Dashboard in Local Test Mode")
    # --- Create a LOCAL engine instance FOR TESTING ONLY ---
    myCon_strLclServer = "database-3.c67ymu6q22o1.us-east-1.rds.amazonaws.com"
    myCon_strLclDatabase = "SigmaTB"
    myCon_strLclUser = "admin"
    myCon_strLclPassword = "Er1c41234$" # Use secure method if possible

    myVar_objTestDbEngine = None
    try:
        # Updated connection string to use SQLAlchemy with pymssql driver
        myCon_strTestConnectionString = f"mssql+pytds://{myCon_strLclUser}:{myCon_strLclPassword}@{myCon_strLclServer}:1433/{myCon_strLclDatabase}"
        myVar_objTestDbEngine = create_engine(myCon_strTestConnectionString)
        with myVar_objTestDbEngine.connect() as myVar_objTestDbConnection:
             Com_st.sidebar.success("🔌 Local Test DB Connected.")
    except Exception as myVar_objTestEngErr:
        Com_st.error(f"❌ Failed to create Local Test DB Engine: {myVar_objTestEngErr}")
        Com_st.stop()

    # --- Run the main display function with the test engine ---
    if myVar_objTestDbEngine:
        # Call the main display function directly now
        sub_displayMainDashboardView(myVar_objTestDbEngine)
    else:
        Com_st.error("Test execution stopped due to DB connection failure.")

# ============================================================================
#  EOF
# ============================================================================