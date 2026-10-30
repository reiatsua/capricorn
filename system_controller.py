"""
System Controller for CAPRI.
Provides tools to control the PC:
- Spotify & Media Playback Control
- Opening Applications and Websites
- Browsing, searching, and reading files (STRICTLY READ-ONLY)
"""

import os
import sys
import glob
import time
import ctypes
import urllib.parse
import webbrowser
import subprocess
from typing import List, Dict, Optional
from terminal_ui import ui

# Win32 Virtual Key Constants for Media and Volume
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3
KEYEVENTF_KEYUP = 0x0002

def _press_key(vk_code: int, repeat: int = 1):
    """Simulates pressing and releasing a virtual key code."""
    try:
        user32 = ctypes.windll.user32
        for _ in range(repeat):
            user32.keybd_event(vk_code, 0, 0, 0)
            time.sleep(0.03)
            user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)
            time.sleep(0.03)
    except Exception as e:
        ui.print_status("ERROR", f"Failed to press key {vk_code}: {e}")

# ==============================================================================
# 1. SPOTIFY & MEDIA CONTROLS
# ==============================================================================

def play_spotify(query: str = "") -> str:
    """
    Запустить воспроизведение или найти музыку в Spotify.
    
    Args:
        query: поисковый запрос (артист, трек, жанр или плейлист, например: 'cyberpunk 2077', 'synthwave', 'phonk').
               Если оставить query пустым, переключает воспроизведение (Play / Pause).
    """
    query = (query or "").strip()
    ui.print_system(f"Выполняю команду Spotify: query='{query}'")

    if not query:
        # Toggle Play/Pause on current media
        _press_key(VK_MEDIA_PLAY_PAUSE)
        return "Переключила воспроизведение в Spotify (Play/Pause), чумба."

    try:
        # Spotify search URI
        encoded_query = urllib.parse.quote(query)
        spotify_uri = f"spotify:search:{encoded_query}"
        
        # Start spotify search URI via Windows protocol
        os.startfile(spotify_uri)
        time.sleep(0.8)
        # Attempt to trigger play on active search
        _press_key(VK_MEDIA_PLAY_PAUSE)
        return f"Запустила поиск и воспроизведение в Spotify по запросу: '{query}'."
    except Exception as e:
        # Fallback to web search if desktop uri fails
        web_url = f"https://open.spotify.com/search/{urllib.parse.quote(query)}"
        webbrowser.open(web_url)
        return f"Открыла веб-плеер Spotify с поиском '{query}' (ошибка десктоп-протокола: {e})."

def control_playback(action: str) -> str:
    """
    Управление воспроизведением и громкостью мультимедиа и Spotify.
    
    Args:
        action: одно из действий:
            - 'play_pause': воспроизведение / пауза
            - 'next': следующий трек
            - 'prev': предыдущий трек
            - 'volume_up': прибавить громкость
            - 'volume_down': убавить громкость
            - 'mute': заглушить звук
    """
    action = (action or "").strip().lower()
    ui.print_system(f"Команда мультимедиа: action='{action}'")

    if action in ["play_pause", "play", "pause", "toggle"]:
        _press_key(VK_MEDIA_PLAY_PAUSE)
        return "Переключила плей/паузу, чумба."
    elif action in ["next", "skip", "след", "следующий"]:
        _press_key(VK_MEDIA_NEXT_TRACK)
        return "Переключила на следующий трек."
    elif action in ["prev", "previous", "назад", "предыдущий"]:
        _press_key(VK_MEDIA_PREV_TRACK)
        return "Вернула предыдущий трек."
    elif action in ["volume_up", "louder", "громче", "плюс"]:
        _press_key(VK_VOLUME_UP, repeat=4)
        return "Сделала звук погромче."
    elif action in ["volume_down", "quieter", "тише", "минус"]:
        _press_key(VK_VOLUME_DOWN, repeat=4)
        return "Убавила громкость."
    elif action in ["mute", "unmute", "глуши", "тишина"]:
        _press_key(VK_VOLUME_MUTE)
        return "Переключила режим без звука (Mute)."
    else:
        _press_key(VK_MEDIA_PLAY_PAUSE)
        return f"Выполнила базовую команду переключения для '{action}'."

