# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import os
from datetime import datetime
from tqdm import tqdm

# -------------------------------------------------------------
# CONSTANTS
# -------------------------------------------------------------
myConStrInputFilePath = r"sql\Insert_into_AS400_MSSQL_Equivalences.sql"
myConStrOutputFilePath = r"sql\Insert_into_AS400_MSSQL_Equivalences_cleaned.sql"

# -------------------------------------------------------------
# FUNCTIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# Function: fun_clean_insert_lines
# Description:
#   Reads a SQL insert file line by line.
#   Replaces spaces with underscores in the portion of each line
#   starting from the first occurrence of "z_".
#   Writes cleaned lines to a new output file.
# Parameters:
#   - myVarStrInputPath: Full path to the input SQL file
#   - myVarStrOutputPath: Full path to save the cleaned SQL file
# Returns:
#   None
# -------------------------------------------------------------
def fun_clean_insert_lines(myVarStrInputPath, myVarStrOutputPath):
    # Local variable declarations
    myVarListLines = []
    myVarIntLineCount = 0

    try:
        # --------------------
        # Step 1: Read all lines
        # --------------------
        with open(myVarStrInputPath, 'r', encoding='utf-8') as myVarObjInFile:
            myVarListLines = myVarObjInFile.readlines()
            myVarIntLineCount = len(myVarListLines)

        # --------------------
        # Step 2: Process lines and write to output
        # --------------------
        with open(myVarStrOutputPath, 'w', encoding='utf-8') as myVarObjOutFile:
            print(f"Processing {myVarIntLineCount} lines...\n")
            for myVarStrLine in tqdm(myVarListLines, desc="Cleaning SQL lines"):
                myVarIntStart = myVarStrLine.find("z_")
                if myVarIntStart != -1:
                    myVarStrPrefix = myVarStrLine[:myVarIntStart]
                    myVarStrSuffix = myVarStrLine[myVarIntStart:].replace(" ", "_")
                    myVarStrCleaned = myVarStrPrefix + myVarStrSuffix
                else:
                    myVarStrCleaned = myVarStrLine

                myVarObjOutFile.write(myVarStrCleaned)

        # --------------------
        # Final status
        # --------------------
        print(f"\n✅ File cleaned and saved to: {myVarStrOutputPath}")

    except Exception as myVarObjErr:
        print(f"❌ ERROR: Failed to clean file.\nDescription: {str(myVarObjErr)}")


# -------------------------------------------------------------
# MAIN EXECUTION
# -------------------------------------------------------------
if __name__ == "__main__":
    # Print start timestamp
    print(f"\n--- Starting execution at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")

    # Run the cleaning function
    fun_clean_insert_lines(myConStrInputFilePath, myConStrOutputFilePath)

    # Print end timestamp
    print(f"\n--- Finished execution at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
