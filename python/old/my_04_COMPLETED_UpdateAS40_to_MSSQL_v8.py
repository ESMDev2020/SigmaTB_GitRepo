# -*- coding: utf-8 -*-
"""
COMPLETE DATABASE SYNCHRONIZATION SCRIPT
DOCUMENTATION: Synchronizes data between source database (AS400 or MySQL) and MSSQL 
               using year-based partitioning with automatic fiscal year column detection.
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
    # MySQL settings (new section for MySQL support)
    'MYSQL': {
        'DRIVER': "{MySQL ODBC 8.0 Unicode Driver}",  # Adjust driver name as needed
        'SERVER': "localhost",
        'PORT': "3306",
        'DATABASE': "dwdata",
        'UID': "user",
        'PWD': "password",
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
    'SOURCE_TYPE': 'MYSQL',  # 'AS400' or 'MYSQL'
    
    # Operation settings
    'BATCH_SIZE': 10000,
    'MAX_THREADS': 20,
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
        varStrConnString = (
            f"DRIVER={myDictConfig['MYSQL']['DRIVER']};"
            f"SERVER={myDictConfig['MYSQL']['SERVER']};"
            f"PORT={myDictConfig['MYSQL']['PORT']};"
            f"DATABASE={myDictConfig['MYSQL']['DATABASE']};"
            f"UID={myDictConfig['MYSQL']['UID']};"
            f"PWD={myDictConfig['MYSQL']['PWD']};"
        )
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
    Retrieve column names and descriptions with fallback to actual structure.
    INPUT:
        varObjSourceCursor - Source database cursor (AS400 or MySQL)
        varObjMSSQLCursor - MSSQL cursor
        varStrSchema - Schema name
        varStrTable - Table name
    OUTPUT:
        List of tuples (column_name, column_description)
    """
    try:
        # Different metadata queries based on source type
        if myDictConfig['SOURCE_TYPE'] == 'AS400':
            # AS400 metadata query
            varObjSourceCursor.execute(f"""
                SELECT COLUMN_NAME, COLUMN_TEXT FROM QSYS2.SYSCOLUMNS
                WHERE TABLE_SCHEMA = '{varStrSchema}' AND TABLE_NAME = '{varStrTable}'
                ORDER BY ORDINAL_POSITION
            """)
            varListMetadataCols = [
                (col[0].strip(), (col[1] or "").strip().replace(" ", "_").replace("'", "_").replace(']', ']]').replace('?', 'q')) 
                for col in varObjSourceCursor.fetchall()
            ]
        else:  # MYSQL
            # MySQL metadata query
            varObjSourceCursor.execute(f"""
                SELECT COLUMN_NAME, COLUMN_COMMENT 
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = '{varStrSchema}' AND TABLE_NAME = '{varStrTable}'
                ORDER BY ORDINAL_POSITION
            """)
            varListMetadataCols = [
                (col[0].strip(), (col[1] or col[0]).strip().replace(" ", "_").replace("'", "_").replace(']', ']]').replace('?', 'q')) 
                for col in varObjSourceCursor.fetchall()
            ]
        
        # Get actual columns to verify
        varListActualCols = fun_GetActualColumnNames(varObjSourceCursor, varStrSchema, varStrTable)
        
        if len(varListMetadataCols) != len(varListActualCols):
            fun_PrintStatus(varStrTable, "Metadata mismatch - Using actual column names", "warning")
            return [(col, col) for col in varListActualCols]
        
        return varListMetadataCols
    except Exception as varExcError:
        fun_PrintStatus(varStrTable, f"Metadata query failed: {str(varExcError)} - Using actual names", "warning")
        varListActualCols = fun_GetActualColumnNames(varObjSourceCursor, varStrSchema, varStrTable)
        return [(col, col) for col in varListActualCols]

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

def fun_CreateTable(varObjCursor, varStrSchema, varStrSqlTable, varListCols):
    """Create a new table in the target database"""
    try:
        columns_sql = ', '.join([f'[{col[1]}_____{col[0]}] NVARCHAR(MAX)' for col in varListCols])
        sql = f"""
            CREATE TABLE [{varStrSchema}].[{varStrSqlTable}] (
                {columns_sql}
            )
        """
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

