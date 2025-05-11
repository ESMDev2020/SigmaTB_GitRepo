# -*- coding: utf-8 -*-
"""
COMPLETE DATABASE SYNCHRONIZATION SCRIPT
DOCUMENTATION: Synchronizes data between source database (AS400 or MySQL) and MSSQL 
               using year-based partitioning with automatic fiscal year column detection.
               NOW WITH DATA TYPE PRESERVATION.
"""

# =============================================
# IMPORTS SECTION
# =============================================
import pyodbc
from tqdm import tqdm
import threading
from datetime import datetime
import traceback
from decimal import Decimal
import winsound
import time
from queue import Queue, Empty
print_lock = threading.Lock()


# =============================================
# CONSTANTS SECTION
# =============================================
# Configuration dictionary
myDictConfig = {
    # AS400 settings
    'AS400': {
        'DSN': "METALNET",
        'UID': "ESAAVEDR",
        'PWD': "ESM25",
        'TIMEOUT': 30,
        'LIBRARY': "MW4FILE"
    },
    # MySQL settings (updated to use DSN approach)
    'MYSQL': {
        'DSN': "DocuWare",
        'UID': "your_username",
        'PWD': "your_password",
        'TIMEOUT': 30,
        'SCHEMA': "dwdata"
    },
    # SQL Server settings
    'SQL_SERVER': {
        'DRIVER': "{ODBC Driver 17 for SQL Server}",
        'SERVER': "database-3.c67ymu6q22o1.us-east-1.rds.amazonaws.com,1433",
        'DB': "SigmaTB",
        'UID': "admin",
        'PWD': "Er1c41234$",
        'SCHEMA': "mrs"
    },
    # Source selection
    'SOURCE_TYPE': 'AS400',  # 'AS400' or 'MYSQL'
    
    # Operation settings
    'BATCH_SIZE': 1000,
    'MAX_THREADS': 1,
    'MAX_RETRIES': 3,
    'RETRY_DELAY': 5,
    'LOG_FILE': "failed_inserts.log",
    'REPORT_FILE': "migration_report.csv"
}

# System constants
myConStrVbCrLf = "\r\n"
myConStrTimestampFormat = '%Y-%m-%d %H:%M:%S'

# =============================================
# CLASSES SECTION
# =============================================
class clsConnectionPool:
    """
    Thread-safe connection pool implementation.
    DOCUMENTATION: Manages database connections with pooling for efficient reuse.
    """
    def __init__(self, funCreator, varIntMaxSize=5):
        """
        Initialize connection pool
        INPUT: 
            funCreator - Function to create new connections
            varIntMaxSize - Maximum pool size
        """
        self.objQueuePool = Queue(varIntMaxSize)
        self.funCreateConnection = funCreator
        self.varIntMaxSize = varIntMaxSize
        self.objLockThread = threading.Lock()
        self.varIntConnectionsCreated = 0
        
        # Initialize pool with connections
        for _ in range(varIntMaxSize):
            self.sub_CreateAndAddConnection()

    def sub_CreateAndAddConnection(self):
        """Create a new connection and add it to the pool"""
        try:
            objNewConn = self.funCreateConnection()
            self.objQueuePool.put(objNewConn)
            with self.objLockThread:
                self.varIntConnectionsCreated += 1
        except Exception as varExcError:
            print(f"Failed to create connection: {str(varExcError)}")
            raise

    def fun_GetConnection(self):
        """Retrieve a connection from the pool with timeout"""
        try:
            return self.objQueuePool.get(timeout=30)
        except Empty:
            with self.objLockThread:
                if self.varIntConnectionsCreated < self.varIntMaxSize:
                    self.sub_CreateAndAddConnection()
                    return self.objQueuePool.get(timeout=30)
            raise Exception("Connection pool exhausted and max size reached")

    def sub_ReturnConnection(self, objConn):
        """Return a connection to the pool"""
        if objConn:
            try:
                objConn.rollback()
                self.objQueuePool.put(objConn)
            except Exception as varExcError:
                print(f"Error returning connection to pool: {str(varExcError)}")
                try:
                    objConn.close()
                except:
                    pass
                self.sub_CreateAndAddConnection()

    def sub_CloseAllConnections(self):
        """Close all connections in the pool"""
        while not self.objQueuePool.empty():
            try:
                objConn = self.objQueuePool.get_nowait()
                objConn.close()
            except:
                pass

# Global connection pool variables
myObjSourcePool = None
myObjSqlPool = None
global_table_results = []  # To print the report

# =============================================
# FUNCTIONS SECTION
# =============================================
def fun_InitializeConnectionPools():
    """
    Initialize connection pools for source database (AS400 or MySQL) and SQL Server.
    DOCUMENTATION: Creates thread-safe connection pools for both database systems.
    """
    global myObjSourcePool, myObjSqlPool
    
    def fun_CreateAs400Connection():
        """Create a new AS400 connection"""
        fun_PrintStatus("", "Creating AS400 connection", "process")
        varStrConnString = f"DSN={myDictConfig['AS400']['DSN']};UID={myDictConfig['AS400']['UID']};PWD={myDictConfig['AS400']['PWD']};Timeout={myDictConfig['AS400']['TIMEOUT']}"
        return pyodbc.connect(varStrConnString, autocommit=False)
    
    def fun_CreateMySQLConnection():
        """Create a new MySQL connection"""
        fun_PrintStatus("", "Creating MySQL connection", "process")
        varStrConnString = f"DSN={myDictConfig['MYSQL']['DSN']}"
        return pyodbc.connect(varStrConnString, autocommit=False)
    
    def fun_CreateSqlConnection():
        """Create a new SQL Server connection"""
        fun_PrintStatus("", "Creating SQL connection", "process")
        varStrConnString = (
            f"DRIVER={myDictConfig['SQL_SERVER']['DRIVER']};"
            f"SERVER={myDictConfig['SQL_SERVER']['SERVER']};"
            f"DATABASE={myDictConfig['SQL_SERVER']['DB']};"
            f"UID={myDictConfig['SQL_SERVER']['UID']};"
            f"PWD={myDictConfig['SQL_SERVER']['PWD']};"
            "Encrypt=yes;TrustServerCertificate=yes;Connection Timeout=30;"
        )
        return pyodbc.connect(varStrConnString, autocommit=False)
    
    # Create connection pool based on source type
    if myDictConfig['SOURCE_TYPE'] == 'AS400':
        fun_PrintStatus("SYSTEM", "Initializing AS400 connection pool", "process")
        myObjSourcePool = clsConnectionPool(fun_CreateAs400Connection, myDictConfig['MAX_THREADS'])
    else:  # MYSQL
        fun_PrintStatus("SYSTEM", "Initializing MySQL connection pool", "process")
        myObjSourcePool = clsConnectionPool(fun_CreateMySQLConnection, myDictConfig['MAX_THREADS'])
    
    myObjSqlPool = clsConnectionPool(fun_CreateSqlConnection, myDictConfig['MAX_THREADS'])

def fun_PrintStatus(varStrTableName, varStrStatus, varStrIcon):
    """
    Print formatted status message with timestamp and icon.
    INPUT:
        varStrTableName - Name of table being processed
        varStrStatus - Status message to display
        varStrIcon - Icon type for visual indication
    """
    varStrTimestamp = datetime.now().strftime(myConStrTimestampFormat)
    
    dictIcons = {
        "process":  "      ⚙️",
        "download": "   ⬇️",
        "insert":   "      ➕",
        "drop"  :   "   🗑️",
        "update":   "🔄",
        "success":  "✅",
        "failure":  "❌",
        "warning":  "⚠️",
        "info":     "ℹ️"  # Add this line for info messages
    }
    
    varStrIcon = dictIcons.get(varStrIcon, "❓")
    with print_lock:
        print(f"[{varStrTimestamp}] {varStrIcon} {varStrTableName.ljust(20)}: {varStrStatus}")

