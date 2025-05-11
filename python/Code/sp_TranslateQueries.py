import pyodbc
import time
import re
from tqdm import tqdm
import sys

# -----------------------------------------------------------------------------
# 1.- Documentation
#     This script connects to a SQL Server database, extracts terms enclosed
#     in square brackets '[]' from an input SQL query. For each unique term,
#     it executes the stored procedure 'my_sp_getXPfromObjects' to retrieve
#     information. Based on a second input ('code' or 'name'), it returns
#     either the object's code (assumed to be the term itself) or its name
#     (retrieved via the SP, likely from extended properties).
# -----------------------------------------------------------------------------

# --- Constants ---
my_con_str_script_start_message = "Starting execution"
my_con_str_script_end_message = "Finished execution"
my_con_str_open_bracket_regex = r"\[([^\]]+)\]"
my_con_str_sp_name = "my_sp_getXPfromObjects"

# --- Database Connection ---
my_var_str_db_connection_string = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=database-3.c67ymu6q22o1.us-east-1.rds.amazonaws.com;DATABASE=SigmaTB;UID=admin;PWD=Er1c41234$"

# --- Input Constants ---
my_var_str_sql_input = "SELECT [GLTRNT], [GLTRN#] FROM [GLTRANS] WHERE [GLTRN#] IS NOT NULL AND [GLTRANS].[GLACCT] = '12345';"
my_var_str_required_output = "name"  # Change to "code" or "name" as needed

# --- Function Variables ---
my_var_list_results = []
my_var_obj_cnxn = None
my_var_obj_cursor = None
my_var_list_bracketed_terms = []
my_var_set_unique_terms = set()
my_var_int_total_unique_terms = 0
my_var_str_term = ""
my_var_str_sp_query = ""
my_var_tuple_sp_result = None
my_var_str_xp_value = ""
my_var_obj_progress_bar = None
my_var_str_object_code = ""
my_var_str_object_name = ""
my_var_obj_error = None
my_var_str_sql_state = ""
my_var_obj_sp_error = None
my_var_obj_close_error = None
my_var_str_table_name = ""
my_var_str_column_name = ""
my_var_str_object_type = ""

# --- Main Execution Variables ---
my_var_list_output_data = []
my_var_tuple_item = None
my_var_str_modified_query = ""


