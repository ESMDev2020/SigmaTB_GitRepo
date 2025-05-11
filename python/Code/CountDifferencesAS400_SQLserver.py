# =============================================================================
# 🔍 ROW COUNT COMPARISON MODULE
# DESCRIPTION:
#     Compares row counts between AS400 and SQL Server databases using CSV files
#     Only compares tables that exist in SQL Server, extracting AS400 table names
#     from the SQL Server table names (everything after "_____")
# =============================================================================

# 📦 IMPORTS
import pandas as pd
import os
from pathlib import Path
import datetime

# =============================================================================
# 📝 CONSTANTS
# =============================================================================
# File paths
myCon_strAS400File = '/Users/erick/Documents/GitHub/SigmaTB_LocalRepo/data//20250419. MW4FILERowCounts.csv'
myCon_strSQLServerFile = '/Users/erick/Documents/GitHub/SigmaTB_LocalRepo/data//20250419. SQLServerRowCounts.csv'
myCon_strOutputFile = '/Users/erick/Documents/GitHub/SigmaTB_LocalRepo/data//RowCountComparison.csv'

# =============================================================================
# 🧩 FUNCTION: fun_read_csv_file
# =============================================================================
def fun_read_csv_file(my_var_strFilePath):
    """
    Reads a CSV file and returns a pandas DataFrame
    Returns tuple of (DataFrame, error message if any)
    """
    # Variable declarations
    my_var_dfData = None  # Will store the DataFrame
    my_var_strError = ""  # Will store any error message

    try:
        # Check if file exists
        if not os.path.exists(my_var_strFilePath):
            return None, f"File not found: {my_var_strFilePath}"
        
        # Read the CSV file
        my_var_dfData = pd.read_csv(my_var_strFilePath)
        return my_var_dfData, None
    except Exception as my_var_errException:
        return None, f"Error reading file {my_var_strFilePath}: {str(my_var_errException)}"

# =============================================================================
# 🧩 FUNCTION: fun_extract_as400_table_name
# =============================================================================
def fun_extract_as400_table_name(my_var_strSQLTableName):
    """
    Extracts the AS400 table name from the SQL Server table name
    Returns the AS400 table name (everything after "_____" and removes any remaining underscores)
    """
    # Variable declarations
    my_var_strAS400TableName = ""  # Will store the extracted AS400 table name

    try:
        # Split by "_____" and take the last part
        my_var_strAS400TableName = my_var_strSQLTableName.split("_____")[-1]
        # Remove any remaining underscores
        my_var_strAS400TableName = my_var_strAS400TableName.replace("_", "")
        return my_var_strAS400TableName
    except Exception:
        return my_var_strSQLTableName  # Return original if split fails

# =============================================================================
# 🧩 FUNCTION: fun_compare_row_counts
# =============================================================================
def fun_compare_row_counts(my_var_dfAS400, my_var_dfSQLServer):
    """
    Compares row counts between AS400 and SQL Server DataFrames
    Only compares tables that exist in SQL Server
    Returns tuple of (comparison DataFrame, error message if any)
    """
    # Variable declarations
    my_var_dfComparison = None  # Will store the comparison results
    my_var_strError = ""        # Will store any error message
    my_var_dfSQLProcessed = None  # Will store processed SQL Server data
    my_var_dfAS400Processed = None  # Will store processed AS400 data

    try:
        # Process SQL Server data
        my_var_dfSQLProcessed = my_var_dfSQLServer.copy()
        # Rename columns to match our expected format
        my_var_dfSQLProcessed = my_var_dfSQLProcessed.rename(columns={
            'TableName': 'TableName',
            'ApproximateRowCount': 'SQLServer_RowCount'
        })
        # Extract AS400 table name
        my_var_dfSQLProcessed['AS400TableName'] = my_var_dfSQLProcessed['TableName'].apply(fun_extract_as400_table_name)

        # Process AS400 data
        my_var_dfAS400Processed = my_var_dfAS400.copy()
        # Rename columns to match our expected format
        my_var_dfAS400Processed = my_var_dfAS400Processed.rename(columns={
            'TABLENAME': 'AS400TableName',
            'APPROXIMATEROWCOUNT': 'AS400_RowCount'
        })

        # Print processed data for debugging
        print("\nSQL Server processed data sample:")
        print(my_var_dfSQLProcessed.head())
        print("\nAS400 processed data sample:")
        print(my_var_dfAS400Processed.head())

        # Merge the DataFrames on AS400 table name
        my_var_dfComparison = pd.merge(
            my_var_dfSQLProcessed[['TableName', 'AS400TableName', 'SQLServer_RowCount']],
            my_var_dfAS400Processed[['AS400TableName', 'AS400_RowCount']],
            on='AS400TableName',
            how='left'
        )

        # Fill NaN values with 0 for row counts
        my_var_dfComparison['AS400_RowCount'] = my_var_dfComparison['AS400_RowCount'].fillna(0)

        # Calculate the difference
        my_var_dfComparison['Difference'] = my_var_dfComparison['AS400_RowCount'] - my_var_dfComparison['SQLServer_RowCount']

        # Add a status column
        my_var_dfComparison['Status'] = my_var_dfComparison.apply(
            lambda row: 'Match' if row['Difference'] == 0 else 'Mismatch',
            axis=1
        )

        # Sort by absolute difference
        my_var_dfComparison = my_var_dfComparison.sort_values(by='Difference', key=abs, ascending=False)

        # Select and rename columns for final output
        my_var_dfComparison = my_var_dfComparison[[
            'TableName',
            'AS400TableName',
            'SQLServer_RowCount',
            'AS400_RowCount',
            'Difference',
            'Status'
        ]]

        return my_var_dfComparison, None
    except Exception as my_var_errException:
        return None, f"Error comparing row counts: {str(my_var_errException)}"

