import sqlite3


class Database:
    def __init__(self, db_path: str = "reels_studio.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_tables()

    def _create_tables(self):
        cur = self.conn.cursor()
        cur.execute(
            """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            password_salt TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""
        )
        cur.execute(
            """CREATE TABLE IF NOT EXISTS reels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            topic TEXT NOT NULL,
            script TEXT,
            caption TEXT,
            hashtags TEXT,
            status TEXT DEFAULT 'Draft',
            output_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE)"""
        )
        self.conn.commit()
        cur.close()

    def register_user(self, full_name, email, password_hash, password_salt):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO users (full_name, email, password_hash, password_salt) VALUES (?, ?, ?, ?)",
            (full_name, email, password_hash, password_salt),
        )
        self.conn.commit()
        cur.close()

    def get_user(self, email):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=?", (email,))
        row = cur.fetchone()
        cur.close()
        return dict(row) if row else None

    def add_reel(self, user_id, title, topic, script, caption, hashtags):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO reels (user_id, title, topic, script, caption, hashtags) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, title, topic, script, caption, hashtags),
        )
        self.conn.commit()
        cur.close()

    def get_reels(self, user_id):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM reels WHERE user_id=? ORDER BY id DESC", (user_id,))
        rows = cur.fetchall()
        cur.close()
        return [dict(r) for r in rows]

    def set_video_path(self, reel_id, path):
        cur = self.conn.cursor()
        cur.execute("UPDATE reels SET output_path=?, status='Rendered' WHERE id=?", (path, reel_id))
        self.conn.commit()
        cur.close()

    def delete_reel(self, reel_id, user_id):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM reels WHERE id=? AND user_id=?", (reel_id, user_id))
        self.conn.commit()
        cur.close()