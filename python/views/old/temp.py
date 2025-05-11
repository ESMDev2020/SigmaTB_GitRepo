import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import altair as alt
from sqlalchemy import create_engine

# ---------- Titles for each query result ----------
query_titles = [
    "🔍 Item Being Reviewed",
    "📈 IA / MP / SO Summary (Last 13 Months)",
    "📦 Inventory On Hand vs Reserved",
    "🔪 Usage and Vendor",
    "🗓 Depletion Forecast",
    "🧪 Inventory + PO",
    "🧪 Purchase Orders",
    "🧪 Family Breakdown (if any)"
]

# ---------- Database connection ----------
server = "database-3.c67ymu6q22o1.us-east-1.rds.amazonaws.com"
database = "SigmaTB"
username = "admin"
password = "Er1c41234$"
engine = create_engine(f"mssql+pytds://{username}:{password}@{server}:1433/{database}")

# ---------- SESSION STATE for interactive item click ----------
if "selected_item" not in st.session_state:
    st.session_state.selected_item = "50002"

# ---------- DASHBOARD TOP SECTION ----------
st.title("📊 Inventory Dashboard")

# .........................................................................................
# LOAD INVENTORY DATA
# .........................................................................................
try:
    with engine.begin() as conn:
        myDataFrame = pd.read_sql("SELECT * FROM e_ROPData", conn)

    myDataFrame = myDataFrame.rename(columns={
        "OnHand": "In Stock (ft)",
        "OnPO": "PO Incoming (ft)",
        "lbs/ft": "Pounds per",
        "con/wk": "Usage/Week",
        "FastPathSort": "Grade"
    })

    # Filter only for items with non-null Usage/Week (don't exclude inactive yet)
    myDataFrame = myDataFrame[myDataFrame["Usage/Week"].notnull()]
    myDataFrame["Weeks Left"] = (myDataFrame["In Stock (ft)"].astype(float) / myDataFrame["Usage/Week"].astype(float)).round(1)

    myDataFrame["Reorder Flag"] = myDataFrame["Weeks Left"].apply(
        lambda w: "✅ No" if w > 26 else ("⚠️ Caution" if 12 < w <= 26 else "❌ Yes")
    )

    myDataFrame["Origin"] = myDataFrame["Description"].apply(lambda x: "China" if "++" in str(x) else "Other")

    # ➕ NEW: Active vs Inactive classification
    myDataFrame["Item Status"] = myDataFrame["Usage/Week"].apply(lambda x: "Active" if pd.notnull(x) and x > 0 else "Inactive")

    # Summary tiles
    st.write("## Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Active Items", f"{int(len(myDataFrame)):,}")
    col2.metric("Items < 12 Weeks", f"{int((myDataFrame['Weeks Left'] < 12).sum()):,}")
    col3.metric("Avg Inv Weeks Left", f"{myDataFrame['Weeks Left'].astype(float).mean():,.1f}")

    col4, col5 = st.columns(2)
    col4.metric("Feet On Hand", f"{myDataFrame['In Stock (ft)'].astype(float).sum():,.0f}")
    col5.metric("PO Feet In Transit", f"{myDataFrame['PO Incoming (ft)'].astype(float).sum():,.0f}")

    # .........................................................................................
    # FILTERS
    # .........................................................................................
    with st.expander("🔍 Filter Options", expanded=False):
        reorder_filter = st.multiselect(
            "Reorder Flag",
            options=sorted(myDataFrame["Reorder Flag"].dropna().unique().tolist()),
            default=sorted(myDataFrame["Reorder Flag"].dropna().unique().tolist())
        )
        type_filter = st.multiselect(
            "Type" if "Vndr" in myDataFrame.columns else "(Type not available)",
            options=sorted(myDataFrame["Vndr"].dropna().unique().tolist()) if "Vndr" in myDataFrame.columns else [],
            default=sorted(myDataFrame["Vndr"].dropna().unique().tolist()) if "Vndr" in myDataFrame.columns else []
        )
        status_filter = st.multiselect(
            "Item Status",
            options=sorted(myDataFrame["Item Status"].dropna().unique().tolist()),
            default=sorted(myDataFrame["Item Status"].dropna().unique().tolist())
        )

    filtered_myDataFrame = myDataFrame.copy()
    if reorder_filter:
        filtered_myDataFrame = filtered_myDataFrame[filtered_myDataFrame["Reorder Flag"].isin(reorder_filter)]
    if "Vndr" in filtered_myDataFrame.columns and type_filter:
        filtered_myDataFrame = filtered_myDataFrame[filtered_myDataFrame["Vndr"].isin(type_filter)]
    if status_filter:
        filtered_myDataFrame = filtered_myDataFrame[filtered_myDataFrame["Item Status"].isin(status_filter)]

    st.write(f"Displaying {len(filtered_myDataFrame)} items")

    # .........................................................................................
    # BEAUTIFUL INTERACTIVE ALTAIR CHART FOR INVENTORY WEEKS
    # .........................................................................................
    highlight = alt.selection_single(on='mouseover', fields=['Item'], nearest=True)

    alt_chart = alt.Chart(filtered_myDataFrame).mark_bar().encode(
        x=alt.X("Item:N", sort='-y', title="Item"),
        y=alt.Y("Weeks Left:Q", title="Weeks Left"),
        color=alt.Color("Reorder Flag:N",
                        scale=alt.Scale(domain=["❌ Yes", "⚠️ Caution", "✅ No"],
                                        range=["red", "orange", "green"]),
                        legend=alt.Legend(title="Reorder Flag")),
        tooltip=["Item", "Weeks Left", "Reorder Flag"]
    ).add_selection(
        highlight
    ).properties(
        width='container', height=400
    ).interactive()

    st.altair_chart(alt_chart, use_container_width=True)

    # .........................................................................................
    #  INTERACTIVE TABLE
    # .........................................................................................
    st.write("## Full Inventory Data (Based on Filters Above)")

    # Sort the table: "In Stock" ascending, "Usage/Week" descending
    filtered_myDataFrame = filtered_myDataFrame.sort_values(
        by=["In Stock (ft)", "Usage/Week"], ascending=[True, False]
    )

    all_columns = list(filtered_myDataFrame.columns)
    default_columns = [col for col in [
        "Item", "In Stock (ft)", "Rsrv", "Level", "Weeks Left", "Reorder Flag",
        "PO Incoming (ft)", "TotCons", "Usage/Week", "Size Text", "Description",
        "Vndr", "Comment", "$/ft", "Origin", "Item Status"
    ] if col in all_columns]

    st.dataframe(filtered_myDataFrame[default_columns])

    # .........................................................................................
    # REPORT BY ITEM BUTTON
    # .........................................................................................
    item_id = st.text_input("Enter Item Number", value=st.session_state.selected_item)
    if st.button("Report by ITEM"):
        try:
            full_report_query = f"""
                SELECT [Size Text], Description, SMO FROM e_ROPData WHERE Item = {item_id};

                WITH Months AS (
                    SELECT FORMAT(DATEADD(MONTH, -n, CAST(GETDATE() AS DATE)), 'yyyy-MM') AS Month
                    FROM (SELECT TOP 13 ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) - 1 AS n FROM sys.all_objects) AS x
                ),
                Aggregated AS (
                    SELECT
                        FORMAT(DATEFROMPARTS(2000 + IHTRYY, IHTRMM, 1), 'yyyy-MM') AS Month,
                        CASE WHEN CONVERT(VARCHAR(10), IHTRNT) = 'IA' THEN IHTQTY
                                WHEN CONVERT(VARCHAR(10), IHTRNT) IN ('OW', 'OR') THEN IHTQTY
                                WHEN CONVERT(VARCHAR(10), IHTRNT) = 'IN' THEN IHTQTY
                                ELSE 0 END AS Qty,
                        CONVERT(VARCHAR(10), IHTRNT) AS Type
                    FROM e_usagedata
                    WHERE IHITEM = {item_id}
                        AND DATEFROMPARTS(2000 + IHTRYY, IHTRMM, 1) >= DATEADD(MONTH, -13, CAST(GETDATE() AS DATE))
                )
                SELECT
                    m.Month,
                    CASE WHEN SUM(CASE WHEN a.Type = 'IA' THEN a.Qty ELSE 0 END) = 0 THEN '-' ELSE FORMAT(SUM(CASE WHEN a.Type = 'IA' THEN a.Qty ELSE 0 END), 'N2') END AS [IA (Inventory Adjustments)],
                    CASE WHEN SUM(CASE WHEN a.Type IN ('OW', 'OR') THEN a.Qty ELSE 0 END) = 0 THEN '-' ELSE FORMAT(SUM(CASE WHEN a.Type IN ('OW', 'OR') THEN a.Qty ELSE 0 END), 'N2') END AS [MP (Material Processed)],
                    CASE WHEN SUM(CASE WHEN a.Type = 'IN' THEN a.Qty ELSE 0 END) = 0 THEN '-' ELSE FORMAT(SUM(CASE WHEN a.Type = 'IN' THEN a.Qty ELSE 0 END), 'N2') END AS [SO (Sales Orders)]
                FROM Months m
                LEFT JOIN Aggregated a ON m.Month = a.Month
                GROUP BY m.Month
                ORDER BY m.Month;

                SELECT [OnHand], [Rsrv], [OnHand] - [Rsrv] AS [Available Inv] FROM e_ROPData WHERE Item = {item_id};

                SELECT 'Usage and Vendor' AS [Title], [#/ft], [UOM], [$/ft], [con/wk], [Vndr] FROM e_ROPData WHERE Item = {item_id};

                SELECT 'When and how much' AS [Question],
                    [OnHand] - [Rsrv] AS [Available Inv],
                    ([#/ft] * ([OnHand] - [Rsrv])) AS [Pounds],
                    [$/ft] * ([OnHand] - [Rsrv]) AS [Dollars],
                    ([OnHand] - [Rsrv]) / [con/wk] AS [Weeks],
                    DATEADD(WEEK, ([OnHand] - [Rsrv]) / [con/wk], CAST(GETDATE() AS DATE)) AS [Expected Depletion Date]
                FROM e_ROPData WHERE Item = {item_id};

                SELECT
                    CASE 
                        WHEN ISNUMERIC(REPLACE(REPLACE(e_ROPData.[OnPO], ',', ''), ' ', '')) = 1 
                        THEN CAST(REPLACE(REPLACE(e_ROPData.[OnPO], ',', ''), ' ', '') AS FLOAT) 
                        ELSE NULL 
                    END AS [OnPO],
                    e_TagData.remnants,
                    e_ROPData.[Level],
                    CASE 
                        WHEN ISNUMERIC(REPLACE(REPLACE(e_ROPData.[OnPO], ',', ''), ' ', '')) = 1 
                        THEN CAST(REPLACE(REPLACE(e_ROPData.[OnPO], ',', ''), ' ', '') AS FLOAT) 
                        ELSE NULL 
                    END / NULLIF(
                        CASE 
                            WHEN ISNUMERIC(REPLACE(REPLACE(e_ROPData.[con/wk], ',', ''), ' ', '')) = 1 
                            THEN CAST(REPLACE(REPLACE(e_ROPData.[con/wk], ',', ''), ' ', '') AS FLOAT) 
                            ELSE NULL 
                        END, 0
                    ) AS [PO Weeks],
                    DATEADD(
                        WEEK,
                        (
                            CASE 
                                WHEN ISNUMERIC(REPLACE(REPLACE(e_ROPData.[OnHand], ',', ''), ' ', '')) = 1 
                                THEN CAST(REPLACE(REPLACE(e_ROPData.[OnHand], ',', ''), ' ', '') AS FLOAT) 
                                ELSE NULL 
                            END
                            - CASE 
                                WHEN ISNUMERIC(REPLACE(REPLACE(e_ROPData.[Rsrv], ',', ''), ' ', '')) = 1 
                                THEN CAST(REPLACE(REPLACE(e_ROPData.[Rsrv], ',', ''), ' ', '') AS FLOAT) 
                                ELSE NULL 
                            END
                            + CASE 
                                WHEN ISNUMERIC(REPLACE(REPLACE(e_ROPData.[OnPO], ',', ''), ' ', '')) = 1 
                                THEN CAST(REPLACE(REPLACE(e_ROPData.[OnPO], ',', ''), ' ', '') AS FLOAT) 
                                ELSE NULL 
                            END
                        ) / NULLIF(
                            CASE 
                                WHEN ISNUMERIC(REPLACE(REPLACE(e_ROPData.[con/wk], ',', ''), ' ', '')) = 1 
                                THEN CAST(REPLACE(REPLACE(e_ROPData.[con/wk], ',', ''), ' ', '') AS FLOAT) 
                                ELSE NULL 
                            END, 0
                        ),
                        GETDATE()
                    ) AS [New Depletion Date]
                FROM
                    e_ROPData
                LEFT JOIN
                    e_TagData ON e_ROPData.Item = e_TagData.item
                WHERE
                    e_ROPData.Item = {item_id};

                SELECT e_POData.due, e_POData.[Due Date], e_POData.Vendor, e_POData.PO, e_POData.Ordered, e_POData.Received
                FROM e_POData WHERE e_POData.Item = {item_id};

                SELECT
                    r.Item,
                    (r.OnHand - r.Rsrv) AS [Available],
                    r.OnPO,
                    r.[#/ft],
                    r.[#/ft] + COALESCE(us.total_usage, 0) AS net_consumption,
                    (r.TotCons / 26.1428571428571) AS [wk use],
                    us.total_usage,
                    r.description,
                    r.[Size Text] as "Size"
                FROM
                    e_ROPData r
                LEFT JOIN (
                    SELECT
                        IHITEM,
                        SUM(IHTQTY) AS total_usage
                    FROM
                        e_usagedata
                    WHERE
                        e_usagedata.IHITEM = e_usagedata.column4  -- Corrected join condition
                    GROUP BY
                        IHITEM
                ) us ON r.Item = us.IHITEM
                WHERE r.Item = {item_id};
            """

            result_sets = []
            with engine.begin() as conn:
                for sql in full_report_query.strip().split(";"):
                    if sql.strip():
                        df = pd.read_sql(sql.strip(), conn)
                        result_sets.append(df)

            st.success("✅ All data loaded successfully!")

            # .........................................................................................
            # CONSUMPTION CHART
            # .........................................................................................

            for i, df in enumerate(result_sets):
                title = query_titles[i] if i < len(query_titles) else f"Result {i + 1}"

                # 👉 Render chart before table 1 ("📈 IA / MP / SO Summary")
                if i == 1 and len(result_sets) >= 4 and not result_sets[2].empty and not result_sets[3].empty:
                    inventory_df = result_sets[2]  # Inventory On Hand vs Reserved
                    usage_vendor_df = result_sets[3]  # Usage and Vendor
                    extra_data = result_sets[5] if len(result_sets) > 5 else pd.DataFrame()

                    def safe_float(df, col, default=0):
                        try:
                            value = df.at[0, col]
                            return float(value) if pd.notnull(value) else default
                        except Exception:
                            return default

                    onhand = safe_float(inventory_df, "OnHand")
                    reserved = safe_float(inventory_df, "Rsrv")
                    available = safe_float(inventory_df, "Available Inv")
                    remnants = safe_float(extra_data, "remnants")
                    onpo = safe_float(extra_data, "OnPO")
                    conwk = safe_float(usage_vendor_df, "con/wk")

                    metric_labels = ["OnHand", "Reserved", "Available", "Remnants", "OnPO", "- con/wk", "Avg Cons x 26 Weeks"]
                    metric_values = [onhand, -reserved, available, remnants, onpo, -conwk, -(conwk * 26)]

                    chart_data = pd.DataFrame({"Metric": metric_labels, "Value": metric_values})
                    st.subheader(f"🌍 Item {item_id} Overview Chart")
                    bar_chart = alt.Chart(chart_data).mark_bar().encode(
                        x=alt.X("Metric", title="Metric", sort=metric_labels),
                        y=alt.Y("Value", title="Feet", scale=alt.Scale(zero=True)),
                        color=alt.Color("Metric", legend=None)
                    ).properties(width=700, height=350)
                    st.altair_chart(bar_chart)

                # .........................................................................................
                # WE FORMAT THE TABLES
                # .........................................................................................
                # Then display the title and table
                st.subheader(title)

                if title == "🧪 Inventory + PO":
                    df["New Depletion Date"] = pd.to_datetime(df["New Depletion Date"]).dt.date

                elif title == "🧪 Purchase Orders":
                    df["Due Date"] = pd.to_datetime(df["Due Date"].astype(str), format="%Y%m%d", errors="coerce").dt.date
                    df["Received"] = pd.to_datetime(df["Received"].astype(str), format="%Y%m%d", errors='coerce').dt.date
                    df["Ordered"] = df["Ordered"].apply(lambda x: f"{x:,.0f}" if pd.notnull(x) else "")

                elif title == "🧪 Family Breakdown (if any)":
                    if "net_consumption" in df.columns:
                        df["net_consumption"] = df["net_consumption"].apply(lambda x: f"{x:,.0f}")
                    if "wk use" in df.columns:
                        df["wk use"] = df["wk use"].apply(lambda x: f"{x:,.2f}")
                    if "total_usage" in df.columns:
                        df["total_usage"] = df["total_usage"].apply(lambda x: f"{x:,.2f}")

                st.dataframe(df)

        except Exception as e:
            st.error(f"❌ Failed to run the report: {e}")

except Exception as e:
    st.error(f"❌ Failed to load dashboard: {e}")

# Update item_id from hyperlink if clicked
query_params = st.query_params
if "selected_item" in query_params:
    st.session_state.selected_item = query_params["selected_item"]