import pyodbc
from pprint import pprint

# Your configuration
myDictConfig = {
    'AS400': {
        'DSN': "METALNET",
        'UID': "ESAAVEDR",
        'PWD': "ESM25",
        'TIMEOUT': 30,
        'LIBRARY': "MW4FILE"
    }
}

def check_as400_metadata():
    try:
        # AS400 connection
        conn = pyodbc.connect(
            f"DSN={myDictConfig['AS400']['DSN']};"
            f"UID={myDictConfig['AS400']['UID']};"
            f"PWD={myDictConfig['AS400']['PWD']};"
            f"TIMEOUT={myDictConfig['AS400']['TIMEOUT']}"
        )
        cursor = conn.cursor()
        
        table_name = "ITEMHIST"
        fiscal_year_column = "IHTRYY"
        
        print(f"\nChecking change tracking options for table: {myDictConfig['AS400']['LIBRARY']}.{table_name}")

        # 1. Verify the fiscal year column exists
        cursor.execute(f"""
            SELECT COLUMN_NAME, DATA_TYPE 
            FROM QSYS2.SYSCOLUMNS 
            WHERE TABLE_SCHEMA = '{myDictConfig['AS400']['LIBRARY']}' 
            AND TABLE_NAME = '{table_name}'
            AND COLUMN_NAME = '{fiscal_year_column}'
        """)
        fiscal_year_info = cursor.fetchone()
        
        # 2. Check for timestamp/date columns (potential change markers)
        cursor.execute(f"""
            SELECT COLUMN_NAME, DATA_TYPE 
            FROM QSYS2.SYSCOLUMNS 
            WHERE TABLE_SCHEMA = '{myDictConfig['AS400']['LIBRARY']}' 
            AND TABLE_NAME = '{table_name}'
            AND (COLUMN_NAME LIKE '%DATE%' 
                 OR COLUMN_NAME LIKE '%TIME%'
                 OR COLUMN_NAME LIKE '%UPD%'
                 OR COLUMN_NAME LIKE '%CHG%'
                 OR DATA_TYPE IN ('TIMESTAMP', 'DATE', 'TIME'))
            ORDER BY COLUMN_NAME
        """)
        potential_change_columns = cursor.fetchall()
        
        # Print results
        print("\n=== Results ===")
        print(f"1. Fiscal year column ('{fiscal_year_column}'):")
        if fiscal_year_info:
            print(f"   - Found: {fiscal_year_info.COLUMN_NAME} ({fiscal_year_info.DATA_TYPE})")
        else:
            print("   - NOT FOUND! Please verify column name")
        
        print("\n2. Potential change-tracking columns:")
        if potential_change_columns:
            for col in potential_change_columns:
                print(f"   - {col.COLUMN_NAME} ({col.DATA_TYPE})")
        else:
            print("   - No timestamp/date columns found")
            print("   - Fallback option: Use fiscal year + full table comparison")
        
        print("\nNote: Journaling is not available (confirmed by system)")
        
    except Exception as e:
        print(f"\nError checking metadata: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

# Run the check
check_as400_metadata()