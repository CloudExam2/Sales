import sqlite3
import pytest

from Sales.src.crud.sales import save_sale

def test_sqlite_connection():
    # Use an in-memory db for fast testing
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE sales_notes (id INTEGER PRIMARY KEY, folio TEXT, total REAL)")
    cursor.execute("INSERT INTO sales_notes (folio, total) VALUES ('F-001', 100.50)")
    
    cursor.execute("SELECT folio FROM sales_notes WHERE id = 1")
    result = cursor.fetchone()
    assert result[0] == 'F-001'
    conn.close()