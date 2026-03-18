"""
School Bell Scheduler - Main Entry Point
A fully offline school bell scheduler that runs 24/7.
Crash-proof: auto-restarts on unhandled exceptions.
"""
import sys
import os
import logging
import traceback
from datetime import datetime


def setup_logging(data_path):
    """Set up file logging for crash diagnostics."""
    log_file = os.path.join(data_path, 'school_bell.log')
    logging.basicConfig(
        filename=log_file,
        level=logging.WARNING,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    # Keep log file from growing forever: truncate if > 1MB
    try:
        if os.path.exists(log_file) and os.path.getsize(log_file) > 1_000_000:
            with open(log_file, 'w') as f:
                f.write(f"--- Log truncated at {datetime.now()} ---\n")
    except OSError:
        pass


def get_base_path():
    """Get the base path for bundled or development mode."""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_data_path():
    """Get writable data path for database and user files."""
    if getattr(sys, 'frozen', False):
        app_data = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'SchoolBellScheduler')
    else:
        app_data = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    os.makedirs(app_data, exist_ok=True)
    return app_data


def get_sounds_path():
    """Get writable path for user sound files."""
    if getattr(sys, 'frozen', False):
        sounds_dir = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'SchoolBellScheduler', 'sounds')
    else:
        sounds_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'sounds')
    os.makedirs(sounds_dir, exist_ok=True)
    return sounds_dir


# Make paths available globally
BASE_PATH = get_base_path()
DATA_PATH = get_data_path()
SOUNDS_PATH = get_sounds_path()


def copy_bundled_assets():
    """Copy bundled assets to writable location on first run."""
    import shutil
    bundled_sounds = os.path.join(BASE_PATH, 'assets', 'sounds')
    if os.path.exists(bundled_sounds):
        for f in os.listdir(bundled_sounds):
            src = os.path.join(bundled_sounds, f)
            dst = os.path.join(SOUNDS_PATH, f)
            if not os.path.exists(dst) and os.path.isfile(src):
                shutil.copy2(src, dst)

    bundled_db = os.path.join(BASE_PATH, 'data', 'school_bell.db')
    target_db = os.path.join(DATA_PATH, 'school_bell.db')
    if os.path.exists(bundled_db) and not os.path.exists(target_db):
        shutil.copy2(bundled_db, target_db)


def main():
    setup_logging(DATA_PATH)

    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt, QCoreApplication
    from PySide6.QtGui import QIcon

    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

    app = QApplication(sys.argv)
    app.setApplicationName("School Bell Scheduler")
    app.setOrganizationName("SchoolBell")
    app.setQuitOnLastWindowClosed(False)

    icon_path = os.path.join(BASE_PATH, 'assets', 'icon.png')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    copy_bundled_assets()

    from app.database import Database
    from app.localization import Localization
    from app.scheduler import BellScheduler
    from app.sound_engine import SoundEngine
    from app.tray import SystemTray
    from ui.main_window import MainWindow

    db = Database(os.path.join(DATA_PATH, 'school_bell.db'))
    localization = Localization(os.path.join(BASE_PATH, 'locales'))

    lang = db.get_setting('language', 'en')
    localization.set_language(lang)

    sound_engine = SoundEngine(SOUNDS_PATH)
    volume = int(db.get_setting('volume', '100'))
    sound_engine.set_volume(volume)
    audio_device = db.get_setting('audio_device', '')
    if audio_device:
        sound_engine.set_output_device(audio_device)
    scheduler = BellScheduler(db, sound_engine)

    window = MainWindow(db, localization, scheduler, sound_engine)
    tray = SystemTray(app, window, scheduler, localization)

    start_minimized = db.get_setting('start_minimized', 'false') == 'true'
    if start_minimized:
        window.hide()
    else:
        window.show()

    scheduler.start()

    exit_code = app.exec()
    scheduler.stop()
    db.close()
    sys.exit(exit_code)


def run_with_recovery():
    """Run the app with automatic crash recovery. Restarts up to 10 times."""
    import time as _time
    max_restarts = 10
    restart_count = 0

    while restart_count < max_restarts:
        try:
            main()
            return
        except SystemExit:
            return
        except Exception:
            restart_count += 1
            logging.critical(
                "CRASH #%d — restarting:\n%s",
                restart_count, traceback.format_exc()
            )
            _time.sleep(2)

    logging.critical("Max restarts (%d) reached. Giving up.", max_restarts)
    sys.exit(1)


if __name__ == '__main__':
    run_with_recovery()
