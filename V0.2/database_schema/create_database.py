import sqlite3
from pathlib import Path

# IDE must be in Version folder before use

SCHEMA_PATH = Path("database_schema\schema.sql")
DB = "database.db" # name of our database

conn = sqlite3.connect(DB) # connects to or creates our database if not exist
cursor = conn.cursor()

conn.executescript(SCHEMA_PATH.read_text())
cursor.execute("PRAGMA foreign_keys = ON;")

cursor.close()
conn.close()
