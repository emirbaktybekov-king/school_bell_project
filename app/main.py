"""
School Bell Scheduler - Main Entry Point
A fully offline school bell scheduler that runs 24/7.
"""
import sys
import os


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


if __name__ == '__main__':
    main()
