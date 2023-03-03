import sqlite3
import os
import time

db_name = 'memory.db'
db_path = os.path.join(os.path.dirname(__file__), db_name)

def initialize_table():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT not null,
        created_at INTEGER not null
    );
    """)
    conn.commit()
    conn.close()

def memory(text):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
    INSERT INTO memory (text, created_at) VALUES (?, ?);
    """, (text, int(time.time())))
    conn.commit()
    conn.close()

# search text in memory. When text split by comma, search each text
# search limit is 3
def search_memory(text):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    search_words = [f'%{t.strip()}%' for t in text.split(',')]
    like_query = " AND ".join(["text LIKE ?" for _ in search_words])
    c.execute(f"""
    SELECT (text) FROM memory WHERE {like_query} ORDER BY created_at DESC LIMIT 3;
    """, search_words)
    result = c.fetchall()
    conn.close()
    return str([r[0] for r in result])

initialize_table()
