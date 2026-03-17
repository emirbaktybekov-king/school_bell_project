"""
Sounds Manager Tab - Add, preview, and delete sound files.
"""
import os
import shutil

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QMessageBox, QAbstractItemView
)
from PySide6.QtCore import Qt


class SoundsManagerTab(QWidget):
    def __init__(self, db, localization, sound_engine):
        super().__init__()
        self.db = db
        self.loc = localization
        self.sound_engine = sound_engine
        self._setup_ui()
        self._load_sounds()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-size: 18px; font-weight: 700; color: #2c3e50;")
        header.addWidget(self.title_label)
        header.addStretch()

        self.add_btn = QPushButton()
        self.add_btn.clicked.connect(self._add_sound)
        header.addWidget(self.add_btn)

        layout.addLayout(header)

        # Info label
        self.info_label = QLabel()
        self.info_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        # Bottom buttons
        btn_layout = QHBoxLayout()

        self.preview_btn = QPushButton()
        self.preview_btn.clicked.connect(self._preview_sound)
        btn_layout.addWidget(self.preview_btn)

        self.stop_btn = QPushButton()
        self.stop_btn.setObjectName("secondaryBtn")
        self.stop_btn.clicked.connect(self._stop_preview)
        btn_layout.addWidget(self.stop_btn)

        self.delete_btn = QPushButton()
        self.delete_btn.setObjectName("dangerBtn")
        self.delete_btn.clicked.connect(self._delete_sound)
        btn_layout.addWidget(self.delete_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def apply_translations(self):
        self.title_label.setText(self.loc.tr('sounds_title'))
        self.add_btn.setText(self.loc.tr('add_sound'))
        self.preview_btn.setText(self.loc.tr('preview'))
        self.stop_btn.setText(self.loc.tr('stop'))
        self.delete_btn.setText(self.loc.tr('delete_sound'))
        self.info_label.setText(self.loc.tr('sounds_info'))
        self.table.setHorizontalHeaderLabels([
            self.loc.tr('col_name'),
            self.loc.tr('col_filename'),
            'ID'
        ])
        self.table.setColumnHidden(2, True)
        self._load_sounds()

    def _load_sounds(self):
        self.table.setRowCount(0)
        sounds = self.db.get_all_sounds()

        available_files = self.sound_engine.get_available_sounds()
        for f in available_files:
            existing = self.db.get_sound_by_filename(f)
            if not existing:
                name = os.path.splitext(f)[0].replace('_', ' ').replace('-', ' ').title()
                self.db.add_sound(name, f)

        sounds = self.db.get_all_sounds()
        for sound in sounds:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(sound['name']))
            self.table.setItem(row, 1, QTableWidgetItem(sound['filename']))
            self.table.setItem(row, 2, QTableWidgetItem(str(sound['id'])))

        self.table.resizeColumnsToContents()

    def _get_selected_sound(self):
        row = self.table.currentRow()
        if row < 0:
            return None, None
        id_item = self.table.item(row, 2)
        filename_item = self.table.item(row, 1)
        if id_item and filename_item:
            return int(id_item.text()), filename_item.text()
        return None, None

    def _add_sound(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            self.loc.tr('select_sound_files'),
            "",
            "Sound Files (*.wav *.mp3 *.ogg *.flac);;All Files (*)"
        )
        if not files:
            return

        for filepath in files:
            filename = os.path.basename(filepath)
            dest = self.sound_engine.get_sound_path(filename)

            counter = 1
            base, ext = os.path.splitext(filename)
            while os.path.exists(dest):
                filename = f"{base}_{counter}{ext}"
                dest = self.sound_engine.get_sound_path(filename)
                counter += 1

            shutil.copy2(filepath, dest)
            name = os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ').title()
            self.db.add_sound(name, filename)

        self._load_sounds()

    def _preview_sound(self):
        _, filename = self._get_selected_sound()
        if filename:
            self.sound_engine.preview_sound(filename)

    def _stop_preview(self):
        self.sound_engine.stop()

    def _delete_sound(self):
        sound_id, filename = self._get_selected_sound()
        if sound_id is None:
            return

        reply = QMessageBox.question(
            self, self.loc.tr('confirm'),
            self.loc.tr('confirm_delete_sound'),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_sound(sound_id)
            if filename:
                filepath = self.sound_engine.get_sound_path(filename)
                if os.path.exists(filepath):
                    os.remove(filepath)
            self._load_sounds()
