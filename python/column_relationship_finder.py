"""
Column Relationship Finder
This script analyzes database tables to find relationships between columns based on matching codes.
It processes the GLTRANS table and its target columns to find matching columns in other tables.
"""

# ===================================================
# IMPORTS
# ===================================================
import pyodbc
import logging
from typing import List, Dict, Tuple
from collections import defaultdict
import sys
from datetime import datetime
import time
import csv

# ===================================================
# CONSTANTS
# ===================================================
# Database Constants
myConStrConnectionString: str = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=database-3.c67ymu6q22o1.us-east-1.rds.amazonaws.com;"
    "Database=SigmaTB;"
    "UID=admin;"
    "PWD=Er1c41234$;"
)

# Table Constants
myConStrSourceTable: str = 'z_General_Ledger_Transaction_File_____GLTRANS'
myConStrSeparator: str = '_____'

# Target Columns Constants
myConListTargetColumns: List[str] = [
    'GLACCT',
    'GLBTCH',
    'GLREF',
    'GLTRNT',
    'GLTRN#',
    'GLAMT',
    'GLAMTQ'
]

# Control Constants
myConBoolExitAfterFirstMatch: bool = False  # Set to True to exit after first match, False to find all matches

# ===================================================
# FUNCTIONS
# ===================================================