def fun_GetOneColumnMetadata(varObjSourceCursor, varObjMSSQLCursor, varStrSchema, varStrTable):
    """
    Retrieve column names, descriptions, and data types with fallback to actual structure.
    INPUT:
        varObjSourceCursor - Source database cursor (AS400 or MySQL)
        varObjMSSQLCursor - MSSQL cursor
        varStrSchema - Schema name
        varStrTable - Table name
    OUTPUT:
        List of tuples (column_name, column_description, data_type, length, numeric_precision, numeric_scale)
    """
    try:
        # Different metadata queries based on source type
        if myDictConfig['SOURCE_TYPE'] == 'AS400':
            # Enhanced AS400 metadata query with data types
            varObjSourceCursor.execute(f"""
                SELECT COLUMN_NAME, COLUMN_TEXT, DATA_TYPE, LENGTH, 
                       NUMERIC_PRECISION, NUMERIC_SCALE 
                FROM QSYS2.SYSCOLUMNS
                WHERE TABLE_SCHEMA = '{varStrSchema}' AND TABLE_NAME = '{varStrTable}'
                ORDER BY ORDINAL_POSITION
            """)
            
            varListMetadataCols = [
                (
                    col[0].strip(),  # column_name 
                    (col[1] or "").strip().replace(" ", "_").replace("'", "_")
                        .replace(']', ']]').replace('?', 'q').replace('/', '_'),  # column_description
                    col[2].strip() if col[2] else "VARCHAR",  # data_type
                    col[3] if col[3] is not None else 50,  # length
                    col[4] if col[4] is not None else 18,  # numeric_precision
                    col[5] if col[5] is not None else 0   # numeric_scale
                ) 
                for col in varObjSourceCursor.fetchall()
            ]
        else:  # MYSQL
            # Enhanced MySQL metadata query with data types
            varObjSourceCursor.execute(f"""
                SELECT COLUMN_NAME, COLUMN_COMMENT, DATA_TYPE, 
                       CHARACTER_MAXIMUM_LENGTH, NUMERIC_PRECISION, NUMERIC_SCALE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = '{varStrSchema}' AND TABLE_NAME = '{varStrTable}'
                ORDER BY ORDINAL_POSITION
            """)
            
            varListMetadataCols = [
                (
                    col[0].strip(),  # column_name
                    (col[1] or col[0]).strip().replace(" ", "_").replace("'", "_")
                        .replace(']', ']]').replace('?', 'q').replace('/', '_'),  # column_description
                    col[2].strip() if col[2] else "VARCHAR",  # data_type
                    col[3] if col[3] is not None else 50,  # length
                    col[4] if col[4] is not None else 18,  # numeric_precision
                    col[5] if col[5] is not None else 0   # numeric_scale
                ) 
                for col in varObjSourceCursor.fetchall()
            ]
        
        # Get actual columns to verify
        varListActualCols = fun_GetActualColumnNames(varObjSourceCursor, varStrSchema, varStrTable)
        
        if len(varListMetadataCols) != len(varListActualCols):
            fun_PrintStatus(varStrTable, "Metadata mismatch - Using actual column names", "warning")
            # Create default metadata with VARCHAR type
            return [(col, col, "VARCHAR", 100, 18, 0) for col in varListActualCols]
        
        return varListMetadataCols
    except Exception as varExcError:
        fun_PrintStatus(varStrTable, f"Metadata query failed: {str(varExcError)} - Using actual names", "warning")
        varListActualCols = fun_GetActualColumnNames(varObjSourceCursor, varStrSchema, varStrTable)
        # Return default values with VARCHAR type
        return [(col, col, "VARCHAR", 100, 18, 0) for col in varListActualCols]

def fun_GetActualColumnNames(varObjCursor, varStrSchema, varStrTable):
    """
    Get actual column names from table structure.
    INPUT:
        varObjCursor - Database cursor
        varStrSchema - Schema name
        varStrTable - Table name
    OUTPUT:
        List of column names
    """
    try:
        # Different syntax for AS400 vs MySQL
        if myDictConfig['SOURCE_TYPE'] == 'AS400':
            varObjCursor.execute(f"SELECT * FROM {varStrSchema}.{varStrTable} WHERE 1=0")
        else:  # MYSQL
            varObjCursor.execute(f"SELECT * FROM `{varStrSchema}`.`{varStrTable}` WHERE 1=0")
            
        return [column[0] for column in varObjCursor.description]
    except Exception as varExcError:
        fun_PrintStatus(varStrTable, f"Error getting actual columns: {str(varExcError)}", "failure")
        return []

def fun_DetectFiscalYearColumn(varObjSourceCursor, varStrSchema, varStrTable):
    """
    Detect fiscal year column by finding the first column ending with 'YY'
    INPUT:
        varObjSourceCursor - Source database cursor (AS400 or MySQL)
        varStrSchema - Schema name
        varStrTable - Table name
    OUTPUT:
        String - Name of fiscal year column or None if not found
    """
    try:
        if myDictConfig['SOURCE_TYPE'] == 'AS400':
            # AS400 metadata query
            varObjSourceCursor.execute(f"""
                SELECT COLUMN_NAME 
                FROM QSYS2.SYSCOLUMNS 
                WHERE TABLE_SCHEMA = '{varStrSchema}' 
                  AND TABLE_NAME = '{varStrTable}'
                  AND COLUMN_NAME LIKE '%YY'
                ORDER BY ORDINAL_POSITION
            """)
        else:  # MYSQL
            # MySQL metadata query
            varObjSourceCursor.execute(f"""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = '{varStrSchema}' 
                  AND TABLE_NAME = '{varStrTable}'
                  AND COLUMN_NAME LIKE '%YY'
                ORDER BY ORDINAL_POSITION
            """)
            
        varObjResult = varObjSourceCursor.fetchone()
        return varObjResult[0] if varObjResult else None
    except Exception as varExcError:
        fun_PrintStatus(varStrTable, f"Error detecting fiscal year column: {str(varExcError)}", "failure")
        return None

def fun_GetTableRowCountWithCondition(varObjCursor, varStrSchema, varStrTable, varStrCondition):
    """
    Get row count for a table with a specific condition.
    Handles different SQL syntax for AS400, MySQL, and MSSQL.
    
    INPUT:
        varObjCursor - Database cursor
        varStrSchema - Schema name
        varStrTable - Table name
        varStrCondition - WHERE condition 
    OUTPUT:
        Integer - Row count or -1 on error
    """
    try:
        if myDictConfig['SOURCE_TYPE'] == 'AS400' and varStrSchema == myDictConfig['AS400']['LIBRARY']:
            # AS400 query - no special handling needed
            sql = f"SELECT COUNT(*) FROM {varStrSchema}.{varStrTable} WHERE {varStrCondition}"
        elif myDictConfig['SOURCE_TYPE'] == 'MYSQL' and varStrSchema == myDictConfig['MYSQL']['SCHEMA']:
            # MySQL query - use backticks for identifiers
            sql = f"SELECT COUNT(*) FROM `{varStrSchema}`.`{varStrTable}` WHERE {varStrCondition}"
        else:
            # MSSQL query - parse condition and apply proper formatting
            varStrBase = f"SELECT COUNT(*) FROM [{varStrSchema}].[{varStrTable}] WHERE "
            
            # Split compound conditions
            varListConditions = varStrCondition.split(" AND ")
            varListProcessedConditions = []
            
            for varStrSingleCondition in varListConditions:
                # Find comparison operator
                varStrOperator = None
                for op in ['<=', '>=', '<>', '!=', '=', '<', '>']:
                    if op in varStrSingleCondition:
                        varStrOperator = op
                        break
                
                if varStrOperator:
                    # Split into column and value parts
                    varStrCol, varStrValue = varStrSingleCondition.split(varStrOperator, 1)
                    varStrCol = varStrCol.strip()
                    
                    # Process condition - Apply TRY_CAST to column if it's fiscal year
                    if "FiscalYearCol" in varStrCol:
                        varStrProcessedCondition = f"TRY_CAST({varStrCol} AS DECIMAL(18,2)) {varStrOperator} {varStrValue.strip()}"
                    else:
                        varStrProcessedCondition = f"{varStrCol} {varStrOperator} {varStrValue.strip()}"
                    
                    varListProcessedConditions.append(varStrProcessedCondition)
                else:
                    # Keep non-comparison conditions as-is
                    varListProcessedConditions.append(varStrSingleCondition)
            
            sql = varStrBase + " AND ".join(varListProcessedConditions)
        
        varObjCursor.execute(sql)
        result = varObjCursor.fetchone()[0]
        return result
    except Exception as varExcError:
        fun_PrintStatus(varStrTable, f"Row count error for condition '{varStrCondition}': {str(varExcError)}", "failure")
        return -1

