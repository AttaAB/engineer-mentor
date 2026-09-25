import sqlite3

conn = sqlite3.connect("links.db", check_same_thread=False)
conn.execute("CREATE TABLE IF NOT EXISTS links (code TEXT, url TEXT, created_at TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS clicks (code TEXT, ts TEXT, user_agent TEXT)")
