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
from PySide6.QtMultimedia import QMediaDevices


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

        # Audio output device
        self.audio_group = QGroupBox()
        audio_layout = QFormLayout(self.audio_group)

        self.audio_device_combo = QComboBox()
        self._populate_audio_devices()
        self.audio_device_label = QLabel()
        audio_layout.addRow(self.audio_device_label, self.audio_device_combo)

        self.refresh_devices_btn = QPushButton()
        self.refresh_devices_btn.setObjectName("secondaryBtn")
        self.refresh_devices_btn.setFixedWidth(160)
        self.refresh_devices_btn.clicked.connect(self._populate_audio_devices)
        audio_layout.addRow("", self.refresh_devices_btn)

        layout.addWidget(self.audio_group)

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

        self.desktop_shortcut_check = QCheckBox()
        startup_layout.addWidget(self.desktop_shortcut_check)

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

    def _populate_audio_devices(self):
        self.audio_device_combo.clear()
        saved_device = self.db.get_setting('audio_device', '')

        self.audio_device_combo.addItem(self.loc.tr('default_device'), '')

        devices = QMediaDevices.audioOutputs()
        selected_idx = 0
        for i, device in enumerate(devices):
            desc = device.description()
            device_id = device.id().data().decode('utf-8', errors='replace')
            self.audio_device_combo.addItem(desc, device_id)
            if device_id == saved_device:
                selected_idx = i + 1

        self.audio_device_combo.setCurrentIndex(selected_idx)

    def apply_translations(self):
        self.title_label.setText(self.loc.tr('settings_title'))
        self.lang_group.setTitle(self.loc.tr('language_settings'))
        self.lang_label.setText(self.loc.tr('language'))
        self.audio_group.setTitle(self.loc.tr('audio_settings'))
        self.audio_device_label.setText(self.loc.tr('audio_device'))
        self.refresh_devices_btn.setText(self.loc.tr('refresh_devices'))
        self.volume_group.setTitle(self.loc.tr('volume_settings'))
        self.volume_label.setText(self.loc.tr('volume'))
        self.startup_group.setTitle(self.loc.tr('startup_settings'))
        self.autostart_check.setText(self.loc.tr('autostart'))
        self.start_minimized_check.setText(self.loc.tr('start_minimized'))
        self.desktop_shortcut_check.setText(self.loc.tr('create_desktop_shortcut'))
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

        desktop_shortcut = self.db.get_setting('desktop_shortcut', 'false') == 'true'
        self.desktop_shortcut_check.setChecked(desktop_shortcut)

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

        # Audio device
        device_id = self.audio_device_combo.currentData()
        self.db.set_setting('audio_device', device_id or '')
        self.sound_engine.set_output_device(device_id)

        volume = self.volume_slider.value()
        self.db.set_setting('volume', str(volume))
        self.sound_engine.set_volume(volume)

        autostart = self.autostart_check.isChecked()
        self.db.set_setting('autostart', 'true' if autostart else 'false')
        self._configure_autostart(autostart)

        start_min = self.start_minimized_check.isChecked()
        self.db.set_setting('start_minimized', 'true' if start_min else 'false')

        # Desktop shortcut
        create_shortcut = self.desktop_shortcut_check.isChecked()
        self.db.set_setting('desktop_shortcut', 'true' if create_shortcut else 'false')
        if create_shortcut:
            self._create_desktop_shortcut()

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

    def _create_desktop_shortcut(self):
        if sys.platform != 'win32':
            return

        try:
            import subprocess
            if getattr(sys, 'frozen', False):
                exe_path = sys.executable
            else:
                exe_path = os.path.abspath(sys.argv[0])

            desktop = os.path.join(os.environ.get('USERPROFILE', ''), 'Desktop')
            shortcut_path = os.path.join(desktop, 'School Bell Scheduler.lnk')

            # Use PowerShell to create the shortcut
            ps_script = f'''
$ws = New-Object -ComObject WScript.Shell
$shortcut = $ws.CreateShortcut("{shortcut_path}")
$shortcut.TargetPath = "{exe_path}"
$shortcut.WorkingDirectory = "{os.path.dirname(exe_path)}"
$shortcut.Description = "School Bell Scheduler"
$shortcut.Save()
'''
            subprocess.run(
                ['powershell', '-NoProfile', '-Command', ps_script],
                capture_output=True, timeout=10
            )
        except Exception:
            pass
