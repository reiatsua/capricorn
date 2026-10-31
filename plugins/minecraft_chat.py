"""Send messages to a Minecraft server with RCON."""

import os
import socket
import struct


def _recv_exact(sock: socket.socket, size: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < size:
        chunk = sock.recv(size - len(chunks))
        if not chunk:
            raise ConnectionError("Сервер закрыл соединение RCON")
        chunks.extend(chunk)
    return bytes(chunks)


def _send_packet(sock: socket.socket, request_id: int, packet_type: int, payload: str):
    body = struct.pack("<ii", request_id, packet_type) + payload.encode("utf-8") + b"\x00\x00"
    sock.sendall(struct.pack("<i", len(body)) + body)
    packet_length = struct.unpack("<i", _recv_exact(sock, 4))[0]
    if packet_length < 10 or packet_length > 4 * 1024 * 1024:
        raise ValueError("Некорректный ответ RCON")
    packet = _recv_exact(sock, packet_length)
    response_id, response_type = struct.unpack("<ii", packet[:8])
    response = packet[8:-2].decode("utf-8", errors="replace")
    return response_id, response_type, response


def send_minecraft_chat(message: str) -> str:
    """Send a message to the Minecraft server chat using configured RCON access."""
    host = os.environ.get("MINECRAFT_RCON_HOST", "127.0.0.1")
    try:
        port = int(os.environ.get("MINECRAFT_RCON_PORT", "25575"))
    except ValueError:
        return "Некорректный MINECRAFT_RCON_PORT. Укажите число, например 25575."
    password = os.environ.get("MINECRAFT_RCON_PASSWORD", "")
    if not password:
        return "Не задан MINECRAFT_RCON_PASSWORD. Включите RCON на сервере и укажите пароль в .env."

    clean_message = " ".join(str(message).replace("\x00", "").split())
    if not clean_message:
        return "Сообщение пустое."
    # Keep the command safely below Minecraft's command length limit.
    clean_message = clean_message[:240]
    try:
        with socket.create_connection((host, port), timeout=4) as sock:
            sock.settimeout(4)
            auth_id = 1
            auth_response_id, _, _ = _send_packet(sock, auth_id, 3, password)
            if auth_response_id == -1:
                return "RCON отклонил пароль. Проверьте MINECRAFT_RCON_PASSWORD."
            if auth_response_id != auth_id:
                return "Не удалось подтвердить авторизацию RCON. Проверьте настройки сервера."

            command_id = 2
            response_id, _, _ = _send_packet(sock, command_id, 2, f"say [CAPRI]: {clean_message}")
            if response_id != command_id:
                return "RCON не подтвердил отправку сообщения."
        return "Сообщение CAPRI отправлено в чат Minecraft."
    except (OSError, ValueError, ConnectionError, struct.error) as exc:
        return f"Не удалось отправить сообщение через RCON: {exc}"


TOOLS = [send_minecraft_chat]