def fun_CheckTableExists(varObjCursor, varStrSchema, varStrTable):
    """Check if a table exists in the database"""
    try:
        varObjCursor.execute(f"""
            SELECT 1 FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = '{varStrSchema}'
            AND TABLE_NAME = '{varStrTable}'
        """)
        return varObjCursor.fetchone() is not None
    except Exception as varExcError:
        fun_PrintStatus(varStrTable, f"Table existence check failed: {str(varExcError)}", "warning")
        return False

def fun_MapAS400TypeToSQLType(varStrAS400Type, varIntLength, varIntPrecision, varIntScale):
    """
    Map AS400 data types to SQL Server data types
    
    INPUT:
        varStrAS400Type - AS400 data type
        varIntLength - Length for character types
        varIntPrecision - Precision for numeric types
        varIntScale - Scale for numeric types
    OUTPUT:
        String - SQL Server data type
    """
    # Standardize type name to uppercase for consistent matching
    varStrType = varStrAS400Type.upper() if varStrAS400Type else "VARCHAR"
    
    # Map AS400 types to SQL Server types
    if varStrType in ('DECIMAL', 'DEC', 'NUMERIC', 'NUM'):
        # Default to (18,0) if precision/scale not provided
        precision = varIntPrecision if varIntPrecision is not None else 18
        scale = varIntScale if varIntScale is not None else 0
        return f"DECIMAL({precision},{scale})"
    elif varStrType in ('INTEGER', 'INT', 'SMALLINT', 'BIGINT'):
        return "INT"
    elif varStrType == 'CHAR':
        length = varIntLength if varIntLength is not None else 50
        # Cap CHAR length to prevent exceeding SQL Server limits
        length = min(length, 8000)
        return f"CHAR({length})"
    elif varStrType in ('VARCHAR', 'VARG', 'VARGRAPHIC'):
        length = varIntLength if varIntLength is not None else 50
        # Cap VARCHAR length or use MAX for large lengths
        if length > 8000:
            return "VARCHAR(MAX)"
        return f"VARCHAR({length})"
    elif varStrType in ('DATE', 'TIME', 'TIMESTAMP'):
        return "DATETIME2"
    elif varStrType in ('DOUBLE', 'FLOAT', 'REAL'):
        return "FLOAT"
    else:
        # Default to NVARCHAR(MAX) for unknown types
        return "NVARCHAR(MAX)"

def fun_CreateTable(varObjCursor, varStrSchema, varStrSqlTable, varListCols):
    """Create a new table in the target database with appropriate data types"""
    try:
        # Build column definitions with proper SQL Server data types
        columns_sql = []
        for col in varListCols:
            col_name = col[0]  # Original column name
            col_desc = col[1]  # Column description for naming
            col_type = col[2]  # AS400/MySQL data type
            col_length = col[3]  # Length for character types
            col_precision = col[4]  # Precision for numeric types
            col_scale = col[5]  # Scale for numeric types
            
            # Map to SQL Server data type
            sql_type = fun_MapAS400TypeToSQLType(col_type, col_length, col_precision, col_scale)
            
            # Create column definition with standardized naming pattern
            columns_sql.append(f'[{col_desc}_____{col_name}] {sql_type}')
        
        # Create table statement
        sql = f"""
            CREATE TABLE [{varStrSchema}].[{varStrSqlTable}] (
                {', '.join(columns_sql)}
            )
        """
        
        fun_PrintStatus(varStrSqlTable, "Creating table with proper data types", "process")
        varObjCursor.execute(sql)
        varObjCursor.connection.commit()
        return True
    except Exception as e:
        if "already an object named" in str(e):
            fun_PrintStatus(varStrSqlTable, "Table already exists (possibly created by another process)", "warning")
            return True
        else:
            fun_PrintStatus(varStrSqlTable, f"Error creating table: {str(e)}", "failure")
            return False

def fun_CompareRowCountPerYear(varObjSourceCursor, varObjMSSQLCursor, varStrSourceTable, varStrSqlTable):
    """
    Compare row counts between source and MSSQL tables per fiscal year.
    Returns dictionary with separate conditions for source and MSSQL.
    
    INPUT:
        varObjSourceCursor - Source database cursor
        varObjMSSQLCursor - MSSQL database cursor
        varStrSourceTable - Source table name
        varStrSqlTable - Destination table name in MSSQL
    OUTPUT:
        Dictionary with year ranges and comparison results
    """
    # Get schema name based on source type
    if myDictConfig['SOURCE_TYPE'] == 'AS400':
        varStrSourceSchema = myDictConfig['AS400']['LIBRARY']
    else:
        varStrSourceSchema = myDictConfig['MYSQL']['SCHEMA']
        
    # Detect fiscal year column in source
    varStrSourceFiscalCol = fun_DetectFiscalYearColumn(
        varObjSourceCursor,
        varStrSourceSchema,
        varStrSourceTable
    )
    
    if not varStrSourceFiscalCol:
        fun_PrintStatus(varStrSourceTable, "No fiscal year column found - using full table comparison", "warning")
        return {'FullTable': {'needs_sync': True}}
    
    # Find corresponding MSSQL column name
    try:
        varObjMSSQLCursor.execute(f"""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = '{myDictConfig['SQL_SERVER']['SCHEMA']}'
              AND TABLE_NAME = '{varStrSqlTable}'
              AND COLUMN_NAME LIKE '%{varStrSourceFiscalCol}'
        """)
        varObjResult = varObjMSSQLCursor.fetchone()
        varStrMssqlFiscalCol = varObjResult[0] if varObjResult else None
    except Exception as varExcError:
        fun_PrintStatus(varStrSqlTable, f"Error finding MSSQL fiscal column: {str(varExcError)}", "failure")
        varStrMssqlFiscalCol = None
    
    if not varStrMssqlFiscalCol:
        fun_PrintStatus(varStrSqlTable, f"No matching MSSQL column found for {varStrSourceFiscalCol}", "warning")
        return {'FullTable': {'needs_sync': True}}
    
    varIntCurrentYear = datetime.now().year

    listYearRanges = [
        ("Historical", 
        f"{varStrSourceFiscalCol} <= 12",
        f"TRY_CAST([{varStrMssqlFiscalCol}] AS DECIMAL(18,2)) <= 12")
    ]

    # Add individual years from 2012 to current year
    for year in range(2012, varIntCurrentYear):
        # For AS400 we use 2-digit years, for MySQL we might use 4-digit
        if myDictConfig['SOURCE_TYPE'] == 'AS400':
            source_year = year - 2000  # Convert to 2-digit year for AS400
        else:
            source_year = year  # MySQL might use 4-digit years
            
        listYearRanges.append(
            (str(year),
            f"{varStrSourceFiscalCol} = {source_year}",
            f"TRY_CAST([{varStrMssqlFiscalCol}] AS DECIMAL(18,2)) = {year}")
        )

    # Add current year and beyond
    if myDictConfig['SOURCE_TYPE'] == 'AS400':
        current_source_year = varIntCurrentYear - 2000  # 2-digit
    else:
        current_source_year = varIntCurrentYear  # 4-digit
        
    listYearRanges.append(
        ("Current and Future", 
        f"{varStrSourceFiscalCol} >= {current_source_year}",
        f"TRY_CAST([{varStrMssqlFiscalCol}] AS DECIMAL(18,2)) >= {varIntCurrentYear}")
    )
    
    dictResults = {}
    for varStrLabel, varStrSourceCondition, varStrMssqlCondition in listYearRanges:
        # Get source count
        varIntSourceCount = fun_GetTableRowCountWithCondition(
            varObjSourceCursor, 
            varStrSourceSchema, 
            varStrSourceTable,
            varStrSourceCondition
        )
        
        # Get MSSQL count
        varIntMssqlCount = fun_GetTableRowCountWithCondition(
            varObjMSSQLCursor,
            myDictConfig['SQL_SERVER']['SCHEMA'],
            varStrSqlTable,
            varStrMssqlCondition
        )
        
        dictResults[varStrLabel] = {
            'source_count': varIntSourceCount,
            'mssql_count': varIntMssqlCount,
            'source_condition': varStrSourceCondition,
            'mssql_condition': varStrMssqlCondition,
            'needs_sync': varIntSourceCount != varIntMssqlCount,
            'source_fiscal_col': varStrSourceFiscalCol,
            'mssql_fiscal_col': varStrMssqlFiscalCol
        }
    
    return dictResults

