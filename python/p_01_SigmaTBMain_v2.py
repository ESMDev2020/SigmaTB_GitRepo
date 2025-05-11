# ════════════════════════════════════════════════════════════════════════════
# 📊 STREAMLIT MAIN APP - SIGMA DASHBOARD
# DESCRIPTION:
#   This script builds the main entry point for the Sigma Dashboard.
#   It manages the database connection and loads UI components from modular
#   files based on sidebar navigation.
#   - All variables follow: myVar_, myCon_, sub_, fun_, Com_ naming conventions
#   - Includes documentation, control logic, and error handling markers
# ════════════════════════════════════════════════════════════════════════════

# 📦 Required Imports
import streamlit as myCom_Streamlit # For UI components and caching
import pandas as Com_pandas           # Needed for DataFrame creation
import matplotlib.pyplot as myCom_plt # ****** ADDED for plotting ******
import seaborn as Com_sns             # ****** ADDED for plotting ******
from sqlalchemy import create_engine # Needed here for fun_connectToDb
from datetime import datetime
import traceback # For error details

# Import view modules containing display logic
# These modules should NOT define their own connection functions/engines anymore
try:
    from views import p_02_ROP
    from views import p_03_Dashboard #as p_03_Dashboard
    from views import p_04_DashboardCosts
    from views import p_05_StoredProcedures
except ImportError as myVar_errImport:
     myCom_Streamlit.error(f"🔴 Failed to import view modules (p_02_ROP, p_03_Dashboard, p_04_DashboardCosts): {myVar_errImport}")
     myCom_Streamlit.error("Ensure these files exist in the 'views' directory.")
     myCom_Streamlit.stop()

# ────────────────────────────────────────────────────────────────────────────
# 📜 CONSTANTS (Defined directly in the main script)
# ────────────────────────────────────────────────────────────────────────────
myCon_strDbServer = "database-3.c67ymu6q22o1.us-east-1.rds.amazonaws.com"
myCon_strDbDatabase = "SigmaTB"
myCon_strDbUsername = "admin"
myCon_strDbPassword = "Er1c41234$" # !! Use secrets !!

# ────────────────────────────────────────────────────────────────────────────
# 🧱 FUNCTIONS (Defined directly in the main script)
# ────────────────────────────────────────────────────────────────────────────
@myCom_Streamlit.cache_resource # Cache the engine object across reruns
def fun_connectToDb(myPar_strUser, myPar_strPassword, myPar_strServer, myPar_strDatabase):
    """ Creates and returns a SQLAlchemy database engine object (Cached). """
    myCom_Streamlit.write("Attempting to create DB engine...") # Log attempt
    try:
        # Changed to use sqlalchemy with pytds driver instead of pymssql
        myVar_strConnectionString = f"mssql+pytds://{myPar_strUser}:{myPar_strPassword}@{myPar_strServer}:1433/{myPar_strDatabase}"
        myVar_objDbEngine = create_engine(myVar_strConnectionString)
        with myVar_objDbEngine.connect() as myVar_objDbConnectionTest: pass
        myCom_Streamlit.write("DB engine created successfully.") # Log success
        return myVar_objDbEngine
    except Exception as myVar_objException:
        myCom_Streamlit.error(f"❌ Database Connection Error in fun_connectToDb: {myVar_objException}")
        return None

# ────────────────────────────────────────────────────────────────────────────
# ⚙️ Streamlit Page Config & Initial Setup
# ────────────────────────────────────────────────────────────────────────────
myCom_Streamlit.set_page_config(page_title="Sigma Dashboard", layout="wide")

myVar_objAppDbEngine = fun_connectToDb(
    myCon_strDbUsername, myCon_strDbPassword, myCon_strDbServer, myCon_strDbDatabase
)

if not myVar_objAppDbEngine:
     myCom_Streamlit.error("🔴 CRITICAL: Database connection failed during startup. Application cannot proceed.")
     myCom_Streamlit.stop()