# =============================================================================
# 🧩 FUNCTION: fun_check_csv_columns
# =============================================================================
def fun_check_csv_columns(my_var_strFilePath):
    """
    Checks and prints the column names from a CSV file
    Returns tuple of (column names list, error message if any)
    """
    # Variable declarations
    my_var_lstColumns = []  # Will store the column names
    my_var_strError = ""    # Will store any error message

    try:
        # Read just the header of the CSV file
        my_var_dfHeader = pd.read_csv(my_var_strFilePath, nrows=0)
        my_var_lstColumns = my_var_dfHeader.columns.tolist()
        return my_var_lstColumns, None
    except Exception as my_var_errException:
        return None, f"Error reading file {my_var_strFilePath}: {str(my_var_errException)}"

# =============================================================================
# 🚀 MAIN EXECUTION
# =============================================================================
if __name__ == "__main__":
    # Variable declarations
    my_var_dfAS400 = None        # Will store AS400 data
    my_var_dfSQLServer = None    # Will store SQL Server data
    my_var_dfComparison = None   # Will store comparison results
    my_var_strError = ""         # Will store any error message
    my_var_dtStartTime = None    # Will store execution start time
    my_var_dtEndTime = None      # Will store execution end time
    my_var_lstAS400Columns = []  # Will store AS400 column names
    my_var_lstSQLServerColumns = []  # Will store SQL Server column names

    # Record start time
    my_var_dtStartTime = datetime.datetime.now()
    print(f"\n🔍 Starting execution at: {my_var_dtStartTime.strftime('%Y-%m-%d %H:%M:%S')}")

    # Check column names in CSV files
    print("\n📋 Checking CSV file columns...")
    my_var_lstAS400Columns, my_var_strError = fun_check_csv_columns(myCon_strAS400File)
    if my_var_strError:
        print(f"❌ Error: {my_var_strError}")
        exit(1)
    print(f"AS400 columns: {my_var_lstAS400Columns}")

    my_var_lstSQLServerColumns, my_var_strError = fun_check_csv_columns(myCon_strSQLServerFile)
    if my_var_strError:
        print(f"❌ Error: {my_var_strError}")
        exit(1)
    print(f"SQL Server columns: {my_var_lstSQLServerColumns}")

    # Read AS400 data
    print("\n📥 Reading AS400 data...")
    my_var_dfAS400, my_var_strError = fun_read_csv_file(myCon_strAS400File)
    if my_var_strError:
        print(f"❌ Error: {my_var_strError}")
        exit(1)

    # Read SQL Server data
    print("📥 Reading SQL Server data...")
    my_var_dfSQLServer, my_var_strError = fun_read_csv_file(myCon_strSQLServerFile)
    if my_var_strError:
        print(f"❌ Error: {my_var_strError}")
        exit(1)

    # Compare row counts
    print("\n🔍 Comparing row counts...")
    my_var_dfComparison, my_var_strError = fun_compare_row_counts(my_var_dfAS400, my_var_dfSQLServer)
    if my_var_strError:
        print(f"❌ Error: {my_var_strError}")
        exit(1)

    # Print results
    print("\n📊 Comparison Results:")
    print("=" * 80)
    print(f"Total tables compared: {len(my_var_dfComparison)}")
    print(f"Tables with matching row counts: {len(my_var_dfComparison[my_var_dfComparison['Status'] == 'Match'])}")
    print(f"Tables with different row counts: {len(my_var_dfComparison[my_var_dfComparison['Status'] == 'Mismatch'])}")
    print("\nTop 10 largest differences:")
    print(my_var_dfComparison.head(10).to_string(index=False))
    print("\n" + "=" * 80)

    # Save results to CSV
    try:
        my_var_dfComparison.to_csv(myCon_strOutputFile, index=False)
        print(f"\n💾 Results saved to: {myCon_strOutputFile}")
    except Exception as my_var_errException:
        print(f"❌ Error saving results: {str(my_var_errException)}")

    # Record end time and print execution duration
    my_var_dtEndTime = datetime.datetime.now()
    print(f"\n⏱️  Execution completed at: {my_var_dtEndTime.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️  Total execution time: {my_var_dtEndTime - my_var_dtStartTime}")