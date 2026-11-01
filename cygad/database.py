import sqlite3
from pathlib import Path
from .config import DATABASE_PATH, DEFAULT_LANGUAGE

def connect():
    Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DATABASE_PATH)
    db.execute("PRAGMA journal_mode=WAL")
    return db

def init_db():
    with connect() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            language TEXT NOT NULL DEFAULT 'en',
            first_seen TEXT DEFAULT CURRENT_TIMESTAMP,
            last_seen TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')

def touch_user(user_id: int, username: str = ""):
    with connect() as db:
        db.execute('''INSERT INTO users(user_id, username, language)
                      VALUES(?, ?, ?)
                      ON CONFLICT(user_id) DO UPDATE SET
                      username=excluded.username, last_seen=CURRENT_TIMESTAMP''',
                   (user_id, username or "", DEFAULT_LANGUAGE))

def get_language(user_id: int) -> str:
    with connect() as db:
        row = db.execute("SELECT language FROM users WHERE user_id=?", (user_id,)).fetchone()
    return row[0] if row else DEFAULT_LANGUAGE

def set_language(user_id: int, language: str):
    with connect() as db:
        db.execute("UPDATE users SET language=?, last_seen=CURRENT_TIMESTAMP WHERE user_id=?",
                   (language, user_id))

def save_message(user_id: int, role: str, content: str):
    # Keep a short recent history for basic continuity.
    with connect() as db:
        db.execute("INSERT INTO messages(user_id, role, content) VALUES(?, ?, ?)",
                   (user_id, role, content[:12000]))
        db.execute('''DELETE FROM messages WHERE user_id=? AND id NOT IN
                      (SELECT id FROM messages WHERE user_id=? ORDER BY id DESC LIMIT 12)''',
                   (user_id, user_id))

def get_history(user_id: int):
    with connect() as db:
        rows = db.execute(
            "SELECT role, content FROM messages WHERE user_id=? ORDER BY id DESC LIMIT 10",
            (user_id,)
        ).fetchall()
    return [{"role": role, "content": content} for role, content in reversed(rows)]

def clear_history(user_id: int):
    with connect() as db:
        db.execute("DELETE FROM messages WHERE user_id=?", (user_id,))

def counts():
    with connect() as db:
        users = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        messages = db.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    return users, messages