else:
     myCom_Streamlit.sidebar.success("🔌 DB Connected")

myCom_Streamlit.write(f"🟢 Execution started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ────────────────────────────────────────────────────────────────────────────
# 🎨 Sidebar Interface
# ────────────────────────────────────────────────────────────────────────────
myCom_Streamlit.sidebar.image("assets/SigmaTube-Bar.jpeg", use_container_width=True)
myVar_strMainSection = myCom_Streamlit.sidebar.selectbox(
    label="📁 Main Section", options=[ "📊 Dashboard", "📦 ROP Reports", "💰 Cost Analysis", "🗄️ Stored Procedures"]
)

# ────────────────────────────────────────────────────────────────────────────
# 💡 MAIN CONTENT DISPLAY LOGIC - Based on Sidebar Selection
# ────────────────────────────────────────────────────────────────────────────

# ========================== COST ANALYSIS SECTION ===========================
if myVar_strMainSection == "💰 Cost Analysis":
    # ... (Cost Analysis code as before) ...
    myVar_strSubsection = myCom_Streamlit.sidebar.radio(
        "📂 Cost Report Type",
        ["Cost by Order", "Shipment by Order", "MP by Order", "Credit Memos (Feb Yr 25)",
         "Untransactioned Costs (Feb Yr 25)", "Sales Report (OE - Feb Yr 25)", "Sales vs GL Comparison (Feb Yr 25)"],
        key="cost_subsection_radio"
    )
    myCom_Streamlit.title(f"💰 Cost Analysis - {myVar_strSubsection}")
    myCom_Streamlit.markdown("---")
    try:
        if myVar_strSubsection == "Cost by Order": p_04_DashboardCosts.sub_displayCostByOrder(myVar_objAppDbEngine)
        elif myVar_strSubsection == "Shipment by Order": p_04_DashboardCosts.sub_displayShipmentByOrder(myVar_objAppDbEngine)
        elif myVar_strSubsection == "MP by Order": p_04_DashboardCosts.sub_displayMPByOrder(myVar_objAppDbEngine)
        elif myVar_strSubsection == "Credit Memos (Feb Yr 25)": p_04_DashboardCosts.sub_displayCreditMemos(myVar_objAppDbEngine)
        elif myVar_strSubsection == "Untransactioned Costs (Feb Yr 25)": p_04_DashboardCosts.sub_displayUntransactionedCosts(myVar_objAppDbEngine)
        elif myVar_strSubsection == "Sales Report (OE - Feb Yr 25)": p_04_DashboardCosts.sub_displaySalesReportFromOE(myVar_objAppDbEngine)
        elif myVar_strSubsection == "Sales vs GL Comparison (Feb Yr 25)": p_04_DashboardCosts.sub_compareSalesVsGL(myVar_objAppDbEngine)
    except AttributeError as myVar_errAttr: myCom_Streamlit.error(f"🔴 Error calling function for '{myVar_strSubsection}' in Cost Analysis: {myVar_errAttr}")
    except Exception as myVar_errGeneral: myCom_Streamlit.error(f"🔴 An unexpected error occurred in the Cost Analysis section: {myVar_errGeneral}"); myCom_Streamlit.code(traceback.format_exc())


# =========================== ROP REPORTS SECTION ============================
elif myVar_strMainSection == "📦 ROP Reports":
    myVar_strSubsection = myCom_Streamlit.sidebar.radio(
        "📂 ROP Subsection",
        [ "📊 Summary Dashboard Data", "🧪 Show Full ROP Table", "📦 Report by ITEM", "📊 Count ROP by Group"],
        key="rop_subsection_radio"
    )
    myCom_Streamlit.title(f"📦 ROP Reports - {myVar_strSubsection}")
    myCom_Streamlit.markdown("---")

    try:
        if myVar_strSubsection == "📊 Summary Dashboard Data":
            # Call the function which returns data
            myVar_dictSummary = p_02_ROP.get_summary_dashboard_data(myVar_objAppDbEngine)
            # Check if the function call was successful and data was returned
            if myVar_dictSummary["success"]:
                 # Display Summary Metrics
                 myCom_Streamlit.subheader("📋 Summary")
                 for myVar_strLabel, myVar_objValue in myVar_dictSummary["summary"].items():
                      myCom_Streamlit.metric(label=myVar_strLabel, value=f"{myVar_objValue:,.1f}" if isinstance(myVar_objValue, float) else f"{myVar_objValue:,}")

                 myCom_Streamlit.markdown("---") # Separator

                 # ****** ADDED DISPLAY LOGIC ******
                 # Convert full data list back to DataFrame
                 myVar_pdDataFrameFull = Com_pandas.DataFrame(myVar_dictSummary["full_data"])

                 # Check if necessary columns exist before plotting
                 myVar_listPlotCols1 = ["Grade", "Weeks Left", "Reorder Flag"]
                 if all(col in myVar_pdDataFrameFull.columns for col in myVar_listPlotCols1):
                     myCom_Streamlit.subheader("📊 Inventory Weeks by Grade")
                     # Use matplotlib object-oriented approach with st.pyplot
                     myVar_fig1, myVar_ax1 = myCom_plt.subplots(figsize=(8, 5))
                     Com_sns.barplot(data=myVar_pdDataFrameFull, x="Grade", y="Weeks Left", hue="Reorder Flag", ax=myVar_ax1)
                     myVar_ax1.set_title("Inventory Weeks by Grade")
                     myCom_plt.tight_layout()
                     myCom_Streamlit.pyplot(myVar_fig1) # Pass the figure object
                 else:
                     myCom_Streamlit.warning("Could not generate 'Weeks by Grade' plot. Missing required columns.")

                 myVar_listPlotCols2 = ["Origin"]
                 if all(col in myVar_pdDataFrameFull.columns for col in myVar_listPlotCols2):
                     myCom_Streamlit.subheader("🌍 Stock by Origin")
                     myVar_pdSeriesOriginCounts = myVar_pdDataFrameFull["Origin"].value_counts()
                     # Use matplotlib object-oriented approach with st.pyplot
                     myVar_fig2, myVar_ax2 = myCom_plt.subplots(figsize=(6, 6))
                     myVar_ax2.pie(myVar_pdSeriesOriginCounts, labels=myVar_pdSeriesOriginCounts.index, autopct='%1.1f%%', startangle=140)
                     myVar_ax2.set_ylabel('') # Remove default ylabel
                     myVar_ax2.set_title("Stock by Origin")
                     # myCom_plt.tight_layout() # Often not needed with st.pyplot managing layout
                     myCom_Streamlit.pyplot(myVar_fig2) # Pass the figure object
                 else:
                      myCom_Streamlit.warning("Could not generate 'Stock by Origin' plot. Missing required columns.")

                 myCom_Streamlit.markdown("---") # Separator
                 myCom_Streamlit.subheader("📄 Full ROP Data Table")
                 myCom_Streamlit.dataframe(myVar_pdDataFrameFull)
                 # ****** END ADDED DISPLAY LOGIC ******
            else:
                 myCom_Streamlit.error(f"Error fetching ROP Summary: {myVar_dictSummary['error']}")

        elif myVar_strSubsection == "🧪 Show Full ROP Table":
             myVar_dictTable = p_02_ROP.get_rop_table(myVar_objAppDbEngine)
             if myVar_dictTable["success"]:
                  myCom_Streamlit.subheader("Full ROP Table")
                  myCom_Streamlit.dataframe(Com_pandas.DataFrame(myVar_dictTable["data"]))
             else:
                  myCom_Streamlit.error(f"Error fetching ROP Table: {myVar_dictTable['error']}")

        elif myVar_strSubsection == "📦 Report by ITEM":
            myVar_strItemIdFromInput = myCom_Streamlit.text_input("Enter Item ID for Report:", key="rop_item_id_input")
            if myVar_strItemIdFromInput:
                myVar_dictItemReport = p_02_ROP.generate_item_report(myVar_objAppDbEngine, myVar_strItemIdFromInput)
                if myVar_dictItemReport["success"]:
                     myCom_Streamlit.success("✅ Item Report Generated!")
                     # Display the list of dataframes returned
                     for myVar_intIdx, myVar_dictData in enumerate(myVar_dictItemReport["data"]):
                         myCom_Streamlit.subheader(f"Report Section {myVar_intIdx+1}") # Generic title
                         myCom_Streamlit.dataframe(Com_pandas.DataFrame(myVar_dictData))
                else:
                     myCom_Streamlit.error(f"Error generating item report: {myVar_dictItemReport['error']}")
            else:
                myCom_Streamlit.warning("⚠️ Please enter an Item ID.")

        elif myVar_strSubsection == "📊 Count ROP by Group":
             myVar_dictCount = p_02_ROP.count_rop_by_group(myVar_objAppDbEngine)
             if myVar_dictCount["success"]:
                  myCom_Streamlit.subheader("ROP Count by Group")
                  myCom_Streamlit.dataframe(Com_pandas.DataFrame(myVar_dictCount["data"]))
             else:
                  myCom_Streamlit.error(f"Error fetching ROP Count: {myVar_dictCount['error']}")

    except AttributeError as myVar_errAttr:
         myCom_Streamlit.error(f"🔴 Error calling function for '{myVar_strSubsection}' in ROP Reports: {myVar_errAttr}")
         myCom_Streamlit.error("Ensure functions in p_02_ROP.py are defined and accept the DB engine.")
    except Exception as myVar_errGeneral:
         myCom_Streamlit.error(f"🔴 An unexpected error occurred in the ROP Reports section: {myVar_errGeneral}")
         myCom_Streamlit.code(traceback.format_exc())


# =========================== DASHBOARD SECTION ============================
elif myVar_strMainSection == "📊 Dashboard":
    myCom_Streamlit.title("📊 Dashboard") # Main title
    myCom_Streamlit.markdown("---")
    # Call the main display function from p_03_Dashboard
    try:
        # This function should handle its own internal layout/subsections if needed
        p_03_Dashboard.sub_displayMainDashboardView(myVar_objAppDbEngine)
    except AttributeError as myVar_errAttr:
         myCom_Streamlit.error(f"🔴 Error calling function for 'Dashboard': {myVar_errAttr}")
         myCom_Streamlit.error("Ensure 'sub_displayMainDashboardView(engine)' exists in p_03_Dashboard.py.")
    except Exception as myVar_errGeneral:
         myCom_Streamlit.error(f"🔴 An unexpected error occurred in the Dashboard section: {myVar_errGeneral}")
         myCom_Streamlit.code(traceback.format_exc())


elif myVar_strMainSection == "🗄️ Stored Procedures":
    try:
        # This function will handle the entire stored procedures UI
        p_05_StoredProcedures.sub_displayStoredProceduresView(myVar_objAppDbEngine)
    except AttributeError as myVar_errAttr:
         myCom_Streamlit.error(f"🔴 Error calling function for 'Stored Procedures': {myVar_errAttr}")
         myCom_Streamlit.error("Ensure 'sub_displayStoredProceduresView(engine)' exists in p_05_StoredProcedures.py.")
    except Exception as myVar_errGeneral:
         myCom_Streamlit.error(f"🔴 An unexpected error occurred in the Stored Procedures section: {myVar_errGeneral}")
         myCom_Streamlit.code(traceback.format_exc())




# ────────────────────────────────────────────────────────────────────────────
# ✅ End Execution Timestamp
# ────────────────────────────────────────────────────────────────────────────

myCom_Streamlit.write(f"✅ Finished execution check at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ============================================================================
#  EOF
# ============================================================================