from pathlib import Path

from magiceditor.core.document import Document
from magiceditor.services.session_state import SessionState
from magiceditor.ui.window_files import (
    apply_save_prefs_to_document,
    index_of_open_path,
    resolve_open_target,
    same_open_path,
)
from magiceditor.ui.window_session import (
    DRAFT_TEXT_CAP,
    RESTORE_FILE_CAP,
    TabSessionView,
    collect_tabs_into_session,
    plan_session_restore,
    session_files_to_open,
)
from magiceditor.ui.workspace_actions import copy_path_text, reveal_folder


def test_collect_tabs_into_session_files_and_drafts(tmp_path: Path) -> None:
    saved = tmp_path / "saved.txt"
    saved.write_text("ok", encoding="utf-8")
    views = [
        TabSessionView(
            path=saved,
            path_is_file=True,
            title="saved.txt",
            text="ok",
            modified=False,
            bookmarks=[2],
            cursor=(3, 1),
            is_current=False,
        ),
        TabSessionView(
            path=None,
            path_is_file=False,
            title="Untitled-1",
            text="draft body",
            modified=True,
            bookmarks=[],
            cursor=(1, 1),
            is_current=True,
        ),
    ]
    base = SessionState(theme="nord", recent_files=["old"], font_size=14)
    out = collect_tabs_into_session(
        views,
        base,
        workspace=None,
        theme="darcula",
        language="en_US",
        word_wrap=True,
        line_numbers=False,
        icon_pack="material",
    )
    assert out.open_files and out.open_files[0].endswith("saved.txt")
    assert out.bookmarks[out.open_files[0]] == [2]
    assert out.cursors[out.open_files[0]] == (3, 1)
    assert out.active_file is None
    assert out.drafts[0]["title"] == "Untitled-1"
    assert out.drafts[0]["active"] is True
    assert out.theme == "darcula"
    assert out.recent_files == ["old"]
    assert out.font_size == 14
    assert DRAFT_TEXT_CAP >= 400_000


def test_collect_dirty_file_stores_path_draft(tmp_path: Path) -> None:
    clean = tmp_path / "saved.txt"
    dirty = tmp_path / "dirty.txt"
    clean.write_text("ok", encoding="utf-8")
    dirty.write_text("disk", encoding="utf-8")
    views = [
        TabSessionView(
            path=clean,
            path_is_file=True,
            title="saved.txt",
            text="ok",
            modified=False,
            bookmarks=[],
            cursor=(1, 1),
            is_current=False,
        ),
        TabSessionView(
            path=dirty,
            path_is_file=True,
            title="dirty.txt",
            text="",
            modified=True,
            bookmarks=[1],
            cursor=(2, 1),
            is_current=True,
        ),
    ]
    out = collect_tabs_into_session(
        views,
        SessionState(),
        workspace=None,
        theme="nord",
        language="pt_BR",
        word_wrap=False,
        line_numbers=True,
        icon_pack="qlementine",
    )
    assert len(out.drafts) == 1
    assert out.drafts[0]["text"] == ""
    assert out.drafts[0]["path"].endswith("dirty.txt")
    assert out.drafts[0]["active"] is True
    assert any(p.endswith("saved.txt") for p in out.open_files)


def test_plan_recovery_text_and_missing_file_becomes_draft(tmp_path: Path) -> None:
    existing = tmp_path / "keep.txt"
    existing.write_text("disk", encoding="utf-8")
    gone = tmp_path / "gone.txt"
    orphan = tmp_path / "extra.txt"
    orphan.write_text("x", encoding="utf-8")
    session = SessionState(
        open_files=[str(existing), str(gone)],
        active_file=str(existing),
        drafts=[
            {"title": "keep.txt", "text": "recovered", "path": str(existing)},
            {"title": "gone.txt", "text": "orphan text", "path": str(gone), "active": True},
            {"title": "extra.txt", "text": "buf", "path": str(orphan)},
        ],
    )
    files, drafts = plan_session_restore(session)
    by_name = {op.path.name: op for op in files}
    assert by_name["keep.txt"].recovery_text == "recovered"
    assert by_name["keep.txt"].activate is True
    assert by_name["extra.txt"].recovery_text == "buf"
    assert "gone.txt" not in by_name
    assert drafts[0].title == "gone.txt"
    assert drafts[0].text == "orphan text"
    assert drafts[0].modified is True