def fun_ConvertValueBasedOnColumnType(val, col_index, column_types):
    """
    Convert a value based on the data type of its column.
    
    INPUT:
        val - The value to convert
        col_index - Index of the column in the row
        column_types - List of column type information
    OUTPUT:
        The converted value
    """
    if val is None:
        return None
        
    # If column_types info is not available, apply basic conversions
    if not column_types or col_index >= len(column_types):
        # Basic conversions
        if isinstance(val, Decimal):
            # Keep decimals as integers if they have no fractional part
            if val % 1 == 0:
                return int(val)
            return float(val)
        return val
        
    # Get column type information
    col_type = column_types[col_index][2].upper() if column_types[col_index][2] else "VARCHAR"
    
    # Apply type-specific conversions
    if col_type in ('DECIMAL', 'DEC', 'NUMERIC', 'NUM', 'INTEGER', 'INT', 'SMALLINT', 'BIGINT'):
        if isinstance(val, Decimal):
            # Preserve integers for whole numbers (prevents .0 suffix)
            if val % 1 == 0:
                return int(val)
            return float(val)
    elif col_type in ('DOUBLE', 'FLOAT', 'REAL'):
        if isinstance(val, (Decimal, int, float)):
            return float(val)
    elif col_type in ('CHAR', 'VARCHAR', 'VARG', 'VARGRAPHIC'):
        # Ensure string representation for character types
        return str(val)
    elif col_type in ('DATE', 'TIME', 'TIMESTAMP'):
        if isinstance(val, datetime):
            return val
        # Try to convert string to datetime if possible
        try:
            return datetime.strptime(str(val), '%Y-%m-%d %H:%M:%S')
        except:
            return val
            
    # Default case - return the value as is
    return val

def fun_BulkInsertYearRange(varObjSourceCursor, varObjMSSQLCursor, varStrSourceTable, varStrSqlTable, varStrYearCondition, varStrFiscalYearCol):
    """
    Bulk insert data for a specific year range with proper data type handling.
    
    INPUT:
        varObjSourceCursor - Source database cursor
        varObjMSSQLCursor - MSSQL database cursor
        varStrSourceTable - Source table name
        varStrSqlTable - Destination table name
        varStrYearCondition - Year range condition
        varStrFiscalYearCol - Fiscal year column name
    OUTPUT:
        Integer - Number of records inserted
    """
    # Get source schema based on source type
    if myDictConfig['SOURCE_TYPE'] == 'AS400':
        varStrSourceSchema = myDictConfig['AS400']['LIBRARY']
    else:
        varStrSourceSchema = myDictConfig['MYSQL']['SCHEMA']
    
    # Get column metadata with type information
    varListColumns = fun_GetOneColumnMetadata(
        varObjSourceCursor, 
        varObjMSSQLCursor,
        varStrSourceSchema, 
        varStrSourceTable
    )
    
    # Get count for progress bar
    varObjCountCursor = varObjSourceCursor.connection.cursor()
    
    if myDictConfig['SOURCE_TYPE'] == 'AS400':
        count_sql = f"""
            SELECT COUNT(*) 
            FROM {varStrSourceSchema}.{varStrSourceTable}
            WHERE {varStrYearCondition}
        """
    else:  # MySQL
        count_sql = f"""
            SELECT COUNT(*) 
            FROM `{varStrSourceSchema}`.`{varStrSourceTable}`
            WHERE {varStrYearCondition}
        """
        
    varObjCountCursor.execute(count_sql)
    varIntTotalRecords = varObjCountCursor.fetchone()[0]
    varObjCountCursor.close()
    
    # Prepare for bulk insert
    varStrColNames = ", ".join([f"[{varTupleCol[1]}_____{varTupleCol[0]}]" for varTupleCol in varListColumns])
    varStrPlaceholders = ", ".join(["?"] * len(varListColumns))
    varIntBatchSize = myDictConfig['BATCH_SIZE']
    varIntTotalInserted = 0

    # Execute source query
    if myDictConfig['SOURCE_TYPE'] == 'AS400':
        query_sql = f"""
            SELECT * 
            FROM {varStrSourceSchema}.{varStrSourceTable}
            WHERE {varStrYearCondition}
        """
    else:  # MySQL
        query_sql = f"""
            SELECT * 
            FROM `{varStrSourceSchema}`.`{varStrSourceTable}`
            WHERE {varStrYearCondition}
        """
        
    varObjSourceCursor.execute(query_sql)

        # Debug code - add right after varObjSourceCursor.execute(query_sql)
    if "GLPPYY = 24" in varStrYearCondition:
        print(f"\n[DEBUG] Starting 2024 data sync...")
        # Get first few records for analysis
        debug_rows = varObjSourceCursor.fetchmany(5)
        varObjSourceCursor.execute(query_sql)  # Re-execute to reset cursor
    
        # Print sample data
        for i, row in enumerate(debug_rows):
            print(f"\n[DEBUG] Sample row {i+1}:")
            for j, val in enumerate(row):
                if j < len(varListColumns):
                    col_name = varListColumns[j][0]
                    col_type = varListColumns[j][2]
                    print(f"  {col_name} ({col_type}): {val} (Type: {type(val).__name__})")

    with tqdm(total=varIntTotalRecords, desc=f"Inserting {varStrSourceTable} {varStrYearCondition}") as varObjProgressBar:
        while True:
            varListBatch = varObjSourceCursor.fetchmany(varIntBatchSize)
            if not varListBatch:
                break
            
                        # Add debug code here - after checking if batch is empty
            if "GLPPYY = 24" in varStrYearCondition and varIntTotalInserted == 0:
                # First batch of 2024 data - add detailed debugging
                print(f"\n[DEBUG] Processing first batch of {len(varListBatch)} records")
                print(f"[DEBUG] Batch size: {varIntBatchSize}")
    
                # Debug the conversion 
                sample_normalized = []
                for row_idx, row in enumerate(varListBatch[:5]):  # Debug first 5 rows
                    print(f"\n[DEBUG] Converting row {row_idx+1}:")
                    sample_row = []
                    for idx, val in enumerate(row):
                        # Get column info
                        col_name = varListColumns[idx][0] if idx < len(varListColumns) else f"Column{idx}"
                        col_type = varListColumns[idx][2] if idx < len(varListColumns) else "Unknown"
            
                        # Convert the value and track
                        try:
                            converted_val = fun_ConvertValueBasedOnColumnType(val, idx, varListColumns)
                            print(f"  {col_name} ({col_type}): {val} → {converted_val}")
                            sample_row.append(converted_val)
                        except Exception as e:
                            print(f"  ERROR converting {col_name}: {str(e)}")
                            raise
        
                    sample_normalized.append(tuple(sample_row))
    
                # Disable fast_executemany for first batch to get better error messages
                print("[DEBUG] Attempting insert with fast_executemany=False")
                varObjMSSQLCursor.fast_executemany = False


            # Convert values with type-aware handling
            varListNormalizedBatch = []
            for row in varListBatch:
                normalized_row = []
                for idx, val in enumerate(row):
                    # Convert the value based on its column type
                    converted_val = fun_ConvertValueBasedOnColumnType(val, idx, varListColumns)
                    normalized_row.append(converted_val)
                
                varListNormalizedBatch.append(tuple(normalized_row))
            
            # Bulk insert
            try:
                varObjMSSQLCursor.fast_executemany = True
                varObjMSSQLCursor.executemany(
                    f"""
                    INSERT INTO [{myDictConfig['SQL_SERVER']['SCHEMA']}].[{varStrSqlTable}]
                    ({varStrColNames}) VALUES ({varStrPlaceholders})
                    """,
                    varListNormalizedBatch
                )
                
                varIntTotalInserted += len(varListNormalizedBatch)
            except Exception as e:
                fun_PrintStatus(varStrSourceTable, f"Batch insert error: {str(e)}", "warning")
                
                # If batch fails, try individual inserts as fallback
                fun_PrintStatus(varStrSourceTable, "Attempting row-by-row insert as fallback", "info")
                successful_rows = 0
                
                for row_idx, row in enumerate(varListNormalizedBatch):
                    try:
                        # Additional validation for problematic rows
                        validated_row = []
                        for idx, val in enumerate(row):
                            if val is None:
                                validated_row.append(None)
                            elif isinstance(val, datetime):
                                # Convert datetime to string to avoid driver issues
                                validated_row.append(val.strftime('%Y-%m-%d %H:%M:%S'))
                            else:
                                validated_row.append(val)
                        
                        # Single row insert
                        varObjMSSQLCursor.execute(
                            f"""
                            INSERT INTO [{myDictConfig['SQL_SERVER']['SCHEMA']}].[{varStrSqlTable}]
                            ({varStrColNames}) VALUES ({varStrPlaceholders})
                            """,
                            tuple(validated_row)
                        )
                        successful_rows += 1
                        varIntTotalInserted += 1
                    except Exception as row_err:
                        fun_PrintStatus(varStrSourceTable, 
                                       f"Row insert error at batch position {row_idx}: {str(row_err)}", 
                                       "warning")
                
                fun_PrintStatus(varStrSourceTable, 
                               f"Row-by-row fallback completed: {successful_rows}/{len(varListNormalizedBatch)} rows inserted", 
                               "info")
            
            varObjProgressBar.update(len(varListBatch))
            
            # Commit periodically
            if varIntTotalInserted % (varIntBatchSize * 10) == 0:
                varObjMSSQLCursor.connection.commit()
                fun_PrintStatus(varStrSourceTable, 
                               f"Inserted {varIntTotalInserted} of {varIntTotalRecords} records for {varStrYearCondition}", 
                               "update")

    # Final commit
    varObjMSSQLCursor.connection.commit()
    return varIntTotalInserted

