import sqlite3
import json

conn = sqlite3.connect('netradar.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get all table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall()]

snapshot = {}
for table in tables:
    cursor.execute(f"SELECT * FROM {table} LIMIT 10")
    rows = cursor.fetchall()
    snapshot[table] = [dict(row) for row in rows]

conn.close()

# Print or save
print(json.dumps(snapshot, indent=2, default=str))

# Or save to file
with open('netradar_snapshot.json', 'w') as f:
    json.dump(snapshot, f, indent=2, default=str)
