# School Bell Scheduler

A fully offline school bell scheduler desktop application for Windows.

## Features

- Runs 24/7 on local system time
- System tray integration with minimize-to-tray
- Customizable bell schedule with day-of-week selection
- Configurable sound sequences (sound + pause chains)
- Sound file management (WAV, MP3, OGG, FLAC)
- Three languages: English, Russian, Kyrgyz
- Windows autostart support
- Volume control

## Requirements (Development)

- Python 3.11+
- PySide6
- simpleaudio
- PyInstaller (for building)

## Quick Start (Development)

```bash
pip install -r requirements.txt
python -m app.main
```

## Building the Executable

On Windows, run:

```bash
build_windows_exe.bat
```

Or manually:

```bash
pip install -r requirements.txt
pyinstaller --onefile --noconsole --name SchoolBell ^
    --add-data "assets;assets" ^
    --add-data "locales;locales" ^
    --add-data "data;data" ^
    app/main.py
```

The output will be at `dist/SchoolBell.exe`.

## Usage

1. Double-click `SchoolBell.exe`
2. Add bell times in the Schedule tab
3. Add sound files in the Sounds tab
4. Configure sound sequences for each bell
5. The app runs in the system tray

## Folder Structure

```
school_bell_project/
  app/
    main.py          - Entry point
    scheduler.py     - Bell timing engine
    sound_engine.py  - Sound playback
    database.py      - SQLite database
    tray.py          - System tray
    localization.py  - Multi-language support
  ui/
    main_window.py   - Main application window
    dashboard.py     - Dashboard tab
    schedule_editor.py - Schedule management
    sounds_manager.py  - Sound file management
    settings.py      - Application settings
  assets/
    sounds/          - Sound files directory
  locales/
    en.json          - English
    ru.json          - Russian
    kg.json          - Kyrgyz
  data/
    school_bell.db   - SQLite database (auto-created)
```

## System Tray

- Double-click tray icon to open
- Right-click for menu: Open, Pause/Resume, Exit
- Close button minimizes to tray (does not exit)

## Database

SQLite database with tables:
- `bells` - Bell schedules with time, days, and sound sequences
- `sounds` - Registered sound files
- `settings` - Application configuration