def fun_FullTableSync(varObjSourceCursor, varObjMSSQLCursor, varStrSourceTable, varStrSqlTable, dictResults):
    """
    Perform full table sync when fiscal year column is not found.
    Handles both AS400 and MySQL as sources with proper data type handling.
    
    INPUT:
        varObjSourceCursor - Source database cursor
        varObjMSSQLCursor - MSSQL database cursor
        varStrSourceTable - Source table name
        varStrSqlTable - Destination table name
        dictResults - Dictionary to update with results
    OUTPUT:
        Dictionary - Updated results with sync details
    """
    try:
        fun_PrintStatus(varStrSourceTable, "Starting full table sync", "process")
        
        # Get source schema based on source type
        if myDictConfig['SOURCE_TYPE'] == 'AS400':
            varStrSourceSchema = myDictConfig['AS400']['LIBRARY']
        else:
            varStrSourceSchema = myDictConfig['MYSQL']['SCHEMA']
            
        # Get total count for progress bar
        varObjCountCursor = varObjSourceCursor.connection.cursor()
        
        if myDictConfig['SOURCE_TYPE'] == 'AS400':
            count_sql = f"SELECT COUNT(*) FROM {varStrSourceSchema}.{varStrSourceTable}"
        else:  # MySQL
            count_sql = f"SELECT COUNT(*) FROM `{varStrSourceSchema}`.`{varStrSourceTable}`"
            
        varObjCountCursor.execute(count_sql)
        varIntTotalRecords = varObjCountCursor.fetchone()[0]
        varObjCountCursor.close()
        
        # Truncate destination table
        varObjMSSQLCursor.execute(f"TRUNCATE TABLE [{myDictConfig['SQL_SERVER']['SCHEMA']}].[{varStrSqlTable}]")
        dictResults['rows_deleted'] = dictResults['initial_mssql_count']
        
        # Get column metadata with type information
        varListColumns = fun_GetOneColumnMetadata(
            varObjSourceCursor,
            varObjMSSQLCursor,
            varStrSourceSchema, 
            varStrSourceTable
        )
        
        # Prepare for bulk insert
        varStrColNames = ", ".join([f"[{varTupleCol[1]}_____{varTupleCol[0]}]" for varTupleCol in varListColumns])
        varStrPlaceholders = ", ".join(["?"] * len(varListColumns))
        varIntBatchSize = myDictConfig['BATCH_SIZE']
        varIntTotalInserted = 0

        # Execute source query
        if myDictConfig['SOURCE_TYPE'] == 'AS400':
            query_sql = f"SELECT * FROM {varStrSourceSchema}.{varStrSourceTable}"
        else:  # MySQL
            query_sql = f"SELECT * FROM `{varStrSourceSchema}`.`{varStrSourceTable}`"
            
        varObjSourceCursor.execute(query_sql)

        with tqdm(total=varIntTotalRecords, desc=f"Inserting {varStrSourceTable}") as varObjProgressBar:
            while True:
                varListBatch = varObjSourceCursor.fetchmany(varIntBatchSize)
                if not varListBatch:
                    break
                
                # Convert values with type-aware handling
                varListNormalizedBatch = []
                for row in varListBatch:
                    normalized_row = []
                    for idx, val in enumerate(row):
                        # Convert the value based on its column type
                        converted_val = fun_ConvertValueBasedOnColumnType(val, idx, varListColumns)
                        normalized_row.append(converted_val)
                    
                    varListNormalizedBatch.append(tuple(normalized_row))
                
                # Bulk insert
                try:
                    varObjMSSQLCursor.fast_executemany = True
                    varObjMSSQLCursor.executemany(
                        f"""
                        INSERT INTO [{myDictConfig['SQL_SERVER']['SCHEMA']}].[{varStrSqlTable}]
                        ({varStrColNames}) VALUES ({varStrPlaceholders})
                        """,
                        varListNormalizedBatch
                    )
                    
                    varIntTotalInserted += len(varListNormalizedBatch)
                except Exception as e:
                    fun_PrintStatus(varStrSourceTable, f"Batch insert error: {str(e)}", "warning")
                    
                    # If batch fails, try individual inserts as fallback
                    fun_PrintStatus(varStrSourceTable, "Attempting row-by-row insert as fallback", "info")
                    successful_rows = 0
                    
                    for row_idx, row in enumerate(varListNormalizedBatch):
                        try:
                            # Additional validation for problematic rows
                            validated_row = []
                            for idx, val in enumerate(row):
                                if val is None:
                                    validated_row.append(None)
                                elif isinstance(val, datetime):
                                    # Convert datetime to string to avoid driver issues
                                    validated_row.append(val.strftime('%Y-%m-%d %H:%M:%S'))
                                else:
                                    validated_row.append(val)
                            
                            # Single row insert
                            varObjMSSQLCursor.execute(
                                f"""
                                INSERT INTO [{myDictConfig['SQL_SERVER']['SCHEMA']}].[{varStrSqlTable}]
                                ({varStrColNames}) VALUES ({varStrPlaceholders})
                                """,
                                tuple(validated_row)
                            )
                            successful_rows += 1
                            varIntTotalInserted += 1
                        except Exception as row_err:
                            fun_PrintStatus(varStrSourceTable, 
                                           f"Row insert error at batch position {row_idx}: {str(row_err)}", 
                                           "warning")
                    
                    fun_PrintStatus(varStrSourceTable, 
                                   f"Row-by-row fallback completed: {successful_rows}/{len(varListNormalizedBatch)} rows inserted", 
                                   "info")
                
                varObjProgressBar.update(len(varListBatch))
                
                # Commit periodically
                if varIntTotalInserted % (varIntBatchSize * 10) == 0:
                    varObjMSSQLCursor.connection.commit()
                    fun_PrintStatus(varStrSourceTable, 
                                   f"Inserted {varIntTotalInserted} of {varIntTotalRecords} records", 
                                   "update")

        # Final commit and update results
        varObjMSSQLCursor.connection.commit()
        dictResults['rows_inserted'] = varIntTotalInserted
        dictResults['final_source_count'] = dictResults['initial_source_count']
        dictResults['final_mssql_count'] = varIntTotalInserted
        
        # Print summary
        fun_PrintSyncSummary(dictResults)
        
        fun_PrintStatus(varStrSourceTable, "Full table sync completed", "success")
        return dictResults
        
    except Exception as varExcError:
        fun_PrintStatus(varStrSourceTable, f"Full sync failed: {str(varExcError)}", "failure")
        varObjMSSQLCursor.connection.rollback()
        dictResults['error'] = str(varExcError)
        return dictResults

