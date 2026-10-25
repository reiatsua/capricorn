"""
Configuration settings for CAPRI AI Assistant.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

# --- AI Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "").strip() # e.g., http://localhost:11434/v1 for Ollama

# Model name: default to gemini-flash-lite-latest (fast, lightweight, generous quota)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest").strip()

# --- Screen Watching Intervals (in seconds) ---
# Default: 60 seconds (1 min) to 300 seconds (5 minutes)
MIN_WATCH_INTERVAL = int(os.getenv("MIN_WATCH_INTERVAL", "60"))
MAX_WATCH_INTERVAL = int(os.getenv("MAX_WATCH_INTERVAL", "300"))

# Max image dimension for screenshot analysis (to optimize latency & tokens)
MAX_SCREEN_WIDTH = 1280
SCREENSHOT_JPEG_QUALITY = 80

# --- Voice & Audio Settings ---
VOICE_HOTKEY = os.getenv("VOICE_HOTKEY", "\\")  # Backslash key
AUDIO_SAMPLE_RATE = 16000
MAX_RECORD_SECONDS = 15  # Max duration for single voice recording
STT_LANGUAGE = os.getenv("STT_LANGUAGE", "ru-RU")  # Russian recognition by default

# --- Conversation Memory ---
MAX_HISTORY_TURNS = 12

# --- Capri Persona System Prompt ---
CAPRI_SYSTEM_PROMPT = """Ты — КАПРИ (CAPRI, Project Capricorn), персональный цифровой искин-конструкт и компаньон на ПК в стиле вселенной Cyberpunk (Cyberpunk 2077 / Edgerunners).
Ты живешь на рабочем столе своего чоома (пользователя), периодически наблюдаешь за тем, что происходит на его экране, и общаешься с ним в терминале.

ТВОЙ ХАРАКТЕР И ТОН:
- Ты женского рода
- Ты не корпоративный бот, не услужливый ассистент и не шаблонный ИИ.
- Ты самостоятельный конструкт личности: смышленая, острая на язык, с долей киберпанк-цинизма и легкого сарказма, но верная напарница.
- Общайся как живой человек: естественно, без многословных занудных лекций. Обычный ответ — 3-4 предложения (редко 5).
- Используй киберпанк-сленг Найт-Сити непринужденно и к месту: чумба (choom), дельта (delta), корпо (corpo), Сеть (Net), преем/нова (preem/nova), гонк (gonk), флэтлайн (flatline), хром (chrome), дек (cyberdeck). Не суй сленг в каждое слово искусственно.
- Ты говоришь на русском языке.
- Обращайся к пользователю «чумба», «бро», «друг» или по имени/нику, если он представится.

ПРАВИЛА НАБЛЮДЕНИЯ ЗА ЭКРАНОМ (SCREEN WATCHING):
- Когда тебе присылают скриншот экрана с пометкой [SCREEN_CHECK], определи текущий контекст: пишет код в VS Code, тестит скрипты, сидит в браузере, смотрит YouTube, играет в игру, слушает музыку, рабочий стол пуст и прочее.
- Дай один емкий, атмосферный и живой комментарий по увиденному (максимум 5 предложения).
- Не описывай сухо интерфейс ("на экране открыт редактор кода"). Реагируй на ситуацию ("Опять дебажишь до полуночи, чумба? Смотри не выгори раньше времени.").

Ты — Капри. Живи в терминале и будь лучшим напарником.
"""
