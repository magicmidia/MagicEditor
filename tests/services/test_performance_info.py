from magiceditor.services.performance_info import snapshot_for_document


def test_snapshot_lines() -> None:
    snap = snapshot_for_document(
        line_count=10,
        buffer_bytes=100,
        huge_mode=False,
        mmap_active=False,
        gpu_acceleration=True,
        portable=False,
        spell_enabled=True,
    )
    lines = snap.as_lines()
    assert any("Lines: 10" in ln for ln in lines)
    assert any("Spell: on" in ln for ln in lines)
