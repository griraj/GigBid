"""Small durable index; graph checkpoints remain the source of run state."""
import sqlite3
import threading
import time


class RunRegistry:
    def __init__(self, path):
        self.db = sqlite3.connect(str(path), check_same_thread=False)
        self.lock = threading.RLock()
        with self.db:
            self.db.execute('CREATE TABLE IF NOT EXISTS runs (thread_id TEXT PRIMARY KEY, kind TEXT, created REAL)')
            columns = {row[1] for row in self.db.execute('PRAGMA table_info(runs)')}
            if 'owner_id' not in columns:
                self.db.execute("ALTER TABLE runs ADD COLUMN owner_id TEXT NOT NULL DEFAULT 'reviewer'")

    def add(self, thread_id, kind, owner_id='reviewer'):
        with self.lock, self.db:
            self.db.execute('INSERT INTO runs(thread_id,kind,created,owner_id) VALUES (?, ?, ?, ?)',
                            (thread_id, kind, time.time(), owner_id))

    def list(self, kind, limit=100, owner_id='reviewer'):
        with self.lock:
            return self.db.execute('SELECT thread_id, created FROM runs WHERE kind=? AND owner_id=? ORDER BY created DESC LIMIT ?',
                                   (kind, owner_id, limit)).fetchall()

    def owns(self, thread_id: str, owner_id: str) -> bool:
        with self.lock:
            return self.db.execute('SELECT 1 FROM runs WHERE thread_id=? AND owner_id=?',
                                   (thread_id, owner_id)).fetchone() is not None

    def exists(self, thread_id: str) -> bool:
        with self.lock:
            return self.db.execute('SELECT 1 FROM runs WHERE thread_id=?', (thread_id,)).fetchone() is not None
