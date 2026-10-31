"""Read chat messages from the local Minecraft client's log."""

import os
import re
from pathlib import Path


_CHAT_PATTERN = re.compile(r"\[CHAT\]\s*(?:\[[^]]+\]\s*)?<([^>]+)>\s*(.*)$")
_LEGACY_CHAT_PATTERN = re.compile(r"\[CHAT\]\s*([^:]+):\s*(.*)$")


def _find_minecraft_log() -> Path | None:
    configured = os.environ.get("MINECRAFT_LOG_PATH")
    candidates = [Path(configured)] if configured else []
    appdata = os.environ.get("APPDATA")
    if appdata:
        candidates.extend([
            Path(appdata) / ".tlauncher" / "legacy" / "Minecraft" / "game" / "logs" / "latest.log",
            Path(appdata) / ".minecraft" / "logs" / "latest.log",
        ])
    return next((path for path in candidates if path.is_file()), None)


def read_custom_minecraft_chat(max_messages: int = 20) -> str:
    """Read recent player chat messages from the Minecraft client log."""
    log_path = _find_minecraft_log()
    if log_path is None:
        return "Лог Minecraft не найден. Проверьте MINECRAFT_LOG_PATH или запустите игру."
    try:
        # Read only a tail of the log so a long session does not consume excess memory.
        with log_path.open("rb") as log_file:
            log_file.seek(0, os.SEEK_END)
            size = log_file.tell()
            log_file.seek(max(0, size - 256 * 1024))
            lines = log_file.read().decode("utf-8", errors="replace").splitlines()

        messages = []
        for line in lines:
            modern = _CHAT_PATTERN.search(line)
            legacy = _LEGACY_CHAT_PATTERN.search(line)
            match = modern or legacy
            if match:
                player, message = (part.strip() for part in match.groups())
                if player and message:
                    messages.append(f"{player}: {message}")
        if not messages:
            return "В логе пока нет сообщений чата."
        return "\n".join(messages[-max(1, min(int(max_messages), 100)):])
    except (OSError, ValueError) as exc:
        return f"Не удалось прочитать лог Minecraft: {exc}"


TOOLS = [read_custom_minecraft_chat]
