"""One running editor: hand file paths to the existing window."""

from __future__ import annotations

import os
from collections.abc import Callable

from PyQt6.QtCore import QByteArray, Qt
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtWidgets import QWidget

from magiceditor.services.instance_protocol import decode_open, encode_open

_SERVER: QLocalServer | None = None
_RECEIVER: Callable[[list[str]], None] | None = None


def server_name() -> str:
    user = os.environ.get("USERNAME") or os.environ.get("USER") or "user"
    return f"MagicEditor-{user}"


def claim_or_forward(paths: list[str], *, timeout_ms: int = 250) -> bool:
    """True if this process should stay up (primary). False if handed off."""
    name = server_name()
    sock = QLocalSocket()
    sock.connectToServer(name)
    if sock.waitForConnected(timeout_ms):
        payload = encode_open(paths)
        sock.write(QByteArray(payload))
        sock.flush()
        sock.waitForBytesWritten(timeout_ms)
        sock.disconnectFromServer()
        if sock.state() != QLocalSocket.LocalSocketState.UnconnectedState:
            sock.waitForDisconnected(timeout_ms)
        return False
    QLocalServer.removeServer(name)
    server = QLocalServer()
    if not server.listen(name):
        QLocalServer.removeServer(name)
        if not server.listen(name):
            return True
    server.newConnection.connect(_on_connection)
    global _SERVER
    _SERVER = server
    return True


def attach_receiver(callback: Callable[[list[str]], None]) -> None:
    global _RECEIVER
    _RECEIVER = callback


def raise_window(window: QWidget) -> None:
    window.show()
    window.setWindowState(window.windowState() & ~Qt.WindowState.WindowMinimized)
    window.showNormal()
    window.raise_()
    window.activateWindow()


def _on_connection() -> None:
    server = _SERVER
    if server is None:
        return
    sock = server.nextPendingConnection()
    if sock is None:
        return
    sock.setParent(server)

    def _read() -> None:
        data = bytes(sock.readAll())
        if not data:
            return
        paths = decode_open(data)
        cb = _RECEIVER
        if cb is not None:
            cb(paths)
        sock.disconnectFromServer()

    sock.readyRead.connect(_read)
    if sock.bytesAvailable() > 0:
        _read()
