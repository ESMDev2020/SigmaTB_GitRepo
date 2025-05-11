#**********************************************************************************************
# THIS GOS INTO ALL THE PROPERTIES OT THE DATABASE, DELETES THEM, AND RECREATES THEM
#
#
#**********************************************************************************************
import pyodbc
import datetime
import time
import logging
from typing import List, Tuple, Optional

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('extended_properties_debug.log'),
        logging.StreamHandler()
    ]
)

class ExtendedPropertiesUpdater:
    def __init__(self, connection_string: str):
        self.conn = pyodbc.connect(connection_string)
        self.cursor = self.conn.cursor()
        self.schema_name_filter = 'dbo'
        self.table_name_filter = 'z_%'
        self.separator = '_____'
        self.start_time = datetime.datetime.now()
        logging.info("ExtendedPropertiesUpdater initialized")
        
    def log(self, message: str, level: str = 'info'):
        """Enhanced logging with different levels"""
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if level == 'debug':
            logging.debug(f'[{timestamp}] {message}')
        elif level == 'info':
            logging.info(f'[{timestamp}] {message}')
        elif level == 'warning':
            logging.warning(f'[{timestamp}] {message}')
        elif level == 'error':
            logging.error(f'[{timestamp}] {message}')
        
    def delete_all_extended_properties(self):
        """Delete all extended properties for tables starting with z_"""
        logging.info("Starting deletion of all extended properties for z_ tables")
        
        # Delete table level properties
        query = """
        DECLARE @sql NVARCHAR(MAX) = '';
        SELECT @sql = @sql + 
            'EXEC sp_dropextendedproperty @name = ''' + ep.name + ''', ' +
            '@level0type = N''SCHEMA'', @level0name = ''' + SCHEMA_NAME(t.schema_id) + ''', ' +
            '@level1type = N''TABLE'', @level1name = ''' + t.name + '''; '
        FROM sys.extended_properties ep
        JOIN sys.tables t ON ep.major_id = t.object_id
        WHERE t.name LIKE ?
        AND ep.minor_id = 0;
        
        EXEC sp_executesql @sql;
        """
        
        try:
            self.cursor.execute(query, (self.table_name_filter,))
            self.conn.commit()
            logging.info("Successfully deleted table level properties")
        except Exception as e:
            logging.error(f"Error deleting table properties: {str(e)}")
            raise
            
        # Delete column level properties
        query = """
        DECLARE @sql NVARCHAR(MAX) = '';
        SELECT @sql = @sql + 
            'EXEC sp_dropextendedproperty @name = ''' + ep.name + ''', ' +
            '@level0type = N''SCHEMA'', @level0name = ''' + SCHEMA_NAME(t.schema_id) + ''', ' +
            '@level1type = N''TABLE'', @level1name = ''' + t.name + ''', ' +
            '@level2type = N''COLUMN'', @level2name = ''' + c.name + '''; '
        FROM sys.extended_properties ep
        JOIN sys.tables t ON ep.major_id = t.object_id
        JOIN sys.columns c ON t.object_id = c.object_id AND ep.minor_id = c.column_id
        WHERE t.name LIKE ?;
        
        EXEC sp_executesql @sql;
        """
        
        try:
            self.cursor.execute(query, (self.table_name_filter,))
            self.conn.commit()
            logging.info("Successfully deleted column level properties")
        except Exception as e:
            logging.error(f"Error deleting column properties: {str(e)}")
            raise
        
    def get_derived_code(self, name: str) -> Optional[str]:
        """Extract the code part after the last separator"""
        #logging.debug(f"Getting derived code for: {name}")
        if self.separator not in name:
            logging.debug(f"No separator found in name: {name}")
            return None
        code = name.split(self.separator)[-1]
        #logging.debug(f"Derived code: {code}")
        return code
    
    def property_exists(self, object_id: int, property_name: str, minor_id: int = 0) -> bool:
        """Check if an extended property exists"""
        #logging.debug(f"Checking if property exists - object_id: {object_id}, property_name: {property_name}, minor_id: {minor_id}")
        query = """
        SELECT 1 
        FROM sys.extended_properties ep
        WHERE ep.major_id = ?
        AND ep.minor_id = ?
        AND ep.name = ?
        """
        self.cursor.execute(query, (object_id, minor_id, property_name))
        exists = bool(self.cursor.fetchone())
        #logging.debug(f"Property exists: {exists}")
        return exists
    
    def get_tables(self) -> List[Tuple[str, str, int]]:
        """Get list of tables to process"""
        logging.info("Fetching tables to process")
        query = """
        SELECT 
            s.name,
            t.name,
            t.object_id
        FROM sys.tables t
        INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
        WHERE t.name LIKE ?
        AND (? IS NULL OR s.name = ?)
        ORDER BY s.name, t.name
        """
        self.cursor.execute(query, (self.table_name_filter, self.schema_name_filter, self.schema_name_filter))
        tables = self.cursor.fetchall()
        logging.info(f"Found {len(tables)} tables to process")
        return tables
    
    def get_columns(self, object_id: int) -> List[Tuple[str, int]]:
        """Get columns for a table"""
        #logging.debug(f"Fetching columns for object_id: {object_id}")
        query = """
        SELECT c.name, c.column_id
        FROM sys.columns c
        WHERE c.object_id = ?
        """
        self.cursor.execute(query, (object_id,))
        columns = self.cursor.fetchall()
        #logging.debug(f"Found {len(columns)} columns")
        return columns
    
    def update_table_property(self, schema_name: str, table_name: str, object_id: int, table_counter: int, total_tables: int):
        """Add table property"""
        logging.info(f"(Table {table_counter} of {total_tables}) - Processing table property for: [{schema_name}].[{table_name}]")
        table_code = self.get_derived_code(table_name)
        if not table_code:
            logging.warning(f"No table code derived for: {table_name}")
            return
            
        query = """
        EXEC sp_addextendedproperty 
            @name = ?,
            @value = ?,
            @level0type = N'SCHEMA',
            @level0name = ?,
            @level1type = N'TABLE',
            @level1name = ?
        """
        
        try:
            self.cursor.execute(query, (table_code, table_name, schema_name, table_name))
            self.conn.commit()
            logging.info(f"(Table {table_counter} of {total_tables}) - Successfully added table property: {table_code}")
        except Exception as e:
            logging.error(f"Error adding table property: {str(e)}")
            raise
    
    def update_column_property(self, schema_name: str, table_name: str, column_name: str, 
                             object_id: int, column_id: int, current_column_count: int, total_columns: int):
        """Add column property"""
        #logging.debug(f"(Col {current_column_count} of {total_columns}) - Processing column property for: [{schema_name}].[{table_name}].[{column_name}]")
        column_code = self.get_derived_code(column_name)
        if not column_code:
            logging.warning(f"No column code derived for: {column_name}")
            return
            
        query = """
        EXEC sp_addextendedproperty 
            @name = ?,
            @value = ?,
            @level0type = N'SCHEMA',
            @level0name = ?,
            @level1type = N'TABLE',
            @level1name = ?,
            @level2type = N'COLUMN',
            @level2name = ?
        """
        
        try:
            self.cursor.execute(query, (column_code, column_name, schema_name, table_name, column_name))
            self.conn.commit()
            #logging.debug(f"(Col {current_column_count} of {total_columns}) - Successfully added column property: {column_code}")
        except Exception as e:
            logging.error(f"Error adding column property: {str(e)}")
            raise
    
    def process_tables(self):
        """Main processing function"""
        logging.info('Starting table processing')
        logging.info('==================================================================')
        
        # First, delete all existing properties
        self.delete_all_extended_properties()
        
        tables = self.get_tables()
        total_tables = len(tables)
        logging.info(f'Total tables to process: {total_tables}')
        
        # Calculate total columns across all tables
        total_columns = 0
        for _, _, object_id in tables:
            columns = self.get_columns(object_id)
            total_columns += len(columns)
        logging.info(f'Total columns to process: {total_columns}')
        
        current_column_count = 0
        for i, (schema_name, table_name, object_id) in enumerate(tables, 1):
            try:
                logging.info(f'Processing table {i} of {total_tables}: [{schema_name}].[{table_name}]')
                
                # Get column count
                columns = self.get_columns(object_id)
                column_count = len(columns)
                logging.info(f'Found {column_count} columns')
                
                # Update table property
                self.update_table_property(schema_name, table_name, object_id, i, total_tables)
                
                # Update column properties
                for column_name, column_id in columns:
                    current_column_count += 1
                    self.update_column_property(schema_name, table_name, column_name, 
                                              object_id, column_id, current_column_count, total_columns)
                
                logging.info(f'Completed table [{schema_name}].[{table_name}]')
                
            except Exception as e:
                logging.error(f'ERROR processing table [{schema_name}].[{table_name}]: {str(e)}')
                continue
        
        end_time = datetime.datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        logging.info('==================================================================')
        logging.info('Processing completed')
        logging.info(f'Total Duration: {duration:.3f} seconds')
        logging.info(f'Processed {total_tables} tables and {total_columns} columns')
        logging.info('==================================================================')
        
    def close(self):
        """Close database connections"""
        logging.info("Closing database connections")
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
    
    logging.info("Starting Extended Properties Updater")
    updater = ExtendedPropertiesUpdater(connection_string)
    try:
        updater.process_tables()
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")
    finally:
        updater.close()

if __name__ == "__main__":
    main() 