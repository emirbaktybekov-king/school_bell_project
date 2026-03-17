"""
Main Window - Central application window with tab navigation.
"""
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QStatusBar
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QCloseEvent

from ui.dashboard import DashboardTab
from ui.schedule_editor import ScheduleEditorTab
from ui.sounds_manager import SoundsManagerTab
from ui.settings import SettingsTab


class MainWindow(QMainWindow):
    def __init__(self, db, localization, scheduler, sound_engine):
        super().__init__()
        self.db = db
        self.loc = localization
        self.scheduler = scheduler
        self.sound_engine = sound_engine

        self.setMinimumSize(QSize(800, 600))
        self._setup_ui()
        self._apply_translations()

        self.loc.language_changed.connect(self._apply_translations)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        self.dashboard_tab = DashboardTab(self.db, self.loc, self.scheduler)
        self.schedule_tab = ScheduleEditorTab(self.db, self.loc, self.scheduler, self.sound_engine)
        self.sounds_tab = SoundsManagerTab(self.db, self.loc, self.sound_engine)
        self.settings_tab = SettingsTab(self.db, self.loc, self.scheduler, self.sound_engine)

        self.tab_widget.addTab(self.dashboard_tab, "")
        self.tab_widget.addTab(self.schedule_tab, "")
        self.tab_widget.addTab(self.sounds_tab, "")
        self.tab_widget.addTab(self.settings_tab, "")

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.setStyleSheet(self._get_stylesheet())

    def _apply_translations(self):
        self.setWindowTitle(self.loc.tr('app_name'))
        self.tab_widget.setTabText(0, self.loc.tr('tab_dashboard'))
        self.tab_widget.setTabText(1, self.loc.tr('tab_schedule'))
        self.tab_widget.setTabText(2, self.loc.tr('tab_sounds'))
        self.tab_widget.setTabText(3, self.loc.tr('tab_settings'))
        self.status_bar.showMessage(self.loc.tr('status_ready'))

        self.dashboard_tab.apply_translations()
        self.schedule_tab.apply_translations()
        self.sounds_tab.apply_translations()
        self.settings_tab.apply_translations()

    def closeEvent(self, event: QCloseEvent):
        event.ignore()
        self.hide()

    def _get_stylesheet(self):
        return """
            QMainWindow {
                background-color: #f5f6fa;
            }
            QTabWidget::pane {
                border: 1px solid #dcdde1;
                background-color: #ffffff;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #dcdde1;
                color: #2f3640;
                padding: 10px 24px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-size: 13px;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                color: #2980b9;
                font-weight: 600;
            }
            QTabBar::tab:hover {
                background-color: #ecf0f1;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 18px;
                border-radius: 4px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #2472a4;
            }
            QPushButton#dangerBtn {
                background-color: #e74c3c;
            }
            QPushButton#dangerBtn:hover {
                background-color: #c0392b;
            }
            QPushButton#secondaryBtn {
                background-color: #95a5a6;
            }
            QPushButton#secondaryBtn:hover {
                background-color: #7f8c8d;
            }
            QTableWidget {
                border: 1px solid #dcdde1;
                gridline-color: #ecf0f1;
                background-color: #ffffff;
                alternate-background-color: #f8f9fa;
                selection-background-color: #3498db;
                selection-color: white;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 6px;
            }
            QHeaderView::section {
                background-color: #ecf0f1;
                color: #2f3640;
                padding: 8px;
                border: none;
                border-right: 1px solid #dcdde1;
                border-bottom: 1px solid #dcdde1;
                font-weight: 600;
                font-size: 13px;
            }
            QLineEdit, QTimeEdit, QComboBox, QSpinBox {
                border: 1px solid #dcdde1;
                border-radius: 4px;
                padding: 6px 10px;
                background-color: #ffffff;
                font-size: 13px;
            }
            QLineEdit:focus, QTimeEdit:focus, QComboBox:focus, QSpinBox:focus {
                border-color: #3498db;
            }
            QGroupBox {
                font-weight: 600;
                font-size: 14px;
                border: 1px solid #dcdde1;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }
            QLabel {
                font-size: 13px;
                color: #2f3640;
            }
            QCheckBox {
                font-size: 13px;
                spacing: 6px;
            }
            QSlider::groove:horizontal {
                border: 1px solid #dcdde1;
                height: 6px;
                background: #ecf0f1;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #3498db;
                border: none;
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QStatusBar {
                background-color: #ecf0f1;
                color: #7f8c8d;
                font-size: 12px;
            }
        """
