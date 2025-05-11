import pyodbc
import logging
from typing import List, Dict, Tuple
from collections import defaultdict
import sys

# Set up logging with debug level
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO to DEBUG
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('column_relationships.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class ColumnRelationshipFinder:
    def __init__(self, connection_string: str):
        logging.debug("Initializing ColumnRelationshipFinder")
        self.conn = pyodbc.connect(connection_string)
        self.cursor = self.conn.cursor()
        self.separator = '_____'
        self.source_table = 'z_General_Ledger_Transaction_File_____GLTRANS'
        self.target_columns = [
            'GLACCT',
            'GLBTCH',
            'GLREF',
            'GLTRNT',
            'GLTRN#',
            'GLAMT',
            'GLAMTQ'
        ]
        logging.debug(f"Source table: {self.source_table}")
        logging.debug(f"Target columns: {self.target_columns}")
        
    def get_column_code(self, column_name: str) -> str:
        """Extract the code part after the last separator"""
        logging.debug(f"Extracting code from column: {column_name}")
        if self.separator not in column_name:
            logging.debug(f"No separator found, returning full name: {column_name}")
            return column_name
        code = column_name.split(self.separator)[-1]
        logging.debug(f"Extracted code: {code}")
        return code
    
    def get_table_columns(self, table_name: str) -> List[Tuple[str, str, int]]:
        """Get all columns for a table with their codes"""
        logging.debug(f"Getting columns for table: {table_name}")
        query = """
        SELECT c.name, c.column_id
        FROM sys.columns c
        WHERE c.object_id = OBJECT_ID(?)
        """
        self.cursor.execute(query, (table_name,))
        columns = []
        for name, column_id in self.cursor.fetchall():
            code = self.get_column_code(name)
            columns.append((name, code, column_id))
            logging.debug(f"Found column: {name} (ID: {column_id}, Code: {code})")
        logging.debug(f"Total columns found: {len(columns)}")
        return columns
    
    def get_table_description(self, table_name: str) -> str:
        """Get table description from extended properties"""
        logging.debug(f"Getting description for table: {table_name}")
        query = """
        SELECT value 
        FROM sys.extended_properties 
        WHERE major_id = OBJECT_ID(?) 
        AND minor_id = 0 
        AND name = 'MS_Description'
        """
        self.cursor.execute(query, (table_name,))
        result = self.cursor.fetchone()
        description = result[0] if result else table_name
        logging.debug(f"Table description: {description}")
        return description
    
    def get_column_description(self, table_name: str, column_id: int) -> str:
        """Get column description from extended properties"""
        logging.debug(f"Getting description for column ID {column_id} in table {table_name}")
        query = """
        SELECT value 
        FROM sys.extended_properties 
        WHERE major_id = OBJECT_ID(?) 
        AND minor_id = ? 
        AND name = 'MS_Description'
        """
        self.cursor.execute(query, (table_name, column_id))
        result = self.cursor.fetchone()
        description = result[0] if result else ''
        logging.debug(f"Column description: {description}")
        return description
    
    def find_relationships(self):
        """Find relationships between columns based on matching codes"""
        logging.info(f"Starting relationship analysis for table {self.source_table}")
        
        # Get source table columns
        logging.debug("Getting source table columns")
        source_columns = self.get_table_columns(self.source_table)
        source_table_desc = self.get_table_description(self.source_table)
        
        # Filter source columns to only target columns
        logging.debug("Filtering source columns")
        source_columns = [(name, code, col_id) for name, code, col_id in source_columns 
                         if name in self.target_columns]
        logging.debug(f"Filtered source columns: {source_columns}")
        
        # Get all tables in the database
        logging.debug("Getting all tables in database")
        query = """
        SELECT TABLE_SCHEMA + '.' + TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE = 'BASE TABLE'
        AND TABLE_NAME != ?
        """
        self.cursor.execute(query, (self.source_table,))
        all_tables = [row[0] for row in self.cursor.fetchall()]
        logging.debug(f"Found {len(all_tables)} tables to analyze")
        
        relationships = []
        for source_name, source_code, source_col_id in source_columns:
            logging.debug(f"\nAnalyzing source column: {source_name} (Code: {source_code})")
            source_desc = self.get_column_description(self.source_table, source_col_id)
            
            for table_name in all_tables:
                logging.debug(f"Checking table: {table_name}")
                # Get columns for the current table
                target_columns = self.get_table_columns(table_name)
                table_desc = self.get_table_description(table_name)
                
                for target_name, target_code, target_col_id in target_columns:
                    logging.debug(f"Comparing with target column: {target_name} (Code: {target_code})")
                    # Check if codes match
                    if source_code == target_code:
                        logging.debug(f"MATCH FOUND: {source_code} == {target_code}")
                        target_desc = self.get_column_description(table_name, target_col_id)
                        
                        relationship = {
                            'SourceTableName': source_table_desc,
                            'ForeignTableName': table_desc,
                            'SourceColumnName': source_desc,
                            'ForeignColumnName': target_desc,
                            'SourceTableCode': self.source_table,
                            'ForeignTableCode': table_name,
                            'SourceColumnCode': source_name,
                            'ForeignColumnCode': target_name
                        }
                        relationships.append(relationship)
                        logging.info(f"Found relationship: {source_name} -> {target_name}")
                    else:
                        logging.debug(f"No match: {source_code} != {target_code}")
        
        logging.info(f"Total relationships found: {len(relationships)}")
        return relationships
    
    def close(self):
        """Close database connections"""
        logging.debug("Closing database connections")
        self.cursor.close()
        self.conn.close()

def main():
    # ODBC connection string
    connection_string = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=database-3.c67ymu6q22o1.us-east-1.rds.amazonaws.com;"
        "Database=SigmaTB;"
        "UID=admin;"
        "PWD=Er1c41234$;"
    )
    
    logging.info("Starting column relationship finder")
    finder = ColumnRelationshipFinder(connection_string)
    try:
        relationships = finder.find_relationships()
        
        # Print results in a formatted way
        print("\nFound Relationships:")
        print("=" * 100)
        for rel in relationships:
            print(f"Source: {rel['SourceTableName']}.{rel['SourceColumnName']} ({rel['SourceColumnCode']})")
            print(f"Target: {rel['ForeignTableName']}.{rel['ForeignColumnName']} ({rel['ForeignColumnCode']})")
            print("-" * 100)
            
        logging.info(f"Total relationships found: {len(relationships)}")
        
    except Exception as e:
        logging.error(f"Error: {str(e)}", exc_info=True)  # Added exc_info for full traceback
    finally:
        finder.close()

if __name__ == "__main__":
    main()