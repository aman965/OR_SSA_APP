import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend', 'db.sqlite3')

print(f"Connecting to database at: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("UPDATE core_scenario SET status = 'created'")
updated_rows = cursor.rowcount
conn.commit()

print(f"Reset {updated_rows} scenarios to 'created' status")

conn.close()
