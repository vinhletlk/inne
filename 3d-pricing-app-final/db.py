import sqlite3
import json
from datetime import datetime

class DBConn:
    def __init__(self, db_path='orders.db'):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                phone TEXT,
                address TEXT,
                email TEXT,
                quote TEXT,
                created_at TEXT
            )''')
            conn.commit()

    def save_order(self, data):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''INSERT INTO orders (name, phone, address, email, quote, created_at)
                         VALUES (?, ?, ?, ?, ?, ?)''', (
                data.get('name',''),
                data.get('phone',''),
                data.get('address',''),
                data.get('email',''),
                json.dumps(data.get('quote',{})),
                datetime.utcnow().isoformat()
            ))
            conn.commit()