def fun_CompareAndSyncTables(varObjSourceCursor, varObjMSSQLCursor, varStrSourceTable, varStrSqlTable):
    """
    Compare and sync tables year by year with detailed reporting.
    Handles both AS400 and MySQL as sources with proper data type handling.
    
    INPUT:
        varObjSourceCursor - Source database cursor
        varObjMSSQLCursor - MSSQL database cursor
        varStrSourceTable - Source table name
        varStrSqlTable - Destination table name
    OUTPUT:
        Dictionary - Results with sync details
    """
    # Add cycle counter variable
    varIntCycleCounter = 1
    
    # Get source schema based on source type
    if myDictConfig['SOURCE_TYPE'] == 'AS400':
        varStrSourceSchema = myDictConfig['AS400']['LIBRARY']
    else:
        varStrSourceSchema = myDictConfig['MYSQL']['SCHEMA']
        
    # Initialize results dictionary with additional table_created flag
    dictResults = {
        'table_name': varStrSourceTable,
        'mssql_table': varStrSqlTable,
        'years': {},
        'initial_source_count': 0,
        'initial_mssql_count': 0,
        'final_source_count': 0,
        'final_mssql_count': 0,
        'rows_deleted': 0,
        'rows_inserted': 0,
        'table_created': False
    }

    try:
        # First check if MSSQL table exists
        table_exists = fun_CheckTableExists(
            varObjMSSQLCursor, 
            myDictConfig['SQL_SERVER']['SCHEMA'],
            varStrSqlTable
        )

        if not table_exists:
            fun_PrintStatus(varStrSourceTable, f"({varIntCycleCounter}) Destination table not found - creating it", "process")
            varIntCycleCounter += 1
            
            try:
                # Get verified column metadata with type information
                varListCols = fun_GetOneColumnMetadata(
                    varObjSourceCursor, 
                    varObjMSSQLCursor,
                    varStrSourceSchema, 
                    varStrSourceTable
                )
                
                # Create the table with proper data types
                table_created = fun_CreateTable(
                    varObjMSSQLCursor,
                    myDictConfig['SQL_SERVER']['SCHEMA'],
                    varStrSqlTable,
                    varListCols
                )
                
                if table_created:
                    dictResults['table_created'] = True
                    fun_PrintStatus(varStrSourceTable, f"({varIntCycleCounter}) Destination table created successfully", "success")
                    varIntCycleCounter += 1
                else:
                    raise Exception("Failed to create destination table")
                    
            except Exception as create_error:
                # If table was created by another process between our check and creation attempt
                if "already an object named" in str(create_error):
                    fun_PrintStatus(varStrSourceTable, f"({varIntCycleCounter}) Table already exists (possibly created by another process)", "warning")
                    varIntCycleCounter += 1
                else:
                    raise create_error  # Re-raise other errors

        # Get initial total counts
        
        # Source total count
        if myDictConfig['SOURCE_TYPE'] == 'AS400':
            count_sql = f"SELECT COUNT(*) FROM {varStrSourceSchema}.{varStrSourceTable}"
        else:  # MySQL
            count_sql = f"SELECT COUNT(*) FROM `{varStrSourceSchema}`.`{varStrSourceTable}`"
            
        varObjSourceCursor.execute(count_sql)
        dictResults['initial_source_count'] = varObjSourceCursor.fetchone()[0]
        
        # MSSQL total count (will be 0 if table was just created)
        varObjMSSQLCursor.execute(f"SELECT COUNT(*) FROM [{myDictConfig['SQL_SERVER']['SCHEMA']}].[{varStrSqlTable}]")
        dictResults['initial_mssql_count'] = varObjMSSQLCursor.fetchone()[0]
        
        fun_PrintStatus(varStrSourceTable, 
                       f"({varIntCycleCounter}) Initial counts - Source: {dictResults['initial_source_count']}, MSSQL: {dictResults['initial_mssql_count']}", 
                       "info")
        varIntCycleCounter += 1

        # If rowcount is equal, we skip
        if (dictResults['initial_source_count'] == dictResults['initial_mssql_count']):
            fun_PrintStatus(varStrSourceTable, 
                        f"({varIntCycleCounter}) Initial counts are equal......... skipping...", 
                        "info")
            varIntCycleCounter += 1
            
            # Set final counts equal to initial counts since no changes were made
            dictResults['final_source_count'] = dictResults['initial_source_count']
            dictResults['final_mssql_count'] = dictResults['initial_mssql_count']
            
            global_table_results.append({
                'table-name': varStrSourceTable,
                'initial_source': dictResults['initial_source_count'],
                'initial_mssql': dictResults['initial_mssql_count'],
                'final_source': dictResults['final_source_count'],
                'final_mssql': dictResults['final_mssql_count'],
                'status': 'skipped',
                'rows_inserted': 0,
                'rows_deleted': 0,
                'table_created': dictResults.get('table_created', False)
            })
            return dictResults

        # Detect fiscal year column
        varStrFiscalYearCol = fun_DetectFiscalYearColumn(
            varObjSourceCursor,
            varStrSourceSchema,
            varStrSourceTable
        )
        
        if not varStrFiscalYearCol:
            fun_PrintStatus(varStrSourceTable, f"({varIntCycleCounter}) No fiscal year column found - performing full table sync", "warning")
            varIntCycleCounter += 1
            return fun_FullTableSync(varObjSourceCursor, varObjMSSQLCursor, varStrSourceTable, varStrSqlTable, dictResults)

        # Find corresponding MSSQL fiscal year column
        try:
            varObjMSSQLCursor.execute(f"""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = '{myDictConfig['SQL_SERVER']['SCHEMA']}'
                  AND TABLE_NAME = '{varStrSqlTable}'
                  AND COLUMN_NAME LIKE '%{varStrFiscalYearCol}'
            """)
            varObjResult = varObjMSSQLCursor.fetchone()
            varStrMssqlFiscalCol = varObjResult[0] if varObjResult else None
        except Exception as varExcError:
            fun_PrintStatus(varStrSqlTable, f"({varIntCycleCounter}) Error finding MSSQL fiscal column: {str(varExcError)}", "warning")
            varIntCycleCounter += 1
            varStrMssqlFiscalCol = None

        # Define year ranges to process
        varIntCurrentYear = datetime.now().year
        
        # For AS400 we use 2-digit years in conditions, for MySQL we might use 4-digit
        if myDictConfig['SOURCE_TYPE'] == 'AS400':
            # Historical range
            listYearRanges = [("Historical", f"{varStrFiscalYearCol} < 12")]  # Before 2012 (11 = 2011, 10 = 2010, etc.)
            
            # Add yearly ranges
            for year in range(2012, varIntCurrentYear + 1):
                listYearRanges.append((str(year), f"{varStrFiscalYearCol} = {year - 2000}"))
                
            # Future years
            listYearRanges.append(("Future", f"{varStrFiscalYearCol} > {varIntCurrentYear - 2000}"))
        else:
            # For MySQL, need to determine if it uses 2 or 4 digit years
            # This is a simplified approach - might need adjustment based on actual MySQL data
            listYearRanges = [("Historical", f"{varStrFiscalYearCol} < 12")]
            
            # Add yearly ranges
            for year in range(2012, varIntCurrentYear + 1):
                listYearRanges.append((str(year), f"{varStrFiscalYearCol} = {year - 2000}"))
                
            # Future years
            listYearRanges.append(("Future", f"{varStrFiscalYearCol} > {varIntCurrentYear - 2000}"))

        # Process each year range
        for varStrLabel, varStrYearCondition in listYearRanges:
            # Get row counts for this year range
            varIntSourceCount = fun_GetTableRowCountWithCondition(
                varObjSourceCursor,
                varStrSourceSchema,
                varStrSourceTable,
                varStrYearCondition
            )
            
            if varStrMssqlFiscalCol:
                varStrMssqlCondition = varStrYearCondition.replace(varStrFiscalYearCol, f"TRY_CAST([{varStrMssqlFiscalCol}] AS DECIMAL(18,2))")
            else:
                varStrMssqlCondition = "1=1"  # Fallback to all records if we can't map the column
            
            varIntMssqlCount = fun_GetTableRowCountWithCondition(
                varObjMSSQLCursor,
                myDictConfig['SQL_SERVER']['SCHEMA'],
                varStrSqlTable,
                varStrMssqlCondition
            )
            
            # Store year results
            dictResults['years'][varStrLabel] = {
                'source_count': varIntSourceCount,
                'mssql_count': varIntMssqlCount,
                'synced': False
            }
            
            fun_PrintStatus(
                varStrSourceTable,
                f"({varIntCycleCounter}) {varStrLabel} {varStrYearCondition} year range - Source: {varIntSourceCount}, MSSQL: {varIntMssqlCount}",
                "info"
            )
            varIntCycleCounter += 1

            # Only sync if counts differ
            if varIntSourceCount != varIntMssqlCount:
                fun_PrintStatus(varStrSourceTable, f"({varIntCycleCounter}) Counts differ - syncing {varStrLabel} year range", "failure")
                varIntCycleCounter += 1
                
                # Delete existing data for this year range in MSSQL
                if varStrMssqlFiscalCol:
                    varObjMSSQLCursor.execute(f"""
                        DELETE FROM [{myDictConfig['SQL_SERVER']['SCHEMA']}].[{varStrSqlTable}]
                        WHERE {varStrMssqlCondition}
                    """)
                    varObjMSSQLCursor.connection.commit()
                    dictResults['rows_deleted'] += varIntMssqlCount
                
                # Insert fresh data from source with proper type handling
                varIntInserted = fun_BulkInsertYearRange(
                    varObjSourceCursor,
                    varObjMSSQLCursor,
                    varStrSourceTable,
                    varStrSqlTable,
                    varStrYearCondition,
                    varStrFiscalYearCol
                )
                
                dictResults['rows_inserted'] += varIntInserted
                dictResults['years'][varStrLabel]['synced'] = True
                dictResults['years'][varStrLabel]['rows_inserted'] = varIntInserted

        # Get final total counts - CRITICAL for accurate reporting
        fun_PrintStatus(varStrSourceTable, f"({varIntCycleCounter}) Getting final row counts", "process")
        varIntCycleCounter += 1
        
        # Source total count
        if myDictConfig['SOURCE_TYPE'] == 'AS400':
            final_source_sql = f"SELECT COUNT(*) FROM {varStrSourceSchema}.{varStrSourceTable}"
        else:  # MySQL
            final_source_sql = f"SELECT COUNT(*) FROM `{varStrSourceSchema}`.`{varStrSourceTable}`"
            
        varObjSourceCursor.execute(final_source_sql)
        dictResults['final_source_count'] = varObjSourceCursor.fetchone()[0]
        
        # MSSQL total count
        varObjMSSQLCursor.execute(f"SELECT COUNT(*) FROM [{myDictConfig['SQL_SERVER']['SCHEMA']}].[{varStrSqlTable}]")
        dictResults['final_mssql_count'] = varObjMSSQLCursor.fetchone()[0]
        
        fun_PrintStatus(varStrSourceTable, 
                       f"({varIntCycleCounter}) Final counts - Source: {dictResults['final_source_count']}, MSSQL: {dictResults['final_mssql_count']}", 
                       "info")
        varIntCycleCounter += 1

        # Add to global results - IMPORTANT: Use the final counts here
        global_table_results.append({
            'table-name': varStrSourceTable,
            'initial_source': dictResults['initial_source_count'],
            'initial_mssql': dictResults['initial_mssql_count'],
            'final_source': dictResults['final_source_count'],  # Updated final count
            'final_mssql': dictResults['final_mssql_count'],    # Updated final count
            'status': 'synced',
            'rows_inserted': dictResults['rows_inserted'],
            'rows_deleted': dictResults['rows_deleted'],
            'table_created': dictResults.get('table_created', False)
        })
        
        return dictResults
    
    except Exception as varExcError:
        fun_PrintStatus(varStrSourceTable, f"({varIntCycleCounter}) Sync failed: {str(varExcError)}", "failure")
        varObjMSSQLCursor.connection.rollback()
        dictResults['error'] = str(varExcError)
        
        # Make sure to set the final counts even in error cases
        dictResults['final_source_count'] = dictResults['initial_source_count']  # Default to initial on error
        dictResults['final_mssql_count'] = dictResults['initial_mssql_count']    # Default to initial on error
        
        # Add failed result to global with proper counts
        global_table_results.append({
            'table-name': varStrSourceTable,
            'initial_source': dictResults['initial_source_count'],
            'initial_mssql': dictResults['initial_mssql_count'],
            'final_source': dictResults['final_source_count'],  # Use updated value
            'final_mssql': dictResults['final_mssql_count'],    # Use updated value
            'status': 'failed',
            'rows_inserted': dictResults.get('rows_inserted', 0),
            'rows_deleted': dictResults.get('rows_deleted', 0),
            'table_created': dictResults.get('table_created', False),
            'error': str(varExcError)
        })
        
        return dictResults


