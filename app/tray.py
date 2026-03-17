"""
System Tray module - Manages the system tray icon and menu.
"""
import os
import sys

from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QAction
from PySide6.QtCore import Qt


def create_default_icon():
    """Create a simple bell icon programmatically."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    painter.setBrush(QColor(52, 152, 219))
    painter.setPen(QColor(41, 128, 185))
    painter.drawEllipse(12, 8, 40, 36)

    painter.setBrush(QColor(41, 128, 185))
    painter.drawRect(8, 30, 48, 8)

    painter.setBrush(QColor(44, 62, 80))
    painter.drawEllipse(26, 42, 12, 12)

    painter.setPen(QColor(255, 255, 255))
    font = QFont("Arial", 16, QFont.Weight.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect().adjusted(0, -6, 0, -6), Qt.AlignmentFlag.AlignCenter, "B")

    painter.end()
    return QIcon(pixmap)


class SystemTray(QSystemTrayIcon):
    def __init__(self, app, main_window, scheduler, localization):
        super().__init__(app)
        self.app = app
        self.main_window = main_window
        self.scheduler = scheduler
        self.loc = localization

        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        icon_path = os.path.join(base_path, 'assets', 'icon.png')

        if os.path.exists(icon_path):
            self.setIcon(QIcon(icon_path))
        else:
            self.setIcon(create_default_icon())

        self.setToolTip(self.loc.tr('app_name'))
        self._build_menu()

        self.activated.connect(self._on_activated)
        self.loc.language_changed.connect(self._rebuild_menu)
        self.scheduler.status_changed.connect(self._on_status_changed)

        self.show()

    def _build_menu(self):
        menu = QMenu()

        self.action_open = QAction(self.loc.tr('tray_open'), menu)
        self.action_open.triggered.connect(self._show_window)
        menu.addAction(self.action_open)

        menu.addSeparator()

        self.action_pause = QAction(self.loc.tr('tray_pause'), menu)
        self.action_pause.triggered.connect(self.scheduler.pause)
        menu.addAction(self.action_pause)

        self.action_resume = QAction(self.loc.tr('tray_resume'), menu)
        self.action_resume.triggered.connect(self.scheduler.resume)
        menu.addAction(self.action_resume)

        if self.scheduler.is_paused():
            self.action_pause.setVisible(False)
            self.action_resume.setVisible(True)
        else:
            self.action_pause.setVisible(True)
            self.action_resume.setVisible(False)

        menu.addSeparator()

        self.action_exit = QAction(self.loc.tr('tray_exit'), menu)
        self.action_exit.triggered.connect(self._quit_app)
        menu.addAction(self.action_exit)

        self.setContextMenu(menu)

    def _rebuild_menu(self):
        self.setToolTip(self.loc.tr('app_name'))
        self._build_menu()

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_window()

    def _show_window(self):
        self.main_window.showNormal()
        self.main_window.activateWindow()
        self.main_window.raise_()

    def _on_status_changed(self, running):
        if running:
            self.action_pause.setVisible(True)
            self.action_resume.setVisible(False)
        else:
            self.action_pause.setVisible(False)
            self.action_resume.setVisible(True)

    def _quit_app(self):
        self.hide()
        self.app.quit()
