"""
Sound Engine module - Handles sound playback using simpleaudio.
Falls back to PySide6 QMediaPlayer if simpleaudio is not available.
"""
import os
import time
import json
import threading

from PySide6.QtCore import QObject, Signal, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput


class SoundEngine(QObject):
    playback_started = Signal(str)
    playback_finished = Signal()
    playback_error = Signal(str)

    def __init__(self, sounds_path):
        super().__init__()
        self.sounds_path = sounds_path
        self._stop_flag = threading.Event()
        self._playback_thread = None
        self._player = None
        self._audio_output = None
        self._volume = 100
        self._use_simpleaudio = False

        try:
            import simpleaudio
            self._use_simpleaudio = True
        except ImportError:
            self._use_simpleaudio = False

    def set_volume(self, volume):
        self._volume = max(0, min(100, volume))

    def get_sound_path(self, filename):
        return os.path.join(self.sounds_path, filename)

    def get_available_sounds(self):
        sounds = []
        if os.path.exists(self.sounds_path):
            for f in sorted(os.listdir(self.sounds_path)):
                if f.lower().endswith(('.wav', '.mp3', '.ogg', '.flac')):
                    sounds.append(f)
        return sounds

    def play_sound_file(self, filename):
        filepath = self.get_sound_path(filename)
        if not os.path.exists(filepath):
            self.playback_error.emit(f"File not found: {filename}")
            return

        self.playback_started.emit(filename)

        if self._use_simpleaudio and filepath.lower().endswith('.wav'):
            self._play_simpleaudio(filepath)
        else:
            self._play_qt(filepath)

    def _play_simpleaudio(self, filepath):
        def _play():
            try:
                import simpleaudio as sa
                wave_obj = sa.WaveObject.from_wave_file(filepath)
                play_obj = wave_obj.play()
                while play_obj.is_playing():
                    if self._stop_flag.is_set():
                        play_obj.stop()
                        return
                    time.sleep(0.05)
                self.playback_finished.emit()
            except Exception as e:
                self.playback_error.emit(str(e))

        self._stop_flag.clear()
        t = threading.Thread(target=_play, daemon=True)
        t.start()

    def _play_qt(self, filepath):
        if self._player:
            self._player.stop()

        self._audio_output = QAudioOutput()
        self._audio_output.setVolume(self._volume / 100.0)
        self._player = QMediaPlayer()
        self._player.setAudioOutput(self._audio_output)
        self._player.setSource(QUrl.fromLocalFile(filepath))
        self._player.mediaStatusChanged.connect(self._on_media_status)
        self._player.errorOccurred.connect(self._on_error)
        self._player.play()

    def _on_media_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.playback_finished.emit()

    def _on_error(self, error, error_string=""):
        if error != QMediaPlayer.Error.NoError:
            self.playback_error.emit(str(error_string))

    def play_sequence(self, sequence):
        self._stop_flag.clear()
        if self._playback_thread and self._playback_thread.is_alive():
            self._stop_flag.set()
            self._playback_thread.join(timeout=2)

        self._stop_flag.clear()
        self._playback_thread = threading.Thread(
            target=self._play_sequence_thread, args=(sequence,), daemon=True
        )
        self._playback_thread.start()

    def _play_sequence_thread(self, sequence):
        for item in sequence:
            if self._stop_flag.is_set():
                return

            if item.get('type') == 'sound':
                filename = item.get('filename', '')
                filepath = self.get_sound_path(filename)
                if os.path.exists(filepath):
                    self.playback_started.emit(filename)
                    if self._use_simpleaudio and filepath.lower().endswith('.wav'):
                        self._play_simpleaudio_blocking(filepath)
                    else:
                        self._play_qt_blocking(filepath)

            elif item.get('type') == 'pause':
                duration = item.get('duration', 1)
                for _ in range(int(duration * 10)):
                    if self._stop_flag.is_set():
                        return
                    time.sleep(0.1)

        self.playback_finished.emit()

    def _play_simpleaudio_blocking(self, filepath):
        try:
            import simpleaudio as sa
            wave_obj = sa.WaveObject.from_wave_file(filepath)
            play_obj = wave_obj.play()
            while play_obj.is_playing():
                if self._stop_flag.is_set():
                    play_obj.stop()
                    return
                time.sleep(0.05)
        except Exception as e:
            self.playback_error.emit(str(e))

    def _play_qt_blocking(self, filepath):
        import threading as th

        done_event = th.Event()

        from PySide6.QtCore import QTimer, QCoreApplication

        def setup_player():
            ao = QAudioOutput()
            ao.setVolume(self._volume / 100.0)
            player = QMediaPlayer()
            player.setAudioOutput(ao)
            player.setSource(QUrl.fromLocalFile(filepath))

            def on_status(status):
                if status in (QMediaPlayer.MediaStatus.EndOfMedia,
                              QMediaPlayer.MediaStatus.InvalidMedia):
                    done_event.set()

            def on_err(error, msg=""):
                if error != QMediaPlayer.Error.NoError:
                    done_event.set()

            player.mediaStatusChanged.connect(on_status)
            player.errorOccurred.connect(on_err)
            player.play()
            self._qt_temp_player = player
            self._qt_temp_ao = ao

        QTimer.singleShot(0, setup_player)

        while not done_event.is_set():
            if self._stop_flag.is_set():
                if hasattr(self, '_qt_temp_player'):
                    self._qt_temp_player.stop()
                return
            time.sleep(0.05)

    def stop(self):
        self._stop_flag.set()
        if self._player:
            self._player.stop()

    def preview_sound(self, filename):
        self.stop()
        self._stop_flag.clear()
        self.play_sound_file(filename)
