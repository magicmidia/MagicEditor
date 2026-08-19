"""Central application log — repo-root ``MagicEditor.log``.

Captures logging (warning+), warnings, uncaught exceptions, native faults,
and Qt messages. Windowed EXE has no console; this file is the only trace.
"""

from __future__ import annotations

import logging
import sys
import threading
import warnings
from pathlib import Path
from typing import TextIO

from magiceditor.paths import is_frozen, log_file_path, user_data_dir

LOG_FILENAME = "MagicEditor.log"
_MAX_BYTES = 2_000_000
_FMT = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

_installed = False
_log_path: Path | None = None
_fault_fp: TextIO | None = None
_stdio_fp: TextIO | None = None
_qt_handler_ref: object | None = None


def current_log_path() -> Path:
    """Path currently in use, or the default location."""
    return _log_path if _log_path is not None else log_file_path()


def setup_logging(path: Path | None = None) -> Path:
    """Install file logging. Idempotent for the same destination.

    Never raises if the preferred path is not writable (installed under
    ``Program Files``). Falls back to the user data dir, then hooks only.
    """
    global _installed, _log_path

    preferred = Path(path) if path is not None else log_file_path()
    dest = _pick_writable_log(preferred)
    if dest is None:
        dest = preferred
        if not _installed:
            _install_hooks()
            _installed = True
            _log_path = dest
        return dest

    if _installed and _log_path is not None:
        try:
            if dest.resolve() == _log_path.resolve():
                return dest
        except OSError:
            return dest

    try:
        _attach_file_handler(dest)
    except OSError:
        dest = preferred
        if not _installed:
            _install_hooks()
            _installed = True
            _log_path = dest
        return dest

    _install_hooks()
    _enable_faulthandler(dest)
    if is_frozen():
        _redirect_stdio(dest)

    _installed = True
    _log_path = dest
    logging.getLogger("magiceditor").info("Logging started -> %s", dest)
    return dest


def _pick_writable_log(preferred: Path) -> Path | None:
    fallback = user_data_dir() / LOG_FILENAME
    candidates = [preferred]
    if fallback != preferred:
        candidates.append(fallback)
    for cand in candidates:
        try:
            cand.parent.mkdir(parents=True, exist_ok=True)
            _rotate_if_needed(cand)
            with cand.open("a", encoding="utf-8"):
                pass
            return cand
        except OSError:
            continue
    return None


def _install_hooks() -> None:
    logging.captureWarnings(True)
    warnings.simplefilter("default")
    sys.excepthook = _excepthook
    if hasattr(threading, "excepthook"):
        threading.excepthook = _thread_excepthook
    if hasattr(sys, "unraisablehook"):
        sys.unraisablehook = _unraisable_hook
    _install_qt_handler()


def _rotate_if_needed(dest: Path) -> None:
    try:
        if dest.is_file() and dest.stat().st_size >= _MAX_BYTES:
            bak = dest.with_suffix(".log.1")
            if bak.exists():
                bak.unlink()
            dest.replace(bak)
    except OSError:
        pass


def _attach_file_handler(dest: Path) -> None:
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    resolved = dest.resolve()
    for handler in list(root.handlers):
        if isinstance(handler, logging.FileHandler):
            try:
                if Path(handler.baseFilename).resolve() == resolved:
                    root.removeHandler(handler)
                    handler.close()
            except OSError:
                pass
    fh = logging.FileHandler(dest, encoding="utf-8")
    fh.setLevel(logging.WARNING if is_frozen() else logging.DEBUG)
    fh.setFormatter(_FMT)
    root.addHandler(fh)
    if is_frozen():
        root.setLevel(logging.WARNING)


def _enable_faulthandler(dest: Path) -> None:
    global _fault_fp
    try:
        import faulthandler
    except ImportError:
        return
    try:
        if _fault_fp is not None:
            _fault_fp.close()
        _fault_fp = dest.open("a", encoding="utf-8", errors="replace")
        faulthandler.enable(file=_fault_fp, all_threads=True)
    except OSError:
        _fault_fp = None


def _redirect_stdio(dest: Path) -> None:
    """Windowed PyInstaller EXE: ``sys.stderr`` is None — send it to the log."""
    global _stdio_fp
    try:
        _stdio_fp = dest.open("a", encoding="utf-8", errors="replace")
    except OSError:
        return
    if sys.stdout is None or not getattr(sys.stdout, "isatty", lambda: False)():
        sys.stdout = _stdio_fp
    if sys.stderr is None or not getattr(sys.stderr, "isatty", lambda: False)():
        sys.stderr = _stdio_fp


def _install_qt_handler() -> None:
    global _qt_handler_ref
    try:
        from PyQt6.QtCore import QtMsgType, qInstallMessageHandler
    except Exception:
        return

    levels = {
        QtMsgType.QtDebugMsg: logging.DEBUG,
        QtMsgType.QtInfoMsg: logging.INFO,
        QtMsgType.QtWarningMsg: logging.WARNING,
        QtMsgType.QtCriticalMsg: logging.ERROR,
        QtMsgType.QtFatalMsg: logging.CRITICAL,
    }
    log = logging.getLogger("qt")

    def _qt_message(mode: object, _ctx: object, message: str) -> None:
        log.log(levels.get(mode, logging.WARNING), "%s", message)  # type: ignore[arg-type]

    _qt_handler_ref = _qt_message
    qInstallMessageHandler(_qt_message)


def _excepthook(exc_type: type[BaseException], exc: BaseException, tb: object) -> None:
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc, tb)
        return
    logging.getLogger("magiceditor").error(
        "Uncaught exception",
        exc_info=(exc_type, exc, tb),  # type: ignore[arg-type]
    )


def _thread_excepthook(args: threading.ExceptHookArgs) -> None:
    if args.exc_type is not None and issubclass(args.exc_type, KeyboardInterrupt):
        return
    logging.getLogger("magiceditor").error(
        "Uncaught thread exception in %s",
        args.thread.name if args.thread else "?",
        exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
    )


def _unraisable_hook(unraisable: object) -> None:
    exc = getattr(unraisable, "exc_value", None)
    logging.getLogger("magiceditor").error(
        "Unraisable exception: %s",
        getattr(unraisable, "err_msg", None) or exc,
        exc_info=exc if isinstance(exc, BaseException) else None,
    )
