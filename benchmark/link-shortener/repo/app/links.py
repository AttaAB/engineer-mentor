import random
import string
from datetime import datetime

from app.db import conn

ALPHABET = string.ascii_letters + string.digits


def generate_code(length=6):
    return "".join(random.choice(ALPHABET) for _ in range(length))


def create_link(url):
    while True:
        code = generate_code()
        row = conn.execute("SELECT 1 FROM links WHERE code = ?", (code,)).fetchone()
        if row is None:
            break
    conn.execute(
        "INSERT INTO links (code, url, created_at) VALUES (?, ?, ?)",
        (code, url, datetime.utcnow().isoformat()),
    )
    conn.commit()
    return code


def resolve_link(code):
    row = conn.execute("SELECT url FROM links WHERE code = ?", (code,)).fetchone()
    return row[0] if row else None
