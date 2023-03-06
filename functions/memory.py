import sqlite3
import os
import json
import time
import torch
import numpy as np
from annoy import AnnoyIndex
from sentence_transformers import SentenceTransformer, util

# text2vector model
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
# annoy
f = 384
t = AnnoyIndex(f, "angular")
# db
db_name = 'database.db'
db_path = os.path.join(os.path.dirname(__file__), db_name)

def text2vector(text):
    return model.encode(text)

def initialize_annoy():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    result = c.execute("""SELECT id, vector FROM memory;""")
    for row in result:
        t.add_item(row[0], json.loads(row[1]))
    t.build(10)

def search_annoy(text, n=3):
    v = text2vector(text)
    return t.get_nns_by_vector(v, n)

def update_annoy(id, vector):
    t.add_item(id, vector)
    t.unbuild()
    t.build(10)

def initialize_table():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT not null,
        created_at INTEGER not null,
        vector TEXT not null
    );
    """)
    conn.commit()
    conn.close()

def memory(text):
    vector = text2vector(text)
    vector_json = json.dumps(vector.tolist())
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    result = c.execute("""
    INSERT INTO memory (text, created_at, vector) VALUES (?, ?, ?);
    """, (text, time.time(), vector_json))
    conn.commit()
    conn.close()
    update_annoy(result.lastrowid, vector)

# search text in memory. When text split by comma, search each text
# search limit is 3
# result array is like ["%Y-%m-%d %H:%M:%S text", "..."]
def search_memory(text, n=3):
    # get ids
    vector = text2vector(text)
    ids = t.get_nns_by_vector(vector, n)
    # get text
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
    SELECT id, text, created_at FROM memory WHERE id IN ({});
    """.format(','.join('?' * len(ids))), ids)
    result = c.fetchall()
    conn.close()
    # parse result
    parse_datetime = lambda x: time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(x))
    data = {}
    for row in result:
        data[row[0]] = {
            "text": row[1],
            "created_at": parse_datetime(row[2])
        }
    return [data[id]["created_at"] + " " + data[id]["text"] for id in ids]

initialize_table()
initialize_annoy()
