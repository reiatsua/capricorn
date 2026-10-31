import socket

def minecraft_status_check(host: str = "localhost", port: int = 25575) -> str:
    """
    Проверяет доступность RCON сервера Minecraft для управления игрой.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        sock.connect((host, port))
        sock.close()
        return "RCON порт Майнкрафта открыт! Капри готова подключаться к миру, чумба."
    except Exception as e:
        return f"RCON порт не отвечает ({e}). Подними локальный сервер с включенным rcon (enable-rcon=true), и я ворвусь в твой мир как босс!"