# ==============================================================================
# 2. APPLICATIONS & WEBSITES
# ==============================================================================

# Common app aliases
APP_ALIASES = {
    "spotify": "spotify:",
    "спотифай": "spotify:",
    "спотик": "spotify:",
    "discord": "discord:",
    "дискорд": "discord:",
    "диск": "discord:",
    "steam": "steam:",
    "стим": "steam:",
    "telegram": "telegram.exe",
    "телеграм": "telegram.exe",
    "телега": "telegram.exe",
    "notepad": "notepad.exe",
    "блокнот": "notepad.exe",
    "calc": "calc.exe",
    "калькулятор": "calc.exe",
    "explorer": "explorer.exe",
    "проводник": "explorer.exe",
    "taskmgr": "taskmgr.exe",
    "диспетчер задач": "taskmgr.exe",
    "cmd": "cmd.exe",
    "терминал": "cmd.exe",
    "powershell": "powershell.exe",
    "vscode": "code.cmd",
    "вскод": "code.cmd",
    "vs code": "code.cmd",
    "код": "code.cmd",
    "browser": "https://google.com",
    "браузер": "https://google.com",
    "хром": "chrome.exe",
    "chrome": "chrome.exe",
    "фаерфокс": "firefox.exe",
    "firefox": "firefox.exe",
    "edge": "msedge.exe",
    "эдж": "msedge.exe",
}

def _find_installed_shortcut(app_name: str) -> Optional[str]:
    """Scans Desktop and Start Menu for .lnk matching the app name."""
    search_dirs = [
        os.path.expandvars(r"%USERPROFILE%\Desktop"),
        r"C:\Users\Public\Desktop",
        os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
        os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs"),
    ]
    app_lower = app_name.lower().strip()
    
    # 1. Exact match
    for d in search_dirs:
        for f in glob.glob(os.path.join(d, "**", "*.lnk"), recursive=True):
            base = os.path.splitext(os.path.basename(f))[0].lower()
            if base == app_lower:
                return f
        for f in glob.glob(os.path.join(d, "**", "*.url"), recursive=True):
            base = os.path.splitext(os.path.basename(f))[0].lower()
            if base == app_lower:
                return f

    # 2. Substring match
    for d in search_dirs:
        for f in glob.glob(os.path.join(d, "**", "*.lnk"), recursive=True):
            base = os.path.splitext(os.path.basename(f))[0].lower()
            if app_lower in base or base in app_lower:
                return f
    return None

def open_app(app_name: str) -> str:
    """
    Открыть или запустить программу/приложение на компьютере по названию.
    
    Args:
        app_name: название программы (например: 'discord', 'telegram', 'spotify', 'steam',
                  'notepad', 'calc', 'explorer', 'browser', 'chrome', 'firefox', 'vscode', 'taskmgr').
    """
    clean_name = (app_name or "").strip().lower()
    ui.print_system(f"Запуск приложения: '{clean_name}'")

    if not clean_name:
        return "Не указано имя приложения для запуска, чумба."

    # Check direct aliases
    target = APP_ALIASES.get(clean_name)
    
    # Check substring in aliases
    if not target:
        for k, v in APP_ALIASES.items():
            if k in clean_name or clean_name in k:
                target = v
                break

    # If not in aliases, look for installed shortcuts on Desktop / Start Menu
    if not target:
        shortcut = _find_installed_shortcut(clean_name)
        if shortcut:
            target = shortcut

    # Fallback to direct name as executable or protocol
    if not target:
        target = clean_name

    try:
        # Launch target
        if target.startswith("http://") or target.startswith("https://"):
            webbrowser.open(target)
            return f"Открыла браузер: {target}"
        elif target.endswith(":") or target.endswith(".lnk") or target.endswith(".url"):
            os.startfile(target)
            return f"Запустила {app_name}, чумба. Разворачивается на экране."
        else:
            try:
                os.startfile(target)
            except Exception:
                subprocess.Popen(target, shell=True)
            return f"Запустила приложение '{app_name}'."
    except Exception as e:
        # Final fallback: Windows search command
        try:
            subprocess.Popen(f"start {target}", shell=True)
            return f"Запустила '{app_name}' через командную строку."
        except Exception as e2:
            return f"Не удалось запустить '{app_name}': {e2}"

