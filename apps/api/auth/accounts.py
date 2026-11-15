"""Persistent user identities and hashed opaque bearer sessions.

SQLite is the development implementation. Use an external persistent database
before scaling across workers or hosts. Session tokens are never stored raw.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
import re
import sqlite3
import threading
import time
from pathlib import Path
from uuid import uuid4


def password_hash(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"scrypt$16384${salt.hex()}${digest.hex()}"


def check_password(password: str, stored: str) -> bool:
    try:
        algorithm, n, salt, expected = stored.split('$')
        if algorithm != 'scrypt' or int(n) != 16384:
            return False
        actual = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=2**14, r=8, p=1)
        return hmac.compare_digest(actual, bytes.fromhex(expected))
    except (TypeError, ValueError):
        return False


class Accounts:
    def __init__(self, path: str | Path):
        self.lock = threading.RLock()
        self.db = sqlite3.connect(str(path), check_same_thread=False, timeout=15)
        self.db.execute('PRAGMA foreign_keys=ON')
        with self.db:
            self.db.execute('CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, created REAL NOT NULL)')
            self.db.execute('CREATE TABLE IF NOT EXISTS sessions (token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), expires REAL NOT NULL)')

    def register(self, email: str, password: str) -> dict:
        email = email.strip().lower()
        if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email) or len(password) < 12:
            raise ValueError('A valid email and password of at least 12 characters are required')
        user_id = uuid4().hex
        with self.lock, self.db:
            try:
                self.db.execute('INSERT INTO users VALUES (?, ?, ?, ?)',
                                (user_id, email, password_hash(password), time.time()))
            except sqlite3.IntegrityError as exc:
                raise ValueError('Account already exists') from exc
        return {'id': user_id, 'email': email}

    def login(self, email: str, password: str, lifetime_s: int = 86400) -> dict | None:
        with self.lock:
            row = self.db.execute('SELECT id, email, password_hash FROM users WHERE email=?',
                                  (email.strip().lower(),)).fetchone()
            if not row or not check_password(password, row[2]):
                return None
            token = secrets.token_urlsafe(32)
            expires = time.time() + lifetime_s
            with self.db:
                self.db.execute('INSERT INTO sessions VALUES (?, ?, ?)',
                                (hashlib.sha256(token.encode()).hexdigest(), row[0], expires))
            return {'access_token': token, 'token_type': 'bearer', 'expires_at': expires,
                    'user': {'id': row[0], 'email': row[1]}}

    def identity(self, token: str) -> dict | None:
        if not token:
            return None
        digest = hashlib.sha256(token.encode()).hexdigest()
        with self.lock:
            row = self.db.execute('SELECT u.id, u.email FROM users u JOIN sessions s ON u.id=s.user_id WHERE s.token_hash=? AND s.expires>?',
                                  (digest, time.time())).fetchone()
        return {'id': row[0], 'email': row[1]} if row else None

    def logout(self, token: str) -> None:
        with self.lock, self.db:
            self.db.execute('DELETE FROM sessions WHERE token_hash=?',
                            (hashlib.sha256(token.encode()).hexdigest(),))
