"""
Dashboard Tab - Shows current time, next bell, and countdown.
"""
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont


class InfoCard(QFrame):
    def __init__(self, title="", value="", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            InfoCard {
                background-color: #ffffff;
                border: 1px solid #dcdde1;
                border-radius: 8px;
                padding: 16px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)

        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("color: #7f8c8d; font-size: 14px; font-weight: 500;")
        layout.addWidget(self.title_label)

        self.value_label = QLabel(value)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(32)
        font.setBold(True)
        self.value_label.setFont(font)
        self.value_label.setStyleSheet("color: #2c3e50; font-size: 36px;")
        layout.addWidget(self.value_label)

    def set_title(self, text):
        self.title_label.setText(text)

    def set_value(self, text):
        self.value_label.setText(text)


class DashboardTab(QWidget):
    def __init__(self, db, localization, scheduler):
        super().__init__()
        self.db = db
        self.loc = localization
        self.scheduler = scheduler
        self._setup_ui()

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start(500)

        self.scheduler.bell_triggered.connect(self._on_bell_triggered)
        self._update_display()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Title
        self.title_label = QLabel()
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 22px; font-weight: 700; color: #2c3e50; margin-bottom: 8px;")
        layout.addWidget(self.title_label)

        # Status indicator
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 14px; font-weight: 500;")
        layout.addWidget(self.status_label)

        # Cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)

        self.time_card = InfoCard()
        self.next_bell_card = InfoCard()
        self.countdown_card = InfoCard()

        cards_layout.addWidget(self.time_card)
        cards_layout.addWidget(self.next_bell_card)
        cards_layout.addWidget(self.countdown_card)
        layout.addLayout(cards_layout)

        # Today schedule
        self.today_label = QLabel()
        self.today_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #2c3e50; margin-top: 12px;")
        layout.addWidget(self.today_label)

        self.schedule_list = QLabel()
        self.schedule_list.setWordWrap(True)
        self.schedule_list.setStyleSheet("""
            background-color: #ffffff;
            border: 1px solid #dcdde1;
            border-radius: 8px;
            padding: 16px;
            font-size: 14px;
            color: #2c3e50;
            line-height: 1.6;
        """)
        layout.addWidget(self.schedule_list)

        # Last bell notification
        self.last_bell_label = QLabel()
        self.last_bell_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.last_bell_label.setStyleSheet("font-size: 13px; color: #7f8c8d; margin-top: 4px;")
        layout.addWidget(self.last_bell_label)

        layout.addStretch()

    def apply_translations(self):
        self.title_label.setText(self.loc.tr('dashboard_title'))
        self.time_card.set_title(self.loc.tr('current_time'))
        self.next_bell_card.set_title(self.loc.tr('next_bell'))
        self.countdown_card.set_title(self.loc.tr('countdown'))
        self.today_label.setText(self.loc.tr('today_schedule'))
        self._update_display()

    def _update_display(self):
        now = datetime.now()
        self.time_card.set_value(now.strftime('%H:%M:%S'))

        if self.scheduler.is_paused():
            self.status_label.setText(f"⏸  {self.loc.tr('status_paused')}")
            self.status_label.setStyleSheet("font-size: 14px; font-weight: 500; color: #e74c3c;")
        else:
            self.status_label.setText(f"●  {self.loc.tr('status_running')}")
            self.status_label.setStyleSheet("font-size: 14px; font-weight: 500; color: #27ae60;")

        next_bell, remaining = self.scheduler.get_countdown_to_next()
        if next_bell:
            self.next_bell_card.set_value(next_bell['time'])
            if remaining:
                total_seconds = int(remaining.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                if hours > 0:
                    countdown_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                else:
                    countdown_str = f"{minutes:02d}:{seconds:02d}"
                self.countdown_card.set_value(countdown_str)
            else:
                self.countdown_card.set_value("--:--")
        else:
            self.next_bell_card.set_value("--:--")
            self.countdown_card.set_value("--:--")

        self._update_today_schedule()

    def _update_today_schedule(self):
        from app.scheduler import DAY_MAP
        now = datetime.now()
        current_day = DAY_MAP.get(now.weekday(), '')

        bells = self.db.get_enabled_bells()
        today_bells = [b for b in bells if current_day in b['days']]
        today_bells.sort(key=lambda b: b['time'])

        if today_bells:
            current_time = now.strftime('%H:%M')
            lines = []
            for b in today_bells:
                marker = "  ✓  " if b['time'] < current_time else "  ○  "
                lines.append(f"{marker}{b['time']}  —  {b['name']}")
            self.schedule_list.setText("\n".join(lines))
        else:
            self.schedule_list.setText(self.loc.tr('no_bells_today'))

    def _on_bell_triggered(self, bell):
        self.last_bell_label.setText(
            f"{self.loc.tr('last_bell_rang')}: {bell['name']} ({bell['time']})"
        )
