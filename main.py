"""
CAPRI Desktop AI Assistant - Unified Desktop Overlay & Backend Daemon.

Features:
- Floating 8-pointed Cyberpunk Star desktop widget that drifts gently across the screen
- Periodic Screen Watching (30s to 5min) with popup animation and dialogue
- Interactive Dialogue Box with animated construct avatar and text input
- Global Voice Listening on '\\' hotkey with Speech-to-Text
- Dual operation: Works both via GUI popup and VS Code terminal
"""

import sys
import threading
import time
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal

import config
from terminal_ui import ui
from ai_brain import CapriBrain
from screen_watcher import ScreenWatcher
from voice_listener import VoiceListener
from capri_widget import CapriFloatingStar

class CapriQtBridge(QObject):
    sig_screen_analyzed = pyqtSignal(str)
    sig_voice_started = pyqtSignal()
    sig_voice_transcribed = pyqtSignal(str)
    sig_ai_reply = pyqtSignal(str)
    sig_status = pyqtSignal(str)

def run_app():
    # 1. Initialize Qt Application
    app = QApplication(sys.argv)
    app.setApplicationName("CAPRI // Desktop Construct")

    # 2. Initialize AI Brain
    brain = CapriBrain()

    # 3. Print Welcome Banner to terminal
    ui.print_banner(
        provider=brain.provider,
        min_interval=config.MIN_WATCH_INTERVAL,
        max_interval=config.MAX_WATCH_INTERVAL,
        hotkey=config.VOICE_HOTKEY
    )

    if brain.provider == "Offline Demo (Mock)":
        ui.print_system(
            "Внимание: ключ API не найден в .env. Capri работает в оффлайн демо-режиме.\n"
            "      Чтобы подключить полный интеллект, создай файл .env с параметром:\n"
            "      GEMINI_API_KEY=твой_ключ"
        )

    # 4. Initialize Qt Bridge
    bridge = CapriQtBridge()

    # 5. Create Floating Star Widget
    star = CapriFloatingStar()
    star.show()

    # Connect bridge signals to star widget slots
    bridge.sig_screen_analyzed.connect(star.on_screen_analyzed)
    bridge.sig_voice_started.connect(star.on_voice_started)
    bridge.sig_voice_transcribed.connect(star.on_voice_transcribed)
    bridge.sig_ai_reply.connect(star.on_ai_reply)

    # Handlers for background workers
    def on_screen_analyzed(img):
        if screen_watcher.is_paused():
            return
        ui.print_status("WATCHING", "Analyzing captured screen...")
        comment = brain.analyze_screen(img)
        # The dialogue may have opened while the AI was analyzing the captured image.
        if screen_watcher.is_paused():
            ui.print_system("Описание экрана отменено: диалог открыт или действует минутная пауза.")
            return
        ui.print_capri(comment, source="WATCHING")
        bridge.sig_screen_analyzed.emit(comment)

    def on_voice_recognized(text):
        ui.print_user(text, is_voice=True)
        bridge.sig_voice_transcribed.emit(text)

        def _voice_reply_worker():
            ui.print_status("THINKING", "Генерирую ответ...")
            reply = brain.respond_to_text(text)
            ui.print_capri(reply, source="TALKING")
            bridge.sig_ai_reply.emit(reply)

        threading.Thread(target=_voice_reply_worker, daemon=True).start()

    def on_voice_started():
        bridge.sig_voice_started.emit()

    # When user sends message from the dialogue GUI
    def on_user_sent_message(text):
        def _gui_reply_worker():
            ui.print_status("THINKING", "Генерирую ответ...")
            reply = brain.respond_to_text(text)
            ui.print_capri(reply, source="TALKING")
            bridge.sig_ai_reply.emit(reply)

        threading.Thread(target=_gui_reply_worker, daemon=True).start()

    star.user_sent_message.connect(on_user_sent_message)

    # 6. Initialize Background Services
    screen_watcher = ScreenWatcher(on_screen_analyzed=on_screen_analyzed)
    voice_listener = VoiceListener(on_voice_recognized=on_voice_recognized, on_voice_started=on_voice_started)

    star.dialogue_opened.connect(lambda: screen_watcher.set_dialogue_open(True))
    star.dialogue_closed.connect(lambda: screen_watcher.set_dialogue_open(False))
    star.request_screen_check.connect(screen_watcher.trigger_now)
    star.request_voice_toggle.connect(voice_listener.toggle_recording)

    screen_watcher.start()
    voice_listener.start()

    # Initial greeting in terminal
    time.sleep(0.3)
    ui.print_capri("Системы онлайн, чумба. Спотифай на прицеле, дек подключен к системе, файлы под присмотром (read-only).", source="ONLINE")

    # Connect widget close event to clean shutdown
    def on_shutdown():
        ui.print_system("Останавливаю службы...")
        screen_watcher.stop()
        voice_listener.stop()
        ui.print_system("Капри отключена.")

    star.closed.connect(on_shutdown)
    app.aboutToQuit.connect(on_shutdown)

    # Console reader in background so user can also type commands in terminal
    def console_reader():
        while True:
            try:
                line = input().strip()
                if not line:
                    continue
                if line.lower() in ["/exit", "/quit"]:
                    app.quit()
                    break
                elif line.lower() in ["/watch", "/see"]:
                    screen_watcher.trigger_now()
                elif line.lower() == "/status":
                    ui.print_system(f"Провайдер: {brain.provider} | Память: {len(brain.history)}")
                elif line.lower() == "/clear":
                    brain.clear_memory()
                    ui.print_system("Память диалога очищена.")
                else:
                    ui.print_user(line, is_voice=False)
                    star.dialogue_box.append_user_message(line, is_voice=False)
                    star.dialogue_box.set_thinking_state()
                    star.set_state("THINKING")
                    on_user_sent_message(line)
            except (EOFError, KeyboardInterrupt):
                app.quit()
                break

    threading.Thread(target=console_reader, daemon=True).start()

    # 7. Run Qt Event Loop
    sys.exit(app.exec())

if __name__ == "__main__":
    run_app()
