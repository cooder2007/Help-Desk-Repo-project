"""
database.py — SQLite setup and helper functions
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "helpdesk.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # rows behave like dicts
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT    NOT NULL,
            email         TEXT    UNIQUE NOT NULL,
            password_hash TEXT    NOT NULL,
            role          TEXT    NOT NULL CHECK(role IN ('student','teacher','admin','hod')),
            admin_type    TEXT,                  -- Dean, Coordinator, Director, etc.
            department    TEXT,
            semester      INTEGER,               -- students only
            class_section TEXT,                  -- students only  e.g. BCA-A
            subject       TEXT,                  -- teachers only
            classes_taught TEXT,                 -- teachers: JSON array string
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS tokens (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            title         TEXT    NOT NULL,
            description   TEXT    NOT NULL,
            level         TEXT    NOT NULL
                          CHECK(level IN ('class','semester','intra_dept','inter_dept','university')),
            created_by    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            department    TEXT,
            semester      INTEGER,
            class_section TEXT,
            upvote_count  INTEGER DEFAULT 0,
            status        TEXT    DEFAULT 'open'
                          CHECK(status IN ('open','in_progress','resolved','closed')),
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS replies (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            token_id   INTEGER NOT NULL REFERENCES tokens(id) ON DELETE CASCADE,
            author_id  INTEGER NOT NULL REFERENCES users(id),
            message    TEXT    NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS upvotes (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            token_id INTEGER NOT NULL REFERENCES tokens(id) ON DELETE CASCADE,
            user_id  INTEGER NOT NULL REFERENCES users(id),
            UNIQUE(token_id, user_id)
        );

        CREATE INDEX IF NOT EXISTS idx_tokens_level      ON tokens(level);
        CREATE INDEX IF NOT EXISTS idx_tokens_dept       ON tokens(department);
        CREATE INDEX IF NOT EXISTS idx_tokens_semester   ON tokens(semester);
        CREATE INDEX IF NOT EXISTS idx_tokens_class      ON tokens(class_section);
        CREATE INDEX IF NOT EXISTS idx_tokens_created_by ON tokens(created_by);
        """)
    print("✅  Database initialised at", DB_PATH)


def row_to_dict(row):
    return dict(row) if row else None


def rows_to_list(rows):
    return [dict(r) for r in rows]
