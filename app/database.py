"""
Database module - SQLite database management for School Bell Scheduler.
Auto-recovers from corruption by recreating the database.
"""
import sqlite3
import json
import os
import logging
from datetime import datetime


class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        try:
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            # Quick integrity check
            self.conn.execute("PRAGMA integrity_check")
            self._create_tables()
            self._insert_defaults()
        except sqlite3.DatabaseError:
            logging.warning("Database corrupted — recreating: %s", db_path)
            self.conn = None
            try:
                os.remove(db_path)
            except OSError:
                pass
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
                'language': 'ru',
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

        # Insert default bell schedule if no bells exist
        cursor.execute("SELECT COUNT(*) as cnt FROM bells")
        if cursor.fetchone()['cnt'] == 0:
            self._insert_default_schedule()

    def _insert_default_schedule(self):
        sound_seq = json.dumps([
            {"type": "sound", "filename": "bell-sound.mp3"},
            {"type": "pause", "duration": 3},
            {"type": "sound", "filename": "bell-sound.mp3"}
        ])
        weekdays = json.dumps(["mon", "tue", "wed", "thu", "fri", "sat"])
        cursor = self.conn.cursor()

        # ===== 1 смена (Shift 1) =====
        shift1 = [
            ("1 смена - 1 урок (начало)", "07:30"),
            ("1 смена - 1 урок (конец)",  "08:15"),
            ("1 смена - 2 урок (начало)", "08:20"),
            ("1 смена - 2 урок (конец)",  "09:05"),
            ("1 смена - 3 урок (начало)", "09:10"),
            ("1 смена - 3 урок (конец)",  "09:55"),
            ("1 смена - 4 урок (начало)", "10:05"),
            ("1 смена - 4 урок (конец)",  "10:50"),
            ("1 смена - 5 урок (начало)", "10:55"),
            ("1 смена - 5 урок (конец)",  "11:40"),
            ("1 смена - 6 урок (начало)", "11:45"),
            ("1 смена - 6 урок (конец)",  "12:30"),
            ("1 смена - 7 урок (начало)", "12:35"),
            ("1 смена - 7 урок (конец)",  "13:20"),
        ]

        # ===== 2 смена (Shift 2) =====
        shift2 = [
            ("2 смена - 0 урок (начало)", "12:35"),
            ("2 смена - 0 урок (конец)",  "13:20"),
            ("2 смена - 1 урок (начало)", "13:30"),
            ("2 смена - 1 урок (конец)",  "14:15"),
            ("2 смена - 2 урок (начало)", "14:20"),
            ("2 смена - 2 урок (конец)",  "15:05"),
            ("2 смена - 3 урок (начало)", "15:10"),
            ("2 смена - 3 урок (конец)",  "15:55"),
            ("2 смена - 4 урок (начало)", "16:05"),
            ("2 смена - 4 урок (конец)",  "16:50"),
            ("2 смена - 5 урок (начало)", "16:55"),
            ("2 смена - 5 урок (конец)",  "17:40"),
            ("2 смена - 6 урок (начало)", "17:45"),
            ("2 смена - 6 урок (конец)",  "18:30"),
        ]

        # Combine, but skip duplicate times (12:35 and 13:20 overlap between shifts)
        seen_times = set()
        all_bells = []
        for name, t in shift1 + shift2:
            if t not in seen_times:
                seen_times.add(t)
                all_bells.append((name, t))
            # If duplicate time, keep shift 1 name (it rings once for both)

        for name, t in all_bells:
            cursor.execute(
                "INSERT INTO bells (name, time, enabled, days, sound_sequence) VALUES (?, ?, 1, ?, ?)",
                (name, t, weekdays, sound_seq)
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
