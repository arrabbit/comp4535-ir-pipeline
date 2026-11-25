"""
Summary: Creates a new fake users password database (deleting the old one if it
         exists) with a users table and sessions table.

File: seed.py
Authors: Anna Running Rabbit
"""

import hashlib, os, sqlite3

DB_PATH = "app.db"
USERS = [("s.moon", "Usagi Tsukino", "Sailor Guardian"),
         ("t.mask", "Mamoru Chiba", "Sailor Support"),
         ("s.mercury", "Ami Mizuno", "Sailor Guardian"),
         ("s.mars", "Rei Hino", "Sailor Guardian"),
         ("s.jupiter", "Makoto Kino", "Sailor Guardian"),
         ("s.venus", "Minako Aino", "Sailor Guardian"),
         ("s.chibimoon", "Chibiusa Tsukino", "Sailor Guardian"),
         ("s.uranus", "Haruka Tenoh", "Outer Senshi"),
         ("s.neptune", "Michiru Kaiou", "Outer Senshi"),
         ("s.pluto", "Setsuna Meioh", "Outer Senshi"),
         ("s.saturn", "Hotaru Tomoe", "Outer Senshi"),
         ("c.luna", "Luna", "Sailor Support"),
         ("c.artemis", "Artemis", "Sailor Support"),
         ("c.diana", "Diana", "Sailor Support"),
         ("s.fighter", "Seiya Kou", "Starlight Division"),
         ("s.maker", "Taiki Kou", "Starlight Division"),
         ("s.healer", "Yaten Kou", "Starlight Division"),
         ("q.beryl", "Queen Beryl", "Dark Kingdom"),
         ("g.jadeite", "Jadeite", "Dark Kingdom"),
         ("g.kunzite", "Kunzite", "Dark Kingdom")
        ]

# Deletes the old database if there is one
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
conn.execute("""CREATE TABLE users (
    id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_md5 TEXT,
    full_name TEXT, email TEXT, phone TEXT, department TEXT)""")
conn.execute("""CREATE TABLE sessions (
    sid TEXT PRIMARY KEY, username TEXT NOT NULL, created_utc TEXT NOT NULL)""")

for i, (username, full_name, dept) in enumerate(USERS, start=1):
    # build user password as "<username>123", then convert to bytes and hash
    pw = hashlib.md5(f"{username}123".encode()).hexdigest()
    
    # build user email as "<username>@crystaltokyo.example"
    email = f"{username}@crystaltokyo.example"
    
    # build unique user phone number using a counter "403-555-01##"
    phone = f"403-555-01{i:02d}"
    
    conn.execute(
        "INSERT INTO users (username, password_md5, full_name, email, phone, department) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (username, pw, full_name, email, phone, dept))
    
conn.commit()
conn.close()
print("Seeded", len(USERS), "users")