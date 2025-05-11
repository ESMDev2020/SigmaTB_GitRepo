import pymssql
import streamlit as st

st.title("📦 Full Inventory Report for Item 50002")

def run_inventory_report():
    try:
        conn = pymssql.connect(
            server='database-1.cduyeeawahjc.us-east-2.rds.amazonaws.com',
            port=1433,
            user='admin',
            password='Er1c41234$',
            database='SigmaTB'
        )
        cursor = conn.cursor()
        query = """
        SELECT *
        FROM ROPData
        WHERE Item = 50002;
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        if rows:
            for row in rows:
                st.write(f"• Size: {row[0]}, Description: {row[1]}, Style: {row[2]}")
        else:
            st.warning("No records found for Item 50002.")

    except Exception as e:
        st.error(f"❌ Failed to run the report: {e}")

if st.button("Run Full Report"):
    run_inventory_report()
