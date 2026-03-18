"""
Scheduler module - Manages bell timing and triggers sound playback.
Uses local system time only. Runs 24/7.
"""
import json
import logging
from datetime import datetime, timedelta

from PySide6.QtCore import QObject, QTimer, Signal


DAY_MAP = {
    0: 'mon', 1: 'tue', 2: 'wed', 3: 'thu', 4: 'fri', 5: 'sat', 6: 'sun'
}


class BellScheduler(QObject):
    bell_triggered = Signal(dict)
    schedule_updated = Signal()
    status_changed = Signal(bool)

    def __init__(self, db, sound_engine):
        super().__init__()
        self.db = db
        self.sound_engine = sound_engine
        self._paused = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._check_bells)
        self._last_triggered = {}
        self._last_checked_minute = None

    def start(self):
        self._timer.start(1000)

    def stop(self):
        self._timer.stop()

    def is_paused(self):
        return self._paused

    def pause(self):
        self._paused = True
        self.status_changed.emit(False)

    def resume(self):
        self._paused = False
        self.status_changed.emit(True)

    def toggle_pause(self):
        if self._paused:
            self.resume()
        else:
            self.pause()

    def _check_bells(self):
        try:
            self._check_bells_inner()
        except Exception:
            logging.error("Scheduler error (recovered):\n%s",
                          __import__('traceback').format_exc())

    def _check_bells_inner(self):
        if self._paused:
            return

        now = datetime.now()
        current_time = now.strftime('%H:%M')
        current_day = DAY_MAP.get(now.weekday(), '')

        # Only check once per minute (avoids duplicate triggers and
        # fixes the bug where second==0 could be skipped by the timer)
        current_minute_key = now.strftime('%Y-%m-%d_%H:%M')
        if current_minute_key == self._last_checked_minute:
            return
        self._last_checked_minute = current_minute_key

        bells = self.db.get_enabled_bells()
        for bell in bells:
            if bell['time'] == current_time and current_day in bell['days']:
                bell_key = f"{bell['id']}_{current_time}_{now.strftime('%Y-%m-%d')}"
                if bell_key not in self._last_triggered:
                    self._last_triggered[bell_key] = now
                    self._trigger_bell(bell)
                    self._cleanup_old_triggers(now)

    def _trigger_bell(self, bell):
        try:
            self.bell_triggered.emit(bell)
            sequence = bell.get('sound_sequence', [])
            if sequence:
                self.sound_engine.play_sequence(sequence)
        except Exception:
            logging.error("Bell trigger error:\n%s",
                          __import__('traceback').format_exc())

    def _cleanup_old_triggers(self, now):
        cutoff = now - timedelta(minutes=2)
        keys_to_remove = [
            k for k, v in self._last_triggered.items() if v < cutoff
        ]
        for k in keys_to_remove:
            del self._last_triggered[k]

    def get_next_bell(self):
        now = datetime.now()
        current_time_str = now.strftime('%H:%M')
        current_day = DAY_MAP.get(now.weekday(), '')

        bells = self.db.get_enabled_bells()
        today_bells = []
        for bell in bells:
            if current_day in bell['days'] and bell['time'] > current_time_str:
                today_bells.append(bell)

        if today_bells:
            today_bells.sort(key=lambda b: b['time'])
            return today_bells[0]

        for day_offset in range(1, 8):
            future = now + timedelta(days=day_offset)
            future_day = DAY_MAP.get(future.weekday(), '')
            for bell in bells:
                if future_day in bell['days']:
                    return bell

        return None

    def get_countdown_to_next(self):
        next_bell = self.get_next_bell()
        if not next_bell:
            return None, None

        now = datetime.now()
        current_day = DAY_MAP.get(now.weekday(), '')
        bell_time_parts = next_bell['time'].split(':')
        bell_hour = int(bell_time_parts[0])
        bell_minute = int(bell_time_parts[1])

        bell_datetime = now.replace(hour=bell_hour, minute=bell_minute, second=0, microsecond=0)

        if current_day in next_bell['days'] and bell_datetime > now:
            pass
        else:
            for day_offset in range(1, 8):
                future = now + timedelta(days=day_offset)
                future_day = DAY_MAP.get(future.weekday(), '')
                if future_day in next_bell['days']:
                    bell_datetime = future.replace(
                        hour=bell_hour, minute=bell_minute, second=0, microsecond=0
                    )
                    break

        remaining = bell_datetime - now
        if remaining.total_seconds() < 0:
            return next_bell, timedelta(0)

        return next_bell, remaining

    def reload_schedule(self):
        self.schedule_updated.emit()