def fun_get_xp_info(my_var_str_connection_string, my_var_str_sql_statement, my_var_str_output_format):
    """
    Description:
        Connects to SQL Server, extracts bracketed terms from the SQL statement,
        executes a stored procedure for each unique term, and returns requested info.
    Returns:
        tuple: (list of results, output format)
    """
    # --- Input Validation ---
    if my_var_str_output_format.lower() not in ['code', 'name']:
        print(f"-- Error: Invalid output format '{my_var_str_output_format}'. Must be 'code' or 'name'.")
        return [], my_var_str_output_format

    print(f"-- Input SQL Statement: {my_var_str_sql_statement}")
    print(f"-- Requested Output Format: {my_var_str_output_format}")

    try:
        # Command: Connect to the SQL Server database
        print("-- Connecting to the SQL Server database...")
        my_var_obj_cnxn = pyodbc.connect(my_var_str_connection_string, autocommit=True)
        my_var_obj_cursor = my_var_obj_cnxn.cursor()
        print("-- Successfully connected to the database.")

        # Command: Find all text within square brackets
        my_var_list_bracketed_terms = re.findall(my_con_str_open_bracket_regex, my_var_str_sql_statement)
        my_var_set_unique_terms = set(my_var_list_bracketed_terms)
        my_var_int_total_unique_terms = len(my_var_set_unique_terms)
        print(f"-- Found {len(my_var_list_bracketed_terms)} terms within brackets ({my_var_int_total_unique_terms} unique).")

        if not my_var_set_unique_terms:
            print("-- No terms found within square brackets.")
            return [], my_var_str_output_format

        # Control loop: Iterate through each unique bracketed term
        print(f"-- Executing stored procedure '{my_con_str_sp_name}' for each unique term...")
        my_var_obj_progress_bar = tqdm(my_var_set_unique_terms, desc="Querying SP")
        
        for my_var_str_term in my_var_obj_progress_bar:
            my_var_obj_progress_bar.set_postfix({"Term": my_var_str_term})
            my_var_str_xp_value = f"Not Found for {my_var_str_term}"

            try:
                # Determine if this is a table or column reference
                if '.' in my_var_str_term:
                    # This is a column reference [column].[table]
                    my_var_str_column_name, my_var_str_table_name = my_var_str_term.split('.')
                    my_var_str_object_type = "column"
                    my_var_str_lookfor = f"[{my_var_str_column_name}].[{my_var_str_table_name}]"
                else:
                    # This is a table reference [table]
                    my_var_str_table_name = my_var_str_term
                    my_var_str_object_type = "table"
                    my_var_str_lookfor = f"[{my_var_str_table_name}]"

                # Command: Execute the stored procedure with better debugging
                my_var_str_sp_query = f"EXEC {my_con_str_sp_name} @lookfor = ?, @isobject = ?, @returnvalue = ?;"
                print(f"\n-- Debug: Executing query: {my_var_str_sp_query}")
                print(f"-- Debug: With parameters: {my_var_str_lookfor}, {my_var_str_object_type}, {my_var_str_output_format}")
                
                # Execute the stored procedure
                my_var_obj_cursor.execute(my_var_str_sp_query, my_var_str_lookfor, my_var_str_object_type, my_var_str_output_format)
                
                # Debug: Print the SQL that was executed
                print(f"-- Debug: Actual SQL executed: EXEC {my_con_str_sp_name} @lookfor = '{my_var_str_lookfor}', @isobject = '{my_var_str_object_type}', @returnvalue = '{my_var_str_output_format}';")

                # Command: Process all result sets
                my_var_tuple_sp_result = None
                
                # First try to get the first result set
                if my_var_obj_cursor.description:
                    my_var_tuple_sp_result = my_var_obj_cursor.fetchone()
                    print(f"-- Debug: First result set: {my_var_tuple_sp_result}")
                
                # If no result in first set, try next result set
                if not my_var_tuple_sp_result:
                    while my_var_obj_cursor.nextset():
                        if my_var_obj_cursor.description:
                            my_var_tuple_sp_result = my_var_obj_cursor.fetchone()
                            print(f"-- Debug: Next result set: {my_var_tuple_sp_result}")
                            if my_var_tuple_sp_result:
                                break
                
                if my_var_tuple_sp_result:
                    # Check if this is a "Not Found" result
                    if my_var_tuple_sp_result[0] == 'NOT FOUND':
                        print(f"-- Debug: Term not found: {my_var_tuple_sp_result[1]}")
                        my_var_str_xp_value = f"Not Found for {my_var_tuple_sp_result[1]}"
                    else:
                        # The result should be a single value (code or name)
                        my_var_str_xp_value = my_var_tuple_sp_result[0]
                        print(f"-- Debug: Found value: {my_var_str_xp_value}")
                else:
                    print(f"-- Debug: No results found in any result set for term: {my_var_str_term}")
                    my_var_str_xp_value = f"Not Found for {my_var_str_term}"

                # Store the result pair
                my_var_list_results.append((my_var_str_xp_value, my_var_str_term))

            except pyodbc.Error as my_var_obj_sp_error:
                print(f"\n-- Error executing stored procedure for term '{my_var_str_term}': {my_var_obj_sp_error}")
                print(f"-- Debug: Error details: {my_var_obj_sp_error.args}")
                my_var_list_results.append((f"SP Error", my_var_str_term))

        return my_var_list_results, my_var_str_output_format

    except pyodbc.Error as my_var_obj_error:
        my_var_str_sql_state = my_var_obj_error.args[0]
        print(f"-- Error connecting to or querying the database: {my_var_str_sql_state}")
        return [], my_var_str_output_format
    finally:
        # Command: Close the database connection
        if my_var_obj_cnxn:
            try:
                my_var_obj_cnxn.close()
                print("-- Closed database connection")
            except pyodbc.Error as my_var_obj_close_error:
                print(f"-- Error closing database connection: {my_var_obj_close_error}")

# --- Main Execution Block ---
if __name__ == "__main__":
    print(f"{my_con_str_script_start_message}: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Command: Get XP information
    print(f"-- Retrieving XP information...")
    my_var_list_output_data, my_var_str_required_output = fun_get_xp_info(my_var_str_db_connection_string, my_var_str_sql_input, my_var_str_required_output)

    # Command: Output the results
    print("\n-- Results:")
    if my_var_list_output_data:
        # Print header based on input
        header_col1 = "XP Name" if my_var_str_required_output.lower() == 'name' else "XP Code"
        print(f"{header_col1:<50} | {'Original Term':<20}")
        print("-" * 73)
        for my_var_tuple_item in my_var_list_output_data:
            print(f"{str(my_var_tuple_item[0]):<50} | {my_var_tuple_item[1]:<20}")
        
        # Print the modified query
        print("\n-- Modified Query:")
        my_var_str_modified_query = my_var_str_sql_input
        for my_var_tuple_item in my_var_list_output_data:
            my_var_str_modified_query = my_var_str_modified_query.replace(
                f"[{my_var_tuple_item[1]}]", 
                f"[{my_var_tuple_item[0]}]"
            )
        print(my_var_str_modified_query)
    else:
        print("-- No data retrieved.")

    print(f"\n{my_con_str_script_end_message}: {time.strftime('%Y-%m-%d %H:%M:%S')}")