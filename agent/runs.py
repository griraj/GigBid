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

    def add(self, thread_id, kind):
        with self.lock, self.db:
            self.db.execute('INSERT INTO runs VALUES (?, ?, ?)', (thread_id, kind, time.time()))

    def list(self, kind, limit=100):
        with self.lock:
            return self.db.execute('SELECT thread_id, created FROM runs WHERE kind=? ORDER BY created DESC LIMIT ?', (kind, limit)).fetchall()