def test_plan_session_restore_files_and_active_draft(tmp_path: Path) -> None:
    existing = tmp_path / "keep.txt"
    existing.write_text("x", encoding="utf-8")
    session = SessionState(
        open_files=[str(existing), str(tmp_path / "gone.txt")],
        active_file=str(existing),
        bookmarks={str(existing): [4]},
        cursors={str(existing): (2, 5)},
        drafts=[{"title": "Scratch", "text": "hi", "active": True, "cursor": [1, 2]}],
    )
    files, drafts = plan_session_restore(session)
    assert len(files) == 1
    assert files[0].path == existing
    assert files[0].bookmarks == [4]
    assert files[0].cursor == (2, 5)
    assert files[0].activate is True
    assert drafts[0].title == "Scratch"
    assert drafts[0].text == "hi"
    assert drafts[0].modified is True
    assert drafts[0].activate is True
    assert drafts[0].cursor == (1, 2)


def test_session_files_to_open_caps_and_skips_missing(tmp_path: Path) -> None:
    existing = tmp_path / "a.txt"
    existing.write_text("x", encoding="utf-8")
    missing = tmp_path / "gone.txt"
    paths = [str(existing)] + [str(missing)] * (RESTORE_FILE_CAP + 5)
    got = session_files_to_open(paths, cap=RESTORE_FILE_CAP)
    assert got == [existing]


def test_index_of_open_path_reuses_same_file(tmp_path: Path) -> None:
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("1", encoding="utf-8")
    b.write_text("2", encoding="utf-8")
    assert same_open_path(a, Path(str(a)))
    assert index_of_open_path([None, a, b], b) == 2
    assert index_of_open_path([a], tmp_path / "missing.txt") is None


def test_apply_save_prefs_to_document_rewrites_buffer() -> None:
    doc = Document.from_text("ab  \ncd  ")
    assert apply_save_prefs_to_document(doc, trim=True, final_nl=True) is True
    assert doc.text() == "ab\ncd\n"
    assert doc.modified is True
    assert apply_save_prefs_to_document(doc, trim=True, final_nl=True) is False


def test_apply_save_prefs_huge_does_not_truncate() -> None:
    """Huge save prefs must not rebuild from the 2 MB capped text()."""
    from magiceditor.core.piece_table import PieceTable
    from magiceditor.core.syntax_limits import FULL_TEXT_MAX_BYTES

    prefix = b"a" * (FULL_TEXT_MAX_BYTES + 64)
    raw = prefix + b"\nTAIL  "
    doc = Document(buffer=PieceTable(raw), huge_mode=True)
    assert apply_save_prefs_to_document(doc, trim=True, final_nl=True) is True
    out = doc.buffer.get_text(0, len(doc.buffer))
    assert len(out) > FULL_TEXT_MAX_BYTES
    assert out.startswith(b"aaa")
    assert out.endswith(b"\nTAIL\n")
    assert b"TAIL  " not in out


def test_resolve_open_target_dir_vs_file(tmp_path: Path) -> None:
    f = tmp_path / "f.txt"
    f.write_text("1", encoding="utf-8")
    kind, path = resolve_open_target(tmp_path)
    assert kind == "workspace"
    assert path == tmp_path
    kind, path = resolve_open_target(f)
    assert kind == "file"
    assert path == f


def test_workspace_actions_paths(tmp_path: Path) -> None:
    f = tmp_path / "n.txt"
    f.write_text("z", encoding="utf-8")
    assert copy_path_text(f).endswith("n.txt")
    assert reveal_folder(f) == tmp_path
    assert reveal_folder(None) is None
