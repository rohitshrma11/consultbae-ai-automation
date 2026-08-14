import sqlite3
import pandas as pd

conn = sqlite3.connect("database/consultbae.db")

# Show all tables
tables = pd.read_sql_query(
    """
    SELECT name
    FROM sqlite_master
    WHERE type='table'
    ORDER BY name;
    """,
    conn
)

print("\n===== DATABASE TABLES =====")
print(tables.to_string(index=False))


# Master people
people = pd.read_sql_query(
    "SELECT * FROM people",
    conn
)

# Source table counts
naukri_count = pd.read_sql_query(
    "SELECT COUNT(*) AS total FROM naukri_applicants",
    conn
).iloc[0]["total"]

gig_count = pd.read_sql_query(
    "SELECT COUNT(*) AS total FROM gig_workers",
    conn
).iloc[0]["total"]

cbnexus_count = pd.read_sql_query(
    "SELECT COUNT(*) AS total FROM cbnexus_contacts",
    conn
).iloc[0]["total"]


print("\n================================")
print("FINAL DATABASE VALIDATION")
print("================================")

print("Unique people :", len(people))
print("Naukri rows   :", naukri_count)
print("Gig rows      :", gig_count)
print("CBNexus rows  :", cbnexus_count)

conn.close()