def open_website(url: str) -> str:
    """
    Открыть сайт или ссылку в браузере.
    
    Args:
        url: адрес сайта (например: 'youtube.com', 'github.com', 'reddit.com').
    """
    url = (url or "").strip()
    if not url:
        return "Не указан URL для открытия, чумба."
    
    if not (url.startswith("http://") or url.startswith("https://")):
        full_url = f"https://{url}"
    else:
        full_url = url

    ui.print_system(f"Открытие сайта: {full_url}")
    try:
        webbrowser.open(full_url)
        return f"Открыла {full_url} в браузере, чумба."
    except Exception as e:
        return f"Ошибка при открытии сайта {full_url}: {e}"

# ==============================================================================
# 3. FILE SYSTEM TOOLS (STRICTLY READ-ONLY)
# ==============================================================================

COMMON_USER_DIRS = {
    "desktop": os.path.expandvars(r"%USERPROFILE%\Desktop"),
    "documents": os.path.expandvars(r"%USERPROFILE%\Documents"),
    "downloads": os.path.expandvars(r"%USERPROFILE%\Downloads"),
    "capri": os.path.abspath(os.path.dirname(__file__)),
}

def _resolve_path(path_str: str) -> str:
    """Normalizes and safely resolves a user or system path."""
    if not path_str or path_str.strip() in [".", "", "desktop", "рабочий стол"]:
        return COMMON_USER_DIRS["desktop"]
    
    p = path_str.strip().lower()
    if p in ["documents", "документы"]:
        return COMMON_USER_DIRS["documents"]
    if p in ["downloads", "загрузки"]:
        return COMMON_USER_DIRS["downloads"]
    if p in ["project", "capri", "проект"]:
        return COMMON_USER_DIRS["capri"]

    expanded = os.path.expanduser(os.path.expandvars(path_str.strip()))
    return os.path.abspath(expanded)

def search_files(query: str, directory: str = "") -> str:
    """
    Найти файлы по названию или маске.
    Доступ СТРОГО READ-ONLY (только поиск, без изменения и удаления).
    
    Args:
        query: поисковый запрос (например: '*.py', 'отчет', 'cyberpunk', '*.png', 'music').
        directory: папка для поиска (например, 'Desktop', 'Downloads', 'Documents').
                   Если не указана, ищет на Рабочем столе и в текущем проекте.
    """
    query = (query or "*").strip()
    target_dir = _resolve_path(directory)
    ui.print_system(f"Поиск файлов: query='{query}' в '{target_dir}'")

    if not os.path.exists(target_dir):
        return f"Директория '{target_dir}' не существует, чумба."

    matches = []
    # If query has no wildcards, wrap with *
    pattern = query if ("*" in query or "?" in query) else f"*{query}*"

    try:
        # Search recursively with depth limit to stay fast
        for root, dirs, files in os.walk(target_dir):
            # Skip hidden / system folders
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["node_modules", "venv", "__pycache__", "$RECYCLE.BIN"]]
            
            for f in files:
                if glob.fnmatch.fnmatch(f.lower(), pattern.lower()):
                    full_p = os.path.join(root, f)
                    try:
                        size_kb = os.path.getsize(full_p) / 1024.0
                        matches.append((f, full_p, size_kb))
                    except Exception:
                        matches.append((f, full_p, 0))

                if len(matches) >= 20:
                    break
            if len(matches) >= 20:
                break

        if not matches:
            return f"Ничего не нашла по запросу '{query}' в папке '{target_dir}', чумба."

        lines = [f"Нашла {len(matches)} файл(ов) по запросу '{query}':"]
        for name, full_p, size_kb in matches[:15]:
            lines.append(f"- {name} ({size_kb:.1f} KB) -> {full_p}")
        if len(matches) > 15:
            lines.append(f"...и еще {len(matches) - 15} файлов.")

        return "\n".join(lines)
    except Exception as e:
        return f"Ошибка при сканировании файлов: {e}"

def list_directory(path: str = "") -> str:
    """
    Посмотреть список файлов и папок в директории.
    Доступ СТРОГО READ-ONLY (только чтение).
    
    Args:
        path: путь к папке (например: 'C:\\Users\\Admin\\Desktop' или 'Downloads').
              Если оставить пустым, показывает файлы на Рабочем столе.
    """
    target_dir = _resolve_path(path)
    ui.print_system(f"Листинг папки: '{target_dir}'")

    if not os.path.exists(target_dir):
        return f"Папка '{target_dir}' не найдена, чумба."

    try:
        entries = os.listdir(target_dir)
        dirs = []
        files = []

        for e in entries:
            full_p = os.path.join(target_dir, e)
            try:
                if os.path.isdir(full_p):
                    dirs.append(e)
                else:
                    sz_kb = os.path.getsize(full_p) / 1024.0
                    files.append((e, sz_kb))
            except Exception:
                files.append((e, 0))

        lines = [f"Содержимое папки [{target_dir}]:"]
        # Directories
        for d in sorted(dirs)[:12]:
            lines.append(f"📁 [DIR]  {d}")
        # Files
        for f, sz in sorted(files, key=lambda x: x[0])[:18]:
            lines.append(f"📄 [FILE] {f} ({sz:.1f} KB)")

        total = len(dirs) + len(files)
        if total > 30:
            lines.append(f"...всего {total} объектов (показаны первые 30).")

        return "\n".join(lines)
    except Exception as e:
        return f"Не удалось прочитать папку '{target_dir}': {e}"

def read_file_content(file_path: str, max_lines: int = 60) -> str:
    """
    Прочитать содержимое текстового файла (код, лог, заметка, документ).
    Доступ СТРОГО READ-ONLY. Не изменяет и не удаляет файлы.
    
    Args:
        file_path: путь к файлу для чтения.
        max_lines: максимальное количество строк для чтения (по умолчанию 60).
    """
    file_path = file_path.strip()
    ui.print_system(f"Чтение файла: '{file_path}'")

    if not os.path.exists(file_path):
        # Try resolving relative to Desktop or current project
        alt_path = os.path.join(COMMON_USER_DIRS["desktop"], file_path)
        if os.path.exists(alt_path):
            file_path = alt_path
        else:
            return f"Файл '{file_path}' не найден, чумба."

    if os.path.isdir(file_path):
        return f"'{file_path}' — это папка, а не файл. Используй list_directory."

    # Avoid huge files > 5MB
    try:
        size_mb = os.path.getsize(file_path) / (1024.0 * 1024.0)
        if size_mb > 5.0:
            return f"Файл слишком здоровый ({size_mb:.1f} MB), чумба. Читаю только текстовые файлы до 5 MB."
    except Exception:
        pass

    # Read with encoding fallbacks
    encodings = ["utf-8", "cp1251", "latin-1"]
    content = None
    for enc in encodings:
        try:
            with open(file_path, "r", encoding=enc) as f:
                lines = [f.readline() for _ in range(max_lines)]
                content = "".join(lines)
                break
        except UnicodeDecodeError:
            continue
        except Exception as e:
            return f"Не удалось открыть файл '{file_path}': {e}"

    if content is None:
        return f"Не удалось декодировать файл '{file_path}' как текст (возможно, это бинарник или картинка)."

    total_lines = len(content.splitlines())
    header = f"=== [READ-ONLY: {os.path.basename(file_path)}] (показано {total_lines} строк) ===\n"
    return header + content

# List of all tools available for Capri
ALL_CAPRI_TOOLS = [
    play_spotify,
    control_playback,
    open_app,
    open_website,
    search_files,
    list_directory,
    read_file_content
]
