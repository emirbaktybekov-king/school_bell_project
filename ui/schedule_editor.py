"""
Schedule Editor Tab - Create, edit, delete bell schedules with sound sequences.
"""
import json

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QFormLayout, QLineEdit, QTimeEdit, QCheckBox, QComboBox,
    QSpinBox, QGroupBox, QMessageBox, QAbstractItemView
)
from PySide6.QtCore import Qt, QTime
from PySide6.QtGui import QColor


DAY_KEYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']


class SequenceEditorDialog(QDialog):
    def __init__(self, db, loc, sound_engine, sequence=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.loc = loc
        self.sound_engine = sound_engine
        self.sequence = sequence if sequence else []
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self._setup_ui()
        self._load_sequence()
        self._apply_translations()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()

        self.add_sound_btn = QPushButton()
        self.add_sound_btn.clicked.connect(self._add_sound_step)
        btn_layout.addWidget(self.add_sound_btn)

        self.add_pause_btn = QPushButton()
        self.add_pause_btn.clicked.connect(self._add_pause_step)
        btn_layout.addWidget(self.add_pause_btn)

        self.remove_btn = QPushButton()
        self.remove_btn.setObjectName("dangerBtn")
        self.remove_btn.clicked.connect(self._remove_step)
        btn_layout.addWidget(self.remove_btn)

        self.move_up_btn = QPushButton("^")
        self.move_up_btn.setFixedWidth(40)
        self.move_up_btn.clicked.connect(self._move_up)
        btn_layout.addWidget(self.move_up_btn)

        self.move_down_btn = QPushButton("v")
        self.move_down_btn.setFixedWidth(40)
        self.move_down_btn.clicked.connect(self._move_down)
        btn_layout.addWidget(self.move_down_btn)

        layout.addLayout(btn_layout)

        self.preview_btn = QPushButton()
        self.preview_btn.clicked.connect(self._preview)
        layout.addWidget(self.preview_btn)

        dialog_btns = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton()
        self.cancel_btn.setObjectName("secondaryBtn")
        self.cancel_btn.clicked.connect(self.reject)
        dialog_btns.addStretch()
        dialog_btns.addWidget(self.cancel_btn)
        dialog_btns.addWidget(self.ok_btn)
        layout.addLayout(dialog_btns)

    def _apply_translations(self):
        self.setWindowTitle(self.loc.tr('sequence_editor'))
        self.table.setHorizontalHeaderLabels([
            self.loc.tr('seq_type'), self.loc.tr('seq_value'), self.loc.tr('seq_detail')
        ])
        self.add_sound_btn.setText(self.loc.tr('add_sound_step'))
        self.add_pause_btn.setText(self.loc.tr('add_pause_step'))
        self.remove_btn.setText(self.loc.tr('remove'))
        self.preview_btn.setText(self.loc.tr('preview_sequence'))
        self.cancel_btn.setText(self.loc.tr('cancel'))

    def _load_sequence(self):
        self.table.setRowCount(0)
        for item in self.sequence:
            self._add_row(item)

    def _add_row(self, item):
        row = self.table.rowCount()
        self.table.insertRow(row)

        if item.get('type') == 'sound':
            type_item = QTableWidgetItem(self.loc.tr('sound'))
            type_item.setData(Qt.ItemDataRole.UserRole, item)
            self.table.setItem(row, 0, type_item)
            self.table.setItem(row, 1, QTableWidgetItem(item.get('filename', '')))
            self.table.setItem(row, 2, QTableWidgetItem(''))
        elif item.get('type') == 'pause':
            type_item = QTableWidgetItem(self.loc.tr('pause'))
            type_item.setData(Qt.ItemDataRole.UserRole, item)
            self.table.setItem(row, 0, type_item)
            dur = item.get('duration', 1)
            h = dur // 3600
            m = (dur % 3600) // 60
            s = dur % 60
            self.table.setItem(row, 1, QTableWidgetItem(f"{h:02d}:{m:02d}:{s:02d}"))
            self.table.setItem(row, 2, QTableWidgetItem(''))

        for col in range(3):
            it = self.table.item(row, col)
            if it:
                it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)

    def _add_sound_step(self):
        sounds = self.sound_engine.get_available_sounds()
        if not sounds:
            QMessageBox.warning(self, self.loc.tr('warning'), self.loc.tr('no_sounds_available'))
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(self.loc.tr('select_sound'))
        layout = QVBoxLayout(dialog)

        combo = QComboBox()
        combo.addItems(sounds)
        layout.addWidget(combo)

        btn = QPushButton("OK")
        btn.clicked.connect(dialog.accept)
        layout.addWidget(btn)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            item = {'type': 'sound', 'filename': combo.currentText()}
            self.sequence.append(item)
            self._add_row(item)

    def _add_pause_step(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(self.loc.tr('pause_duration'))
        layout = QVBoxLayout(dialog)

        time_edit = QTimeEdit()
        time_edit.setDisplayFormat("HH:mm:ss")
        time_edit.setTime(QTime(0, 0, 0))
        layout.addWidget(time_edit)

        btn = QPushButton("OK")
        btn.clicked.connect(dialog.accept)
        layout.addWidget(btn)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            t = time_edit.time()
            total_seconds = t.hour() * 3600 + t.minute() * 60 + t.second()
            if total_seconds < 1:
                total_seconds = 1
            item = {'type': 'pause', 'duration': total_seconds}
            self.sequence.append(item)
            self._add_row(item)

    def _remove_step(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)
            if row < len(self.sequence):
                self.sequence.pop(row)

    def _move_up(self):
        row = self.table.currentRow()
        if row > 0:
            self.sequence[row], self.sequence[row - 1] = self.sequence[row - 1], self.sequence[row]
            self._load_sequence()
            self.table.setCurrentCell(row - 1, 0)

    def _move_down(self):
        row = self.table.currentRow()
        if 0 <= row < self.table.rowCount() - 1:
            self.sequence[row], self.sequence[row + 1] = self.sequence[row + 1], self.sequence[row]
            self._load_sequence()
            self.table.setCurrentCell(row + 1, 0)

    def _preview(self):
        if self.sequence:
            self.sound_engine.play_sequence(self.sequence)

    def get_sequence(self):
        return self.sequence


class BellEditDialog(QDialog):
    def __init__(self, db, loc, sound_engine, bell=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.loc = loc
        self.sound_engine = sound_engine
        self.bell = bell
        self.sequence = bell['sound_sequence'] if bell else []
        self.setMinimumWidth(450)
        self._setup_ui()
        self._apply_translations()
        if bell:
            self._load_bell()

    def _setup_ui(self):
        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.name_label = QLabel()
        layout.addRow(self.name_label, self.name_edit)

        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_label = QLabel()
        layout.addRow(self.time_label, self.time_edit)

        self.enabled_check = QCheckBox()
        self.enabled_check.setChecked(True)
        self.enabled_label = QLabel()
        layout.addRow(self.enabled_label, self.enabled_check)

        # Days
        self.days_group = QGroupBox()
        days_layout = QHBoxLayout(self.days_group)
        self.day_checks = {}
        for day in DAY_KEYS:
            cb = QCheckBox(day.upper())
            if day in ['mon', 'tue', 'wed', 'thu', 'fri']:
                cb.setChecked(True)
            self.day_checks[day] = cb
            days_layout.addWidget(cb)
        layout.addRow(self.days_group)

        # Sequence
        self.seq_label = QLabel()
        self.seq_info = QLabel()
        self.seq_info.setStyleSheet("color: #7f8c8d;")
        seq_layout = QHBoxLayout()
        seq_layout.addWidget(self.seq_info)
        self.edit_seq_btn = QPushButton()
        self.edit_seq_btn.clicked.connect(self._edit_sequence)
        seq_layout.addWidget(self.edit_seq_btn)
        layout.addRow(self.seq_label, seq_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton()
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton()
        self.cancel_btn.setObjectName("secondaryBtn")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addRow(btn_layout)

        self._update_seq_info()

    def _apply_translations(self):
        self.setWindowTitle(
            self.loc.tr('edit_bell') if self.bell else self.loc.tr('add_bell')
        )
        self.name_label.setText(self.loc.tr('bell_name'))
        self.time_label.setText(self.loc.tr('bell_time'))
        self.enabled_label.setText(self.loc.tr('enabled'))
        self.days_group.setTitle(self.loc.tr('days'))
        self.seq_label.setText(self.loc.tr('sound_sequence'))
        self.edit_seq_btn.setText(self.loc.tr('edit_sequence'))
        self.save_btn.setText(self.loc.tr('save'))
        self.cancel_btn.setText(self.loc.tr('cancel'))

        for day_key, cb in self.day_checks.items():
            cb.setText(self.loc.tr(f'day_{day_key}'))

    def _load_bell(self):
        self.name_edit.setText(self.bell['name'])
        parts = self.bell['time'].split(':')
        self.time_edit.setTime(QTime(int(parts[0]), int(parts[1])))
        self.enabled_check.setChecked(bool(self.bell['enabled']))
        for day in DAY_KEYS:
            self.day_checks[day].setChecked(day in self.bell['days'])

    def _edit_sequence(self):
        dialog = SequenceEditorDialog(
            self.db, self.loc, self.sound_engine,
            sequence=list(self.sequence), parent=self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.sequence = dialog.get_sequence()
            self._update_seq_info()

    def _update_seq_info(self):
        if self.sequence:
            parts = []
            for item in self.sequence:
                if item['type'] == 'sound':
                    parts.append(item['filename'])
                elif item['type'] == 'pause':
                    dur = item['duration']
                    h = dur // 3600
                    m = (dur % 3600) // 60
                    s = dur % 60
                    parts.append(f"[{h:02d}:{m:02d}:{s:02d}]")
            self.seq_info.setText(" > ".join(parts))
        else:
            self.seq_info.setText(self.loc.tr('no_sequence'))

    def get_bell_data(self):
        days = [day for day, cb in self.day_checks.items() if cb.isChecked()]
        return {
            'name': self.name_edit.text().strip() or self.loc.tr('unnamed_bell'),
            'time': self.time_edit.time().toString("HH:mm"),
            'enabled': self.enabled_check.isChecked(),
            'days': days,
            'sound_sequence': self.sequence,
        }


class ScheduleEditorTab(QWidget):
    def __init__(self, db, localization, scheduler, sound_engine):
        super().__init__()
        self.db = db
        self.loc = localization
        self.scheduler = scheduler
        self.sound_engine = sound_engine
        self._setup_ui()
        self._load_bells()

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
        self.add_btn.clicked.connect(self._add_bell)
        header.addWidget(self.add_btn)

        layout.addLayout(header)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self._edit_bell)
        layout.addWidget(self.table)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        self.edit_btn = QPushButton()
        self.edit_btn.clicked.connect(self._edit_bell)
        btn_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton()
        self.delete_btn.setObjectName("dangerBtn")
        self.delete_btn.clicked.connect(self._delete_bell)
        btn_layout.addWidget(self.delete_btn)

        self.toggle_btn = QPushButton()
        self.toggle_btn.clicked.connect(self._toggle_bell)
        btn_layout.addWidget(self.toggle_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def apply_translations(self):
        self.title_label.setText(self.loc.tr('schedule_title'))
        self.add_btn.setText(self.loc.tr('add_bell'))
        self.edit_btn.setText(self.loc.tr('edit_bell'))
        self.delete_btn.setText(self.loc.tr('delete_bell'))
        self.toggle_btn.setText(self.loc.tr('toggle_bell'))
        self.table.setHorizontalHeaderLabels([
            self.loc.tr('col_name'),
            self.loc.tr('col_time'),
            self.loc.tr('col_days'),
            self.loc.tr('col_sequence'),
            self.loc.tr('col_enabled'),
            'ID'
        ])
        self.table.setColumnHidden(5, True)
        self._load_bells()

    def _load_bells(self):
        self.table.setRowCount(0)
        bells = self.db.get_all_bells()

        for bell in bells:
            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 0, QTableWidgetItem(bell['name']))
            self.table.setItem(row, 1, QTableWidgetItem(bell['time']))

            day_labels = []
            for d in bell['days']:
                day_labels.append(self.loc.tr(f'day_{d}'))
            self.table.setItem(row, 2, QTableWidgetItem(', '.join(day_labels)))

            seq_count = len(bell['sound_sequence'])
            seq_text = f"{seq_count} {self.loc.tr('steps')}" if seq_count else self.loc.tr('no_sequence')
            self.table.setItem(row, 3, QTableWidgetItem(seq_text))

            enabled_text = self.loc.tr('yes') if bell['enabled'] else self.loc.tr('no')
            enabled_item = QTableWidgetItem(enabled_text)
            if not bell['enabled']:
                enabled_item.setForeground(QColor('#e74c3c'))
            else:
                enabled_item.setForeground(QColor('#27ae60'))
            self.table.setItem(row, 4, enabled_item)

            id_item = QTableWidgetItem(str(bell['id']))
            self.table.setItem(row, 5, id_item)

        self.table.resizeColumnsToContents()

    def _get_selected_bell_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        id_item = self.table.item(row, 5)
        return int(id_item.text()) if id_item else None

    def _add_bell(self):
        dialog = BellEditDialog(self.db, self.loc, self.sound_engine, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_bell_data()
            self.db.add_bell(data['name'], data['time'], data['days'], data['sound_sequence'])
            self._load_bells()
            self.scheduler.reload_schedule()

    def _edit_bell(self):
        bell_id = self._get_selected_bell_id()
        if bell_id is None:
            return

        bells = self.db.get_all_bells()
        bell = next((b for b in bells if b['id'] == bell_id), None)
        if not bell:
            return

        dialog = BellEditDialog(self.db, self.loc, self.sound_engine, bell=bell, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_bell_data()
            self.db.update_bell(
                bell_id, data['name'], data['time'],
                data['enabled'], data['days'], data['sound_sequence']
            )
            self._load_bells()
            self.scheduler.reload_schedule()

    def _delete_bell(self):
        bell_id = self._get_selected_bell_id()
        if bell_id is None:
            return

        reply = QMessageBox.question(
            self, self.loc.tr('confirm'),
            self.loc.tr('confirm_delete_bell'),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_bell(bell_id)
            self._load_bells()
            self.scheduler.reload_schedule()

    def _toggle_bell(self):
        bell_id = self._get_selected_bell_id()
        if bell_id is None:
            return

        bells = self.db.get_all_bells()
        bell = next((b for b in bells if b['id'] == bell_id), None)
        if bell:
            self.db.toggle_bell(bell_id, not bell['enabled'])
            self._load_bells()
            self.scheduler.reload_schedule()
