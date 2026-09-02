"""Log severity levels (P6): matching, hierarchy, counts, navigation."""

from __future__ import annotations

from magiceditor.core.log_levels import (
    LEVELS,
    count_levels,
    line_level,
    next_line_with_level,
)


def test_common_formats_match() -> None:
    assert line_level("2026-09-01 10:00:00 ERROR disk full") == "error"
    assert line_level("2026-09-01 10:00:00,123 FATAL boom") == "error"
    assert line_level("CRITICAL: database gone") == "error"
    assert line_level("Traceback (most recent call last):") == "error"
    assert line_level("ValueError Exception raised") == "error"
    assert line_level("[WARN] low disk space") == "warn"
    assert line_level("WARNING something odd") == "warn"
    assert line_level("INFO: server started") == "info"
    assert line_level("DEBUG detail") == "debug"
    assert line_level("TRACE enter method") == "debug"


def test_case_insensitive() -> None:
    assert line_level("error occurred") == "error"
    assert line_level("info message") == "info"


def test_no_false_positives_word_boundary() -> None:
    # "information" contains "info" but not as a whole word.
    assert line_level("information processed") is None
    assert line_level("warned about X") is None
    assert line_level("Debugging session") is None
    assert line_level("errorHandler registered") is None
    assert line_level("just a plain line") is None


def test_hierarchy_highest_wins() -> None:
    assert line_level("WARN then ERROR later") == "error"
    assert line_level("INFO and DEBUG together") == "info"
    assert line_level("DEBUG plus WARN") == "warn"


def test_count_levels_synthetic_doc() -> None:
    lines = [
        "INFO boot",
        "WARN disk",
        "ERROR fail",
        "FATAL crash",  # also counts as error
        "plain line",
        "DEBUG detail",
        "INFO and ERROR mixed",  # error (highest)
    ]
    counts = count_levels(lines)
    assert counts == {"error": 3, "warn": 1, "info": 1, "debug": 1}
    assert set(counts) == set(LEVELS)


def test_next_line_with_level_and_wrap() -> None:
    lines = ["INFO a", "ERROR b", "INFO c", "WARN d", "ERROR e"]

    def text(i: int) -> str:
        return lines[i]

    # Forward from line 0 (0-based, exclusive) finds line 1.
    assert next_line_with_level(5, text, "error", 0) == 1
    # From the first error, the next one is line 4.
    assert next_line_with_level(5, text, "error", 1) == 4
    # Past the last error wraps around to line 1.
    assert next_line_with_level(5, text, "error", 4) == 1
    # Start before the document (-1) finds the first match.
    assert next_line_with_level(5, text, "warn", -1) == 3
    # Unknown level / no match / empty document.
    assert next_line_with_level(5, text, "debug", 0) is None
    assert next_line_with_level(5, text, "nope", 0) is None
    assert next_line_with_level(0, text, "error", 0) is None