def fun_PrintSyncSummary(dictResults):
    """
    Print detailed sync summary report.
    Works with both AS400 and MySQL as sources.
    
    INPUT:
        dictResults - Results dictionary with sync details
    """
    source_name = "AS400" if myDictConfig['SOURCE_TYPE'] == 'AS400' else "MySQL"
    
    print("\n" + "="*80)
    print(f"SYNC SUMMARY REPORT - {dictResults['table_name']}")
    print("="*80)
    print(f"Source Table ({source_name}): {dictResults['table_name']}")
    print(f"Target Table (MSSQL): {dictResults['mssql_table']}")
    print("-"*80)
    print(f"Initial Source Count: {dictResults.get('initial_source_count', dictResults.get('initial_as400_count', 0))}")
    print(f"Initial MSSQL Count: {dictResults['initial_mssql_count']}")
    print("-"*80)
    
    # Year range details
    print("\nYEAR RANGE SYNC DETAILS:")
    for varStrYearRange, dictYearData in dictResults['years'].items():
        print(f"\n{varStrYearRange}:")
        print(f"  Source Count: {dictYearData.get('source_count', dictYearData.get('as400_count', 0))}")
        print(f"  MSSQL Count: {dictYearData['mssql_count']}")
        if dictYearData.get('synced', False):
            print(f"  ACTION: Synced ({dictYearData.get('rows_inserted', 0)} rows inserted)")
        else:
            print("  ACTION: No sync needed (counts matched)")
    
    print("\n" + "-"*80)
    print(f"Total Rows Deleted: {dictResults.get('rows_deleted', 0)}")
    print(f"Total Rows Inserted: {dictResults.get('rows_inserted', 0)}")
    print("-"*80)
    print(f"Final Source Count: {dictResults.get('final_source_count', dictResults.get('final_as400_count', 0))}")
    print(f"Final MSSQL Count: {dictResults['final_mssql_count']}")
    print("="*80 + "\n")

def fun_PrintFinalSummary():
    """Print a comprehensive summary of all table processing results"""
    source_name = "AS400" if myDictConfig['SOURCE_TYPE'] == 'AS400' else "MySQL"
    
    print("\n" + "="*80)
    print(f"FINAL MIGRATION SUMMARY REPORT: {source_name} to MSSQL")
    print("="*80)
    print(f"{'#':<4}{'Table':<20}{'Initial Source':>15}{'Initial MSSQL':>15}{'Final Source':>15}{'Final MSSQL':>15}{'Status':>15}{'Rows Ins':>10}{'Rows Del':>10}{'Created':>10}")
    print("-"*120)
    
    for idx, result in enumerate(global_table_results, 1):
        # Handle case where result is a set instead of dict
        if isinstance(result, set):
            print(f"{idx:<4}{'INVALID RESULT (set)':<20}{'N/A':>15}{'N/A':>15}{'N/A':>15}{'N/A':>15}{'ERROR':>15}{'N/A':>10}{'N/A':>10}{'N/A':>10}")
            continue
            
        # Safely get all values with defaults
        table_name = str(result.get('table-name', 'UNKNOWN'))[:20]  # Ensure string and slice
        # Rename field names based on source type
        initial_source = result.get('initial_source', result.get('initial_as400', 0))
        initial_mssql = result.get('initial_mssql', 0)
        final_source = result.get('final_source', result.get('final_as400', 0))
        final_mssql = result.get('final_mssql', 0)
        status = result.get('status', 'UNKNOWN')
        rows_inserted = result.get('rows_inserted', 0)
        rows_deleted = result.get('rows_deleted', 0)
        table_created = 'Yes' if result.get('table_created', False) else 'No'

        print(f"{idx:<4}"
              f"{table_name:<20}"
              f"{initial_source:>15}"
              f"{initial_mssql:>15}"
              f"{final_source:>15}"
              f"{final_mssql:>15}"
              f"{status:>15}"
              f"{rows_inserted:>10}"
              f"{rows_deleted:>10}"
              f"{table_created:>10}")

    # Calculate totals - filter out sets first
    valid_results = [r for r in global_table_results if isinstance(r, dict)]
    total_tables = len(global_table_results)
    total_skipped = sum(1 for r in valid_results if r.get('status') == 'skipped')
    total_synced = sum(1 for r in valid_results if r.get('status') == 'synced')
    total_failed = sum(1 for r in valid_results if r.get('status') == 'failed') + \
                  (len(global_table_results) - len(valid_results))  # Count sets as failures
    total_inserted = sum(r.get('rows_inserted', 0) for r in valid_results)
    total_deleted = sum(r.get('rows_deleted', 0) for r in valid_results)
    total_created = sum(1 for r in valid_results if r.get('table_created', False))

    print("-"*120)
    print(f"SUMMARY: Tables={total_tables} | Synced={total_synced} | Skipped={total_skipped} | Failed={total_failed}")
    print(f"         Rows Inserted={total_inserted} | Rows Deleted={total_deleted} | Tables Created={total_created}")
    print("="*80 + "\n")

def fun_ProcessTable(varTupleTableInfo, varObjLogLock, varObjReportLock):
    """
    Process a single table with source to destination synchronization.
    Handles both AS400 and MySQL as sources using pyodbc.
    
    INPUT:
        varTupleTableInfo - Tuple containing (SourceTable, DestinationTable)
        varObjLogLock - Thread lock for logging
        varObjReportLock - Thread lock for report generation
    OUTPUT:
        None - Results added to global_table_results for final reporting
    """
    varObjSourceConn = None
    varObjSqlConn = None
    varStrSourceTable, varStrSqlTable = varTupleTableInfo

    try:
        # Get connections with retry logic
        for _ in range(myDictConfig['MAX_RETRIES']):
            try:
                varObjSourceConn = myObjSourcePool.fun_GetConnection()
                varObjSqlConn = myObjSqlPool.fun_GetConnection()
                break
            except Exception as e:
                time.sleep(myDictConfig['RETRY_DELAY'])
                continue
        
        if not varObjSourceConn or not varObjSqlConn:
            raise Exception("Failed to get database connections")
        
        # DebugInfo
        #with varObjLogLock:
        #    fun_PrintStatus(varStrSqlTable, f"Processing {varStrSourceTable} -> {varStrSqlTable}", "process")        
   
        # Get cursors
        varObjSourceCursor = varObjSourceConn.cursor()
        varObjMSSQLCursor = varObjSqlConn.cursor()
        
        # Compare and sync tables
        dictResults = fun_CompareAndSyncTables(
            varObjSourceCursor,
            varObjMSSQLCursor,
            varStrSourceTable,
            varStrSqlTable)
            
        # Commit changes
        varObjSourceConn.commit()
        varObjSqlConn.commit()
    
    except Exception as varExcError:
        with varObjLogLock:
            fun_PrintStatus(varStrSourceTable, f"Error: {str(varExcError)}", "failure")
            traceback.print_exc()
        
        # Rollback on error
        if varObjSqlConn:
            varObjSqlConn.rollback()
        if varObjSourceConn:
            varObjSourceConn.rollback()
            
        # Add error to global results
        global_table_results.append({
            'table-name': varStrSourceTable,
            'status': 'failed',
            'error': str(varExcError)
        })
            
    finally:
        # Return connections to pool
        if varObjSourceConn:
            myObjSourcePool.sub_ReturnConnection(varObjSourceConn)
        if varObjSqlConn:
            myObjSqlPool.sub_ReturnConnection(varObjSqlConn)

# =============================================
# MAIN EXECUTION SECTION
# =============================================
if __name__ == "__main__":
    try:
        # Initialize
        varStrStartTime = datetime.now().strftime(myConStrTimestampFormat)
        print(f"[{varStrStartTime}] Starting execution")
        fun_PrintStatus("SYSTEM", f"Starting {myDictConfig['SOURCE_TYPE']} to MSSQL migration process", "process")
        
        fun_InitializeConnectionPools()
        
        # Get list of tables to process
        varObjSqlConn = myObjSqlPool.fun_GetConnection()
        try:
            varObjCursor = varObjSqlConn.cursor()
            varListAllTables = []
            
            try:
                # Determine which mapping table to use based on source type
                if myDictConfig['SOURCE_TYPE'] == 'AS400':
                    mappingTable = "01_AS400_MSSQL_Equivalents"
                    sourceColName = "AS400_TableName"
                else:  # MYSQL
                    mappingTable = "01_mysql_MSSQL_Equivalents"
                    sourceColName = "mysql_TableName"
                
                # Query the appropriate equivalents table
                varObjCursor.execute(
                    f"SELECT MSSQL_TableName, {sourceColName} "
                    f"FROM [{myDictConfig['SQL_SERVER']['SCHEMA']}].[{mappingTable}]"
                )
                
                for varTupleRow in varObjCursor.fetchall():
                    # Standardize table name format based on source type
                    if myDictConfig['SOURCE_TYPE'] == 'AS400':
                        varStrStandardizedName = f"z_____{varTupleRow[1]}" if not str(varTupleRow[0]).startswith('z_') else varTupleRow[0]
                    else:  # MYSQL
                        varStrStandardizedName = f"mysql_____{varTupleRow[1]}" if not str(varTupleRow[0]).startswith('mysql_') else varTupleRow[0]
                        
                    varListAllTables.append((varTupleRow[1], varStrStandardizedName))
                    
                fun_PrintStatus("SYSTEM", f"Found {len(varListAllTables)} tables to process", "success")
                
            except Exception as varExcError:
                fun_PrintStatus("SYSTEM", f"Could not query equivalents table: {str(varExcError)}", "failure")
                varListAllTables = []

        finally:
            myObjSqlPool.sub_ReturnConnection(varObjSqlConn)
        
        # Process tables with threading
        varObjLogLock = threading.Lock()
        varObjReportLock = threading.Lock()
        varObjWorkQueue = Queue()
        
        # Populate work queue
        for varTupleTableInfo in varListAllTables:
            varObjWorkQueue.put(varTupleTableInfo)
        
        # Worker function
        def fun_Worker():
            while True:
                try:
                    # First check if queue is empty to avoid debugger breaks
                    if varObjWorkQueue.empty():
                        return
                        
                    varTupleTableInfo = varObjWorkQueue.get_nowait()
                    try:
                        fun_ProcessTable(varTupleTableInfo, varObjLogLock, varObjReportLock)
                    except Exception as e:
                        with varObjLogLock:
                            fun_PrintStatus("WORKER", f"Error processing table: {str(e)}", "failure")
                            traceback.print_exc()
                    finally:
                        varObjWorkQueue.task_done()
                except Empty:
                    # Normal exit when queue is empty
                    return
                except Exception as e:
                    with varObjLogLock:
                        fun_PrintStatus("WORKER", f"Thread failed: {str(e)}", "failure")
                    return
        
        # Start worker threads with improved error handling
        varListActiveThreads = []
        try:
            for _ in range(min(myDictConfig['MAX_THREADS'], len(varListAllTables))):
                varObjThread = threading.Thread(target=fun_Worker, daemon=True)
                varObjThread.start()
                varListActiveThreads.append(varObjThread)
            
            # Wait for completion with timeout
            varObjWorkQueue.join()
            
            # Additional check for thread completion
            for varObjThread in varListActiveThreads:
                varObjThread.join(timeout=5)  # 5 second timeout per thread
                
        except Exception as e:
            fun_PrintStatus("SYSTEM", f"Thread management error: {str(e)}", "failure")
        
        # Clean up
        try:
            myObjSourcePool.sub_CloseAllConnections()
            myObjSqlPool.sub_CloseAllConnections()
        except Exception as e:
            fun_PrintStatus("SYSTEM", f"Cleanup error: {str(e)}", "failure")
        
        varStrEndTime = datetime.now().strftime(myConStrTimestampFormat)
        print(f"[{varStrEndTime}] Execution completed")
        
        # Print final summary
        fun_PrintFinalSummary()
        fun_PrintStatus("SYSTEM", "Migration completed successfully", "success")
        
    except Exception as varExcError:
        fun_PrintStatus("SYSTEM", f"Migration failed: {str(varExcError)}", "failure")
        traceback.print_exc()
        winsound.Beep(1000, 1000)
    finally:
        # Close all connections in pools
        try:
            if 'myObjSourcePool' in globals() and myObjSourcePool:
                myObjSourcePool.sub_CloseAllConnections()
            if 'myObjSqlPool' in globals() and myObjSqlPool:
                myObjSqlPool.sub_CloseAllConnections()
        except Exception as e:
            print(f"Final cleanup error: {str(e)}")
