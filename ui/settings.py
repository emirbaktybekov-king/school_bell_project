"""
Settings Tab - Application configuration.
"""
import os
import sys

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QCheckBox, QSlider, QGroupBox, QFormLayout,
    QMessageBox
)
from PySide6.QtCore import Qt


class SettingsTab(QWidget):
    def __init__(self, db, localization, scheduler, sound_engine):
        super().__init__()
        self.db = db
        self.loc = localization
        self.scheduler = scheduler
        self.sound_engine = sound_engine
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Title
        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-size: 18px; font-weight: 700; color: #2c3e50;")
        layout.addWidget(self.title_label)

        # Language
        self.lang_group = QGroupBox()
        lang_layout = QFormLayout(self.lang_group)

        self.lang_combo = QComboBox()
        for code, name in self.loc.get_available_languages():
            self.lang_combo.addItem(name, code)
        self.lang_label = QLabel()
        lang_layout.addRow(self.lang_label, self.lang_combo)
        layout.addWidget(self.lang_group)

        # Volume
        self.volume_group = QGroupBox()
        vol_layout = QFormLayout(self.volume_group)

        vol_slider_layout = QHBoxLayout()
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(100)
        self.volume_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.volume_slider.setTickInterval(10)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        vol_slider_layout.addWidget(self.volume_slider)

        self.volume_value_label = QLabel("100%")
        self.volume_value_label.setMinimumWidth(45)
        vol_slider_layout.addWidget(self.volume_value_label)

        self.volume_label = QLabel()
        vol_layout.addRow(self.volume_label, vol_slider_layout)
        layout.addWidget(self.volume_group)

        # Startup
        self.startup_group = QGroupBox()
        startup_layout = QVBoxLayout(self.startup_group)

        self.autostart_check = QCheckBox()
        self.autostart_check.stateChanged.connect(self._on_autostart_changed)
        startup_layout.addWidget(self.autostart_check)

        self.start_minimized_check = QCheckBox()
        self.start_minimized_check.stateChanged.connect(self._on_start_minimized_changed)
        startup_layout.addWidget(self.start_minimized_check)

        layout.addWidget(self.startup_group)

        # Save button
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton()
        self.save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Info
        self.info_label = QLabel()
        self.info_label.setStyleSheet("color: #7f8c8d; font-size: 12px; margin-top: 8px;")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        layout.addStretch()

    def apply_translations(self):
        self.title_label.setText(self.loc.tr('settings_title'))
        self.lang_group.setTitle(self.loc.tr('language_settings'))
        self.lang_label.setText(self.loc.tr('language'))
        self.volume_group.setTitle(self.loc.tr('volume_settings'))
        self.volume_label.setText(self.loc.tr('volume'))
        self.startup_group.setTitle(self.loc.tr('startup_settings'))
        self.autostart_check.setText(self.loc.tr('autostart'))
        self.start_minimized_check.setText(self.loc.tr('start_minimized'))
        self.save_btn.setText(self.loc.tr('save_settings'))
        self.info_label.setText(self.loc.tr('settings_info'))

    def _load_settings(self):
        lang = self.db.get_setting('language', 'en')
        idx = self.lang_combo.findData(lang)
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)

        volume = int(self.db.get_setting('volume', '100'))
        self.volume_slider.setValue(volume)

        autostart = self.db.get_setting('autostart', 'false') == 'true'
        self.autostart_check.setChecked(autostart)

        start_min = self.db.get_setting('start_minimized', 'false') == 'true'
        self.start_minimized_check.setChecked(start_min)

    def _on_volume_changed(self, value):
        self.volume_value_label.setText(f"{value}%")

    def _on_autostart_changed(self, state):
        pass

    def _on_start_minimized_changed(self, state):
        pass

    def _save_settings(self):
        lang = self.lang_combo.currentData()
        self.db.set_setting('language', lang)
        self.loc.set_language(lang)

        volume = self.volume_slider.value()
        self.db.set_setting('volume', str(volume))
        self.sound_engine.set_volume(volume)

        autostart = self.autostart_check.isChecked()
        self.db.set_setting('autostart', 'true' if autostart else 'false')
        self._configure_autostart(autostart)

        start_min = self.start_minimized_check.isChecked()
        self.db.set_setting('start_minimized', 'true' if start_min else 'false')

        QMessageBox.information(
            self, self.loc.tr('success'), self.loc.tr('settings_saved')
        )

    def _configure_autostart(self, enabled):
        if sys.platform != 'win32':
            return

        try:
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            app_name = "SchoolBellScheduler"

            if enabled:
                if getattr(sys, 'frozen', False):
                    exe_path = sys.executable
                else:
                    exe_path = os.path.abspath(sys.argv[0])

                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE
                )
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{exe_path}"')
                winreg.CloseKey(key)
            else:
                try:
                    key = winreg.OpenKey(
                        winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE
                    )
                    winreg.DeleteValue(key, app_name)
                    winreg.CloseKey(key)
                except FileNotFoundError:
                    pass
        except Exception:
            pass
