"""Primary instance receives file paths from a second process (QLocalSocket)."""

from __future__ import annotations

import pytest

pytest.importorskip("PyQt6")
pytest.importorskip("pytestqt")

from PyQt6.QtCore import QByteArray
from PyQt6.QtNetwork import QLocalSocket

from magiceditor.services.instance_protocol import encode_open
from magiceditor.ui.single_instance import claim_or_forward, server_name


def test_second_connect_forwards_paths(qtbot, monkeypatch) -> None:
    monkeypatch.setenv("USERNAME", "me_si_test")
    name = server_name()
    assert name.endswith("me_si_test")
    received: list[list[str]] = []

    from magiceditor.ui import single_instance as si

    si._RECEIVER = received.append
    try:
        assert claim_or_forward([]) is True
        qtbot.wait(50)
        sock = QLocalSocket()
        sock.connectToServer(name)
        assert sock.waitForConnected(1000)
        n = sock.write(QByteArray(encode_open([r"C:\tmp\doc.txt"])))
        assert n > 0
        sock.flush()
        sock.waitForBytesWritten(1000)
        qtbot.waitUntil(lambda: bool(received), timeout=2000)
        assert received[0] == [r"C:\tmp\doc.txt"]
        assert claim_or_forward([r"C:\tmp\other.md"]) is False
    finally:
        si._RECEIVER = None
        if si._SERVER is not None:
            si._SERVER.close()
            si._SERVER = None