def fun_initialize_logging() -> None:
    """
    Initializes logging configuration for the application.
    Sets up both file and console logging with info level.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('column_relationships.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def fun_get_column_code(myStrColumnName: str, myStrSeparator: str) -> str:
    """
    Extracts the code part from a column name after the separator.
    
    Args:
        myStrColumnName: The full column name
        myStrSeparator: The separator used in column names
        
    Returns:
        The extracted code part of the column name
    """
    if myStrSeparator not in myStrColumnName:
        return myStrColumnName
    myStrCode: str = myStrColumnName.split(myStrSeparator)[-1]
    return myStrCode

def fun_get_table_columns(myObjCursor, myStrTableName: str, myStrSeparator: str) -> List[Tuple[str, str, int]]:
    """
    Retrieves all columns for a given table with their codes.
    
    Args:
        myObjCursor: Database cursor
        myStrTableName: Name of the table to get columns from
        myStrSeparator: Separator used in column names
        
    Returns:
        List of tuples containing (column_name, column_code, column_id)
    """
    myStrQuery: str = """
    SELECT c.name, c.column_id
    FROM sys.columns c
    WHERE c.object_id = OBJECT_ID(?)
    """
    myObjCursor.execute(myStrQuery, (myStrTableName,))
    myListColumns: List[Tuple[str, str, int]] = []
    
    # Process each column
    for myStrName, myIntColumnId in myObjCursor.fetchall():
        myStrCode: str = fun_get_column_code(myStrName, myStrSeparator)
        myListColumns.append((myStrName, myStrCode, myIntColumnId))
    
    return myListColumns

def fun_get_table_description(myObjCursor, myStrTableName: str) -> str:
    """
    Retrieves the description of a table from extended properties.
    
    Args:
        myObjCursor: Database cursor
        myStrTableName: Name of the table
        
    Returns:
        Table description or table name if no description exists
    """
    myStrQuery: str = """
    SELECT CAST(value AS NVARCHAR(MAX))
    FROM sys.extended_properties 
    WHERE major_id = OBJECT_ID(?) 
    AND minor_id = 0
    """
    myObjCursor.execute(myStrQuery, (myStrTableName,))
    myObjResult = myObjCursor.fetchone()
    myStrDescription: str = myObjResult[0] if myObjResult else myStrTableName
    return myStrDescription

def fun_get_column_description(myObjCursor, myStrTableName: str, myIntColumnId: int) -> str:
    """
    Retrieves the description of a column from extended properties.
    
    Args:
        myObjCursor: Database cursor
        myStrTableName: Name of the table
        myIntColumnId: ID of the column
        
    Returns:
        Column description or empty string if no description exists
    """
    myStrQuery: str = """
    SELECT CAST(value AS NVARCHAR(MAX))
    FROM sys.extended_properties 
    WHERE major_id = OBJECT_ID(?) 
    AND minor_id = ?
    """
    myObjCursor.execute(myStrQuery, (myStrTableName, myIntColumnId))
    myObjResult = myObjCursor.fetchone()
    myStrDescription: str = myObjResult[0] if myObjResult else ''
    return myStrDescription

def fun_get_table_XP_code(myObjCursor, myStrTableName: str) -> str:
    """
    Retrieves the code (extended property) of a table.
    The code is the part after the separator in the table name.
    
    Args:
        myObjCursor: Database cursor
        myStrTableName: Name of the table
        
    Returns:
        Table code (part after separator) or table name if no separator exists
    """
    if myConStrSeparator not in myStrTableName:
        return myStrTableName
    myStrTableCode: str = myStrTableName.split(myConStrSeparator)[-1]
    return myStrTableCode

def fun_get_column_XP_code(myObjCursor, myStrTableName: str, myIntColumnId: int, myStrColumnName: str) -> str:
    """
    Retrieves the code (extended property) of a column.
    The code is the part after the separator in the column name.
    
    Args:
        myObjCursor: Database cursor
        myStrTableName: Name of the table
        myIntColumnId: ID of the column
        myStrColumnName: Full column name
        
    Returns:
        Column code (part after separator) or column name if no separator exists
    """
    if myConStrSeparator not in myStrColumnName:
        return myStrColumnName
    myStrColumnCode: str = myStrColumnName.split(myConStrSeparator)[-1]
    return myStrColumnCode

def fun_compare_column_codes(myStrSourceCode: str, myStrTargetCode: str) -> bool:
    """
    Compares two column codes, allowing for different prefixes but matching the rest.
    For example: GLTRANS.GLRECD and SHIPMAST.SHRECD would match because RECD is the same.
    
    Args:
        myStrSourceCode: Source column code (e.g., 'GLRECD')
        myStrTargetCode: Target column code (e.g., 'SHRECD')
        
    Returns:
        True if the codes match (ignoring prefix), False otherwise
    """
    # Remove any prefix (first 2 characters) and compare the rest
    myStrSourceBase = myStrSourceCode[2:] if len(myStrSourceCode) > 2 else myStrSourceCode
    myStrTargetBase = myStrTargetCode[2:] if len(myStrTargetCode) > 2 else myStrTargetCode
    
    return myStrSourceBase == myStrTargetBase

def fun_find_relationships(myStrConnectionString: str) -> List[Dict]:
    """
    Main function to find relationships between columns.
    Processes the source table and finds matching columns in other tables.
    
    Args:
        myStrConnectionString: Database connection string
        
    Returns:
        List of dictionaries containing found relationships
    """
    # Initialize variables
    myObjConn = pyodbc.connect(myStrConnectionString)
    myObjCursor = myObjConn.cursor()
    myListRelationships: List[Dict] = []
    
    try:
        # Get total number of columns in tables starting with 'z_'
        myStrQuery: str = """
        SELECT COUNT(c.column_id) as total_columns
        FROM sys.columns c
        JOIN sys.tables t ON c.object_id = t.object_id
        WHERE t.name LIKE 'z_%'
        """
        myObjCursor.execute(myStrQuery)
        myIntTotalColumns = myObjCursor.fetchone()[0]
        
        # Calculate total iterations (columns * target columns to search)
        myIntTotalIterations = myIntTotalColumns * len(myConListTargetColumns)
        logging.info(f"Total columns in z_ tables: {myIntTotalColumns}")
        logging.info(f"Total iterations to process: {myIntTotalIterations} (columns * target columns)")
        
        # Get source table information
        logging.info(f"Starting relationship analysis for table {myConStrSourceTable}")
        myListSourceColumns = fun_get_table_columns(myObjCursor, myConStrSourceTable, myConStrSeparator)
        myStrSourceTableDesc = fun_get_table_description(myObjCursor, myConStrSourceTable)
        
        # Filter source columns
        myListSourceColumns = [(myStrName, myStrCode, myIntColId) 
                              for myStrName, myStrCode, myIntColId in myListSourceColumns 
                              if myStrCode in myConListTargetColumns]
        
        # Get all tables starting with 'z_'
        myStrQuery = """
        SELECT TABLE_SCHEMA + '.' + TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE = 'BASE TABLE'
        AND TABLE_NAME LIKE 'z_%'
        AND TABLE_NAME != ?
        """
        myObjCursor.execute(myStrQuery, (myConStrSourceTable,))
        myListAllTables = [myStrRow[0] for myStrRow in myObjCursor.fetchall()]
        
        # Initialize counter
        myIntCurrentIteration: int = 0
        
        # Process each source column
        for myStrSourceName, myStrSourceCode, myIntSourceColId in myListSourceColumns:
            myStrSourceDesc = fun_get_column_description(myObjCursor, myConStrSourceTable, myIntSourceColId)
            
            # Process each target table
            for myStrTableName in myListAllTables:
                myListTargetColumns = fun_get_table_columns(myObjCursor, myStrTableName, myConStrSeparator)
                myStrTableDesc = fun_get_table_description(myObjCursor, myStrTableName)
                
                # Check each target column
                for myStrTargetName, myStrTargetCode, myIntTargetColId in myListTargetColumns:
                    myIntCurrentIteration += 1
                    
                    # Log progress every 2000 iterations
                    if myIntCurrentIteration % 2000 == 0:
                        logging.info(f"Processing iteration {myIntCurrentIteration} of {myIntTotalIterations} ({(myIntCurrentIteration/myIntTotalIterations)*100:.1f}%)")
                    
                    # Check for code match using the new comparison function
                    if fun_compare_column_codes(myStrSourceCode, myStrTargetCode):
                        myStrTargetDesc = fun_get_column_description(myObjCursor, myStrTableName, myIntTargetColId)
                        
                        # Create relationship record
                        myDictRelationship = {
                            'Source_Table_Name': myConStrSourceTable,      # Table name
                            'Foreign_Table_Name': myStrTableName,          # Table name
                            'Source_Table_XP_Code': fun_get_table_XP_code(myObjCursor, myConStrSourceTable),  # Table XP code
                            'Foreign_Table_XP_Code': fun_get_table_XP_code(myObjCursor, myStrTableName),      # Table XP code
                            'Source_Column_Name': myStrSourceName,         # Full column name
                            'Foreign_Column_Name': myStrTargetName,        # Full column name
                            'Source_Column_XP_Code': fun_get_column_XP_code(myObjCursor, myConStrSourceTable, myIntSourceColId, myStrSourceName),  # Column XP code
                            'Foreign_Column_XP_Code': fun_get_column_XP_code(myObjCursor, myStrTableName, myIntTargetColId, myStrTargetName)       # Column XP code
                        }
                        # Print debug information for myDictRel
                        logging.debug("Relationship Dictionary Contents:")
                        for key, value in myDictRelationship.items():
                            logging.debug(f"{key}: {value}")
                        myListRelationships.append(myDictRelationship)
                        logging.info(f"Found relationship: [{myStrSourceName}] -> [{myStrTargetName}]")
                        
                        # Exit after first match if configured
                        if myConBoolExitAfterFirstMatch:
                            logging.info("Exiting after first match as configured")
                            return myListRelationships
        
        logging.info(f"Total relationships found: {len(myListRelationships)}")
        return myListRelationships
        
    except Exception as myObjError:
        logging.error(f"Error in relationship finding: {str(myObjError)}", exc_info=True)
        raise
    finally:
        myObjCursor.close()
        myObjConn.close()

def sub_print_relationships(myListRelationships: List[Dict]) -> None:
    """
    Prints the found relationships in a formatted way and saves to CSV.
    
    Args:
        myListRelationships: List of relationship dictionaries to print
    """
    # Print to console
    print("\nFound Relationships:")
    print("=" * 100)
    for myDictRel in myListRelationships:
        print(f"Source: [{myDictRel['Source_Table_XP_Code']}].[{myDictRel['Source_Column_XP_Code']}] ->>>>>>>>>>> [{myDictRel['Foreign_Table_XP_Code']}].[{myDictRel['Foreign_Column_XP_Code']}]")
        print("-" * 100)
    
    # Save to CSV
    myStrTimestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    myStrCsvFilename = f"column_relationships_{myStrTimestamp}.csv"
    
    with open(myStrCsvFilename, 'w', newline='') as myObjCsvFile:
        myObjWriter = csv.writer(myObjCsvFile)
        
        # Write header
        myObjWriter.writerow([
            'Source Table XP Code',
            'Source Column XP Code',
            'Foreign Table XP Code',
            'Foreign Column XP Code',
            'Source Table Name',
            'Source Column Name',
            'Foreign Table Name',
            'Foreign Column Name'
        ])
        
        # Write data
        for myDictRel in myListRelationships:
            myObjWriter.writerow([
                myDictRel['Source_Table_XP_Code'],
                myDictRel['Source_Column_XP_Code'],
                myDictRel['Foreign_Table_XP_Code'],
                myDictRel['Foreign_Column_XP_Code'],
                myDictRel['Source_Table_Name'],
                myDictRel['Source_Column_Name'],
                myDictRel['Foreign_Table_Name'],
                myDictRel['Foreign_Column_Name']
            ])
    
    print(f"\nResults have been saved to: {myStrCsvFilename}")

def main():
    """
    Main execution function.
    Initializes logging, finds relationships, and prints results.
    """
    try:
        # Initialize logging
        fun_initialize_logging()
        
        # Record start time
        myDtStartTime = datetime.now()
        logging.info(f"Starting execution at {myDtStartTime}")
        
        # Find relationships
        myListRelationships = fun_find_relationships(myConStrConnectionString)
        
        # Print results
        sub_print_relationships(myListRelationships)
        
        # Record end time and duration
        myDtEndTime = datetime.now()
        myFltDuration = (myDtEndTime - myDtStartTime).total_seconds()
        logging.info(f"Execution completed at {myDtEndTime}")
        logging.info(f"Total execution time: {myFltDuration:.2f} seconds")
        
    except Exception as myObjError:
        logging.error(f"Error in main execution: {str(myObjError)}", exc_info=True)
        raise

if __name__ == "__main__":
    main() 