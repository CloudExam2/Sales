import sqlite3
conn = sqlite3.connect('sales.db')
cursor = conn.cursor()
# Check the last note and its total
cursor.execute("SELECT folio, total FROM sales_notes ORDER BY id DESC LIMIT 1")
print(f"Last Note: {cursor.fetchone()}")
# Check the contents of that note
cursor.execute("SELECT product_id, total FROM note_contents ORDER BY id DESC LIMIT 1")
print(f"Last Item Total: {cursor.fetchone()}")
conn.close()