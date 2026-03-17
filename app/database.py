"""
Database module - SQLite database management for School Bell Scheduler.
"""
import sqlite3
import json
import os
from datetime import datetime


class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        self._insert_defaults()

    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bells (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                time TEXT NOT NULL,
                enabled INTEGER DEFAULT 1,
                days TEXT DEFAULT '["mon","tue","wed","thu","fri"]',
                sound_sequence TEXT DEFAULT '[]',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sounds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                filename TEXT NOT NULL UNIQUE,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')
        self.conn.commit()

    def _insert_defaults(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM settings")
        if cursor.fetchone()['cnt'] == 0:
            defaults = {
                'language': 'en',
                'autostart': 'false',
                'start_minimized': 'false',
                'volume': '100',
                'theme': 'light',
            }
            for key, value in defaults.items():
                cursor.execute(
                    "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                    (key, value)
                )
            self.conn.commit()

    # --- Bells ---

    def get_all_bells(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM bells ORDER BY time ASC")
        rows = cursor.fetchall()
        result = []
        for row in rows:
            bell = dict(row)
            bell['days'] = json.loads(bell['days'])
            bell['sound_sequence'] = json.loads(bell['sound_sequence'])
            result.append(bell)
        return result

    def get_enabled_bells(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM bells WHERE enabled = 1 ORDER BY time ASC")
        rows = cursor.fetchall()
        result = []
        for row in rows:
            bell = dict(row)
            bell['days'] = json.loads(bell['days'])
            bell['sound_sequence'] = json.loads(bell['sound_sequence'])
            result.append(bell)
        return result

    def add_bell(self, name, time_str, days=None, sound_sequence=None):
        if days is None:
            days = ["mon", "tue", "wed", "thu", "fri"]
        if sound_sequence is None:
            sound_sequence = []
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO bells (name, time, days, sound_sequence) VALUES (?, ?, ?, ?)",
            (name, time_str, json.dumps(days), json.dumps(sound_sequence))
        )
        self.conn.commit()
        return cursor.lastrowid

    def update_bell(self, bell_id, name, time_str, enabled, days, sound_sequence):
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE bells SET name=?, time=?, enabled=?, days=?, sound_sequence=? WHERE id=?",
            (name, time_str, int(enabled), json.dumps(days), json.dumps(sound_sequence), bell_id)
        )
        self.conn.commit()

    def delete_bell(self, bell_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM bells WHERE id=?", (bell_id,))
        self.conn.commit()

    def toggle_bell(self, bell_id, enabled):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE bells SET enabled=? WHERE id=?", (int(enabled), bell_id))
        self.conn.commit()

    # --- Sounds ---

    def get_all_sounds(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM sounds ORDER BY name ASC")
        return [dict(row) for row in cursor.fetchall()]

    def add_sound(self, name, filename):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO sounds (name, filename) VALUES (?, ?)",
            (name, filename)
        )
        self.conn.commit()
        return cursor.lastrowid

    def delete_sound(self, sound_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT filename FROM sounds WHERE id=?", (sound_id,))
        row = cursor.fetchone()
        filename = dict(row)['filename'] if row else None
        cursor.execute("DELETE FROM sounds WHERE id=?", (sound_id,))
        self.conn.commit()
        return filename

    def get_sound_by_filename(self, filename):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM sounds WHERE filename=?", (filename,))
        row = cursor.fetchone()
        return dict(row) if row else None

    # --- Settings ---

    def get_setting(self, key, default=None):
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
        row = cursor.fetchone()
        if row:
            return row['value']
        return default

    def set_setting(self, key, value):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, str(value))
        )
        self.conn.commit()

    def close(self):
        if self.conn:
            self.conn.close()
