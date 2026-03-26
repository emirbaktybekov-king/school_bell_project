"""
Sound Engine module - Handles sound playback.
Primary: Windows MCI (winmm.dll) for reliable MP3/WAV playback from any thread.
Fallback: PySide6 QMediaPlayer, simpleaudio (WAV only).
"""
import os
import sys
import time
import logging
import platform
import subprocess
import threading

from PySide6.QtCore import QObject, Signal, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QMediaDevices, QAudioDevice


class SoundEngine(QObject):
    playback_started = Signal(str)
    playback_finished = Signal()
    playback_error = Signal(str)
    _qt_play_requested = Signal(str)

    def __init__(self, sounds_path):
        super().__init__()
        self.sounds_path = sounds_path
        self._stop_flag = threading.Event()
        self._playback_thread = None
        self._player = None
        self._audio_output = None
        self._volume = 100
        self._output_device = None
        self._use_simpleaudio = False
        self._qt_done_event = None
        self._native_proc = None
        self._qt_play_requested.connect(self._setup_qt_player)

        # Check for Windows MCI support
        self._has_mci = False
        if sys.platform == 'win32':
            try:
                import ctypes
                self._winmm = ctypes.windll.winmm
                self._has_mci = True
            except Exception:
                self._has_mci = False

        try:
            import simpleaudio
            self._use_simpleaudio = True
        except ImportError:
            self._use_simpleaudio = False

    def set_volume(self, volume):
        self._volume = max(0, min(100, volume))

    def set_output_device(self, device_id):
        if not device_id:
            self._output_device = None
            return
        for device in QMediaDevices.audioOutputs():
            dev_id = device.id().data().decode('utf-8', errors='replace')
            if dev_id == device_id:
                self._output_device = device
                return
        self._output_device = None

    def _create_audio_output(self):
        if self._output_device:
            ao = QAudioOutput(self._output_device)
        else:
            ao = QAudioOutput()
        ao.setVolume(self._volume / 100.0)
        return ao

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

        self._audio_output = self._create_audio_output()
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
        try:
            self._stop_flag.clear()
            if self._playback_thread and self._playback_thread.is_alive():
                self._stop_flag.set()
                self._playback_thread.join(timeout=2)

            self._stop_flag.clear()
            self._playback_thread = threading.Thread(
                target=self._play_sequence_thread, args=(sequence,), daemon=True
            )
            self._playback_thread.start()
        except Exception as e:
            self.playback_error.emit(str(e))

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
                        self._play_blocking(filepath)

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

    # ---- Platform-native blocking playback (called from background thread) ----

    def _play_blocking(self, filepath):
        """Play a sound file and block until done. Works from any thread."""
        # Windows: use MCI (winmm.dll) - built into every Windows, supports MP3
        if self._has_mci:
            if self._play_windows_mci(filepath):
                return

        # macOS: use afplay (development only)
        if platform.system() == 'Darwin':
            if self._play_afplay(filepath):
                return

        # Fallback: QMediaPlayer via main-thread signal
        self._play_qt_blocking(filepath)

    def _play_windows_mci(self, filepath):
        """Play sound using Windows MCI (winmm.dll). Works from any thread."""
        try:
            import ctypes
            winmm = self._winmm
            alias = "schoolbell"
            buf = ctypes.create_unicode_buffer(256)

            # Close any previous instance
            winmm.mciSendStringW(f'close {alias}', None, 0, 0)

            # Open the file
            ret = winmm.mciSendStringW(
                f'open "{filepath}" alias {alias}', buf, 256, 0
            )
            if ret != 0:
                return False

            # Set volume (MCI uses 0-1000)
            vol = int(self._volume * 10)
            winmm.mciSendStringW(
                f'setaudio {alias} volume to {vol}', None, 0, 0
            )

            # Start playback (non-blocking MCI call, we poll for completion)
            winmm.mciSendStringW(f'play {alias}', None, 0, 0)

            # Wait until done or stopped
            while True:
                if self._stop_flag.is_set():
                    winmm.mciSendStringW(f'stop {alias}', None, 0, 0)
                    break
                winmm.mciSendStringW(
                    f'status {alias} mode', buf, 256, 0
                )
                if buf.value != 'playing':
                    break
                time.sleep(0.05)

            winmm.mciSendStringW(f'close {alias}', None, 0, 0)
            return True
        except Exception as e:
            logging.warning("Windows MCI playback failed: %s", e)
            return False

    def _play_afplay(self, filepath):
        """Play sound using macOS afplay. Works from any thread."""
        try:
            volume = self._volume / 100.0
            proc = subprocess.Popen(
                ['afplay', '-v', str(volume), filepath],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            self._native_proc = proc
            while proc.poll() is None:
                if self._stop_flag.is_set():
                    proc.terminate()
                    self._native_proc = None
                    return True
                time.sleep(0.05)
            self._native_proc = None
            return True
        except Exception as e:
            logging.warning("afplay failed: %s", e)
            return False

    def _setup_qt_player(self, filepath):
        """Slot that runs on the main thread to create and play QMediaPlayer."""
        done_event = self._qt_done_event
        ao = self._create_audio_output()
        player = QMediaPlayer()
        player.setAudioOutput(ao)
        player.setSource(QUrl.fromLocalFile(filepath))

        def on_status(status):
            if status in (QMediaPlayer.MediaStatus.EndOfMedia,
                          QMediaPlayer.MediaStatus.InvalidMedia):
                if done_event:
                    done_event.set()

        def on_err(error, msg=""):
            if error != QMediaPlayer.Error.NoError:
                if done_event:
                    done_event.set()

        player.mediaStatusChanged.connect(on_status)
        player.errorOccurred.connect(on_err)
        player.play()
        self._qt_temp_player = player
        self._qt_temp_ao = ao

    def _play_qt_blocking(self, filepath):
        """Fallback: QMediaPlayer via signal to main thread."""
        done_event = threading.Event()
        self._qt_done_event = done_event
        self._qt_play_requested.emit(filepath)

        timeout = 30.0
        elapsed = 0.0
        while not done_event.is_set() and elapsed < timeout:
            if self._stop_flag.is_set():
                if hasattr(self, '_qt_temp_player') and self._qt_temp_player:
                    self._qt_temp_player.stop()
                return
            time.sleep(0.05)
            elapsed += 0.05

    def stop(self):
        self._stop_flag.set()
        if self._player:
            self._player.stop()
        if self._native_proc and self._native_proc.poll() is None:
            self._native_proc.terminate()
            self._native_proc = None
        # MCI stop is handled by the polling loop via _stop_flag

    def preview_sound(self, filename):
        self.stop()
        self._stop_flag.clear()
        self.play_sound_file(filename)
