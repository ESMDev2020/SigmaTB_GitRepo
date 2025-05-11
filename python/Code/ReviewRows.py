import pyodbc
import time

# ✅ Database connection
conn_str = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=database-3.c67ymu6q22o1.us-east-1.rds.amazonaws.com;"
    "Database=SigmaTB;"
    "UID=admin;"
    "PWD=Er1c41234$;"  # 🔐 Be sure to secure this in real deployments
)

print(time.strftime("%H:%M:%S"), "About to connect")
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

print(time.strftime("%H:%M:%S"), "Connected, about to execute the query")

# Fetch rows that need trimming
cursor.execute("""
    SELECT GLTRN#, GLREF
    FROM GLTRANS
    WHERE GLREF <> LTRIM(RTRIM(GLREF))
""")

print(time.strftime("%H:%M:%S"), "Query executed, processing rows...\n")

# Go row by row with timing
row_count = 0
total_start = time.time()
print(time.strftime("%H:%M:%S"), "About to fetch one...\n")

while True:
    row = cursor.fetchone()
    print(time.strftime("%H:%M:%S"), "Fetched one...\n")
    if row is None:
        print(time.strftime("%H:%M:%S"), "Got no rows...\n")
        break

    print(time.strftime("%H:%M:%S"), "Got one row...\n")
    gltrn = row[0]
    glref_original = row[1] or ""  # handle None
    glref_trimmed = glref_original.strip()

    start = time.time()

    print(time.strftime("%H:%M:%S"), "About to execute the update...\n")
    cursor.execute("""
        UPDATE GLTRANS
        SET GLREF = ?
        WHERE GLTRN# = ?
    """, (glref_trimmed, gltrn))
    conn.commit()  # commit per row so you see true duration

    duration = time.time() - start
    row_count += 1
    print(time.strftime("%H:%M:%S"), f"{row_count:>5}: GLTRN# {gltrn} — {duration:.3f}s — '{glref_original}' ➜ '{glref_trimmed}'")

total_duration = time.time() - total_start
print(time.strftime("%H:%M:%S"), f"\n✅ Done. {row_count} rows updated in {total_duration:.2f} seconds.")

cursor.close()
conn.close()
