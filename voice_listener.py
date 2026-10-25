"""
Global hotkey voice listener and Speech-to-Text handler.
"""

import time
import threading
from typing import Callable, List, Optional
import numpy as np
import sounddevice as sd
import speech_recognition as sr
from pynput import keyboard

import config
from terminal_ui import ui

class VoiceListener:
    """Manages hotkey listening and voice recording/transcription."""

    def __init__(self, on_voice_recognized: Callable[[str], None], on_voice_started: Optional[Callable[[], None]] = None):
        self.on_voice_recognized = on_voice_recognized
        self.on_voice_started = on_voice_started
        self.recognizer = sr.Recognizer()

        self._is_recording = False
        self._record_lock = threading.Lock()
        self._audio_chunks: List[np.ndarray] = []
        self._stream: Optional[sd.InputStream] = None
        self._record_start_time = 0.0

        self._hotkey_listener: Optional[keyboard.Listener] = None

    def start(self):
        """Start listening for the global hotkey."""
        self._hotkey_listener = keyboard.Listener(on_press=self._on_key_press)
        self._hotkey_listener.daemon = True
        self._hotkey_listener.start()
        ui.print_system(f"Voice Listener active. Press '{config.VOICE_HOTKEY}' anywhere to speak.")

    def stop(self):
        if self._hotkey_listener:
            self._hotkey_listener.stop()
        self._stop_recording_internal()

    def _on_key_press(self, key):
        """Triggered whenever a key is pressed."""
        is_target_key = False

        # Check for character '\\'
        if hasattr(key, "char") and key.char == config.VOICE_HOTKEY:
            is_target_key = True
        # Check for Windows VK_OEM_5 (220) which is '\\' / '/' on Russian & US layouts
        elif getattr(key, "vk", None) == 220:
            is_target_key = True

        if is_target_key:
            self._toggle_recording()

    def toggle_recording(self):
        """Programmatically toggle recording (e.g. from UI)."""
        self._toggle_recording()

    def _toggle_recording(self):
        with self._record_lock:
            if not self._is_recording:
                self._start_recording_internal()
            else:
                self._stop_and_process_internal()

    def _audio_callback(self, indata, frames, time_info, status):
        """Stream callback that collects raw audio frames."""
        if self._is_recording:
            self._audio_chunks.append(indata.copy())

            # Auto-stop if exceeding max record duration
            if time.time() - self._record_start_time > config.MAX_RECORD_SECONDS:
                threading.Thread(target=self._auto_stop_timeout, daemon=True).start()

    def _auto_stop_timeout(self):
        with self._record_lock:
            if self._is_recording:
                ui.print_status("LISTENING", "Max record time reached. Stopping...")
                self._stop_and_process_internal()

    def _start_recording_internal(self):
        self._is_recording = True
        self._audio_chunks = []
        self._record_start_time = time.time()

        try:
            self._stream = sd.InputStream(
                samplerate=config.AUDIO_SAMPLE_RATE,
                channels=1,
                dtype="int16",
                callback=self._audio_callback
            )
            self._stream.start()
            ui.print_status("LISTENING", f"Recording audio... Speak now! (Press '{config.VOICE_HOTKEY}' again to send)")
            if self.on_voice_started:
                self.on_voice_started()
        except Exception as e:
            self._is_recording = False
            ui.print_status("ERROR", f"Failed to start mic stream: {e}")

    def _stop_recording_internal(self):
        self._is_recording = False
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

    def _stop_and_process_internal(self):
        self._stop_recording_internal()
        chunks = list(self._audio_chunks)
        self._audio_chunks = []

        if not chunks:
            ui.print_status("NOISE", "Empty audio buffer.")
            return

        # Process STT in a background worker thread to keep hotkey responsive
        threading.Thread(target=self._transcribe_worker, args=(chunks,), daemon=True).start()

    def _transcribe_worker(self, chunks: List[np.ndarray]):
        ui.print_status("THINKING", "Transcribing speech...")
        try:
            audio_data = np.concatenate(chunks, axis=0)
            raw_bytes = audio_data.tobytes()

            sr_audio = sr.AudioData(raw_bytes, config.AUDIO_SAMPLE_RATE, 2)

            # Recognize using Google STT (default ru-RU, fallback to en-US)
            try:
                text = self.recognizer.recognize_google(sr_audio, language=config.STT_LANGUAGE)
            except sr.UnknownValueError:
                # Try English fallback
                try:
                    text = self.recognizer.recognize_google(sr_audio, language="en-US")
                except sr.UnknownValueError:
                    ui.print_status("NOISE", "Не разобрала речь, чоом. Попробуй еще раз.")
                    return

            if text.strip():
                self.on_voice_recognized(text.strip())

        except sr.RequestError as e:
            ui.print_status("ERROR", f"Network error during speech recognition: {e}")
        except Exception as e:
            ui.print_status("ERROR", f"Voice processing error: {e}")