def fun_BulkInsertYearRange(varObjSourceCursor, varObjMSSQLCursor, varStrSourceTable, varStrSqlTable, varStrYearCondition, varStrFiscalYearCol):
    """
    Bulk insert data for a specific year range.
    
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
    
    # Get column metadata
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

    with tqdm(total=varIntTotalRecords, desc=f"Inserting {varStrSourceTable} {varStrYearCondition}") as varObjProgressBar:
        while True:
            varListBatch = varObjSourceCursor.fetchmany(varIntBatchSize)
            if not varListBatch:
                break
            
            # Safe conversion of values with NULL handling
            varListNormalizedBatch = []
            for row in varListBatch:
                normalized_row = []
                for val in row:
                    # First check if the value is None to avoid any comparison issues
                    if val is None:
                        normalized_row.append(None)
                    # Convert Decimal to float for MSSQL, safely handling potential errors
                    elif isinstance(val, Decimal):
                        try:
                            normalized_row.append(float(val))
                        except (TypeError, ValueError):
                            # If conversion fails, use None
                            normalized_row.append(None)
                    # Keep everything else as-is
                    else:
                        normalized_row.append(val)
                
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
                
                for row in varListNormalizedBatch:
                    try:
                        # Additional validation for problematic rows
                        validated_row = []
                        for val in row:
                            if val is None:
                                validated_row.append(None)
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
                        fun_PrintStatus(varStrSourceTable, f"Row insert error: {str(row_err)}", "warning")
                
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
    Handles both AS400 and MySQL as sources.
    
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
        
        # Get column metadata
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
                
                # Safe conversion of values with NULL handling
                varListNormalizedBatch = []
                for row in varListBatch:
                    normalized_row = []
                    for val in row:
                        # First check if the value is None to avoid any comparison issues
                        if val is None:
                            normalized_row.append(None)
                        # Convert Decimal to float for MSSQL, safely handling potential errors
                        elif isinstance(val, Decimal):
                            try:
                                normalized_row.append(float(val))
                            except (TypeError, ValueError):
                                # If conversion fails, use None
                                normalized_row.append(None)
                        # Keep everything else as-is
                        else:
                            normalized_row.append(val)
                    
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
                    
                    for row in varListNormalizedBatch:
                        try:
                            # Additional validation for problematic rows
                            validated_row = []
                            for val in row:
                                if val is None:
                                    validated_row.append(None)
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
                            fun_PrintStatus(varStrSourceTable, f"Row insert error: {str(row_err)}", "warning")
                    
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
    Handles both AS400 and MySQL as sources.
    
    INPUT:
        varObjSourceCursor - Source database cursor
        varObjMSSQLCursor - MSSQL database cursor
        varStrSourceTable - Source table name
        varStrSqlTable - Destination table name
    OUTPUT:
        Dictionary - Results with sync details
    """
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
        
    table_result = {
        'table_name': varStrSourceTable,
        'initial_source': 0,
        'initial_mssql': 0,
        'final_source': 0,
        'final_mssql': 0,
        'status': 'error',
        'rows_inserted': 0,
        'rows_deleted': 0,
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
            fun_PrintStatus(varStrSourceTable, "Destination table not found - creating it", "process")
            
            try:
                # Get verified column metadata
                varListCols = fun_GetOneColumnMetadata(
                    varObjSourceCursor, 
                    varObjMSSQLCursor,
                    varStrSourceSchema, 
                    varStrSourceTable
                )
                
                # Create the table
                table_created = fun_CreateTable(
                    varObjMSSQLCursor,
                    myDictConfig['SQL_SERVER']['SCHEMA'],
                    varStrSqlTable,
                    varListCols
                )
                
                if table_created:
                    dictResults['table_created'] = True
                    fun_PrintStatus(varStrSourceTable, "Destination table created successfully", "success")
                else:
                    raise Exception("Failed to create destination table")
                    
            except Exception as create_error:
                # If table was created by another process between our check and creation attempt
                if "already an object named" in str(create_error):
                    fun_PrintStatus(varStrSourceTable, "Table already exists (possibly created by another process)", "warning")
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
                       f"Initial counts - Source: {dictResults['initial_source_count']}, MSSQL: {dictResults['initial_mssql_count']}", 
                       "info")

        # Report
        initial_source = dictResults['initial_source_count']
        initial_mssql = dictResults['initial_mssql_count']
        table_result.update({
            'initial_source': initial_source,
            'initial_mssql': initial_mssql,
            'final_source': initial_source,  # Default to same as initial
            'final_mssql': initial_mssql     # Default to same as initial
        })

        # If rowcount is equal, we skip
        if (dictResults['initial_source_count'] == dictResults['initial_mssql_count']):
            fun_PrintStatus(varStrSourceTable, 
                        f"Initial counts are equal......... skipping...", 
                        "info")
            global_table_results.append({
                'table-name': varStrSourceTable,
                'initial_source': dictResults['initial_source_count'],
                'initial_mssql': dictResults['initial_mssql_count'],
                'final_source': dictResults['initial_source_count'],
                'final_mssql': dictResults['initial_mssql_count'],
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
            fun_PrintStatus(varStrSourceTable, "No fiscal year column found - performing full table sync", "warning")
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
            fun_PrintStatus(varStrSqlTable, f"Error finding MSSQL fiscal column: {str(varExcError)}", "warning")
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
                f"{varStrLabel} {varStrYearCondition} year range - Source: {varIntSourceCount}, MSSQL: {varIntMssqlCount}",
                "info"
            )

            # Only sync if counts differ
            if varIntSourceCount != varIntMssqlCount:
                fun_PrintStatus(varStrSourceTable, f"Counts differ - syncing {varStrLabel} year range", "failure")
                
                # Delete existing data for this year range in MSSQL
                if varStrMssqlFiscalCol:
                    varObjMSSQLCursor.execute(f"""
                        DELETE FROM [{myDictConfig['SQL_SERVER']['SCHEMA']}].[{varStrSqlTable}]
                        WHERE {varStrMssqlCondition}
                    """)
                    varObjMSSQLCursor.connection.commit()
                    dictResults['rows_deleted'] += varIntMssqlCount
                
                # Insert fresh data from source
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

        # Get final total counts
        fun_PrintStatus(varStrSourceTable, "Getting final row counts", "process")
        
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
                       f"Final counts - Source: {dictResults['final_source_count']}, MSSQL: {dictResults['final_mssql_count']}", 
                       "info")

        # Update the result with sync details
        table_result.update({
            'final_source': dictResults.get('final_source_count', initial_source),
            'final_mssql': dictResults.get('final_mssql_count', initial_mssql),
            'status': 'synced',
            'rows_inserted': dictResults.get('rows_inserted', 0),
            'rows_deleted': dictResults.get('rows_deleted', 0),
            'table_created': dictResults.get('table_created', False)
        })
        
        # Add to global results
        global_table_results.append({
            'table-name': varStrSourceTable,
            'initial_source': dictResults['initial_source_count'],
            'initial_mssql': dictResults['initial_mssql_count'],
            'final_source': dictResults['final_source_count'],
            'final_mssql': dictResults['final_mssql_count'],
            'status': 'synced',
            'rows_inserted': dictResults.get('rows_inserted', 0),
            'rows_deleted': dictResults.get('rows_deleted', 0),
            'table_created': dictResults.get('table_created', False)
        })
        
        return dictResults
    
    except Exception as varExcError:
        fun_PrintStatus(varStrSourceTable, f"Sync failed: {str(varExcError)}", "failure")
        varObjMSSQLCursor.connection.rollback()
        dictResults['error'] = str(varExcError)
        
        # Add failed result to global
        global_table_results.append({
            'table-name': varStrSourceTable,
            'initial_source': dictResults.get('initial_source_count', 0),
            'initial_mssql': dictResults.get('initial_mssql_count', 0),
            'final_source': dictResults.get('initial_source_count', 0),
            'final_mssql': dictResults.get('initial_mssql_count', 0),
            'status': 'failed',
            'rows_inserted': 0,
            'rows_deleted': 0,
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
        
        with varObjLogLock:
            fun_PrintStatus(varStrSqlTable, f"Processing {varStrSourceTable} -> {varStrSqlTable}", "process")        
   
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