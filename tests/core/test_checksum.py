"""Tests for core.checksum — streaming file hashing."""

from __future__ import annotations

import hashlib

import pytest

from magiceditor.core.checksum import DEFAULT_ALGORITHMS, bytes_hashes, file_hashes

CONTENT = b"hello world"
EXPECTED_MD5 = hashlib.md5(CONTENT).hexdigest()
EXPECTED_SHA1 = hashlib.sha1(CONTENT).hexdigest()
EXPECTED_SHA256 = hashlib.sha256(CONTENT).hexdigest()


def test_file_hashes_known_content(tmp_path):
    f = tmp_path / "known.bin"
    f.write_bytes(CONTENT)
    result = file_hashes(f)
    assert set(result) == set(DEFAULT_ALGORITHMS)
    for name in DEFAULT_ALGORITHMS:
        assert result[name] == hashlib.new(name, CONTENT).hexdigest()


def test_file_hashes_small_chunks_match_single_pass(tmp_path):
    f = tmp_path / "chunked.bin"
    f.write_bytes(CONTENT * 100)
    chunked = file_hashes(f, chunk_size=4)
    single = file_hashes(f, chunk_size=1024 * 1024)
    assert chunked == single
    assert chunked["sha256"] == hashlib.sha256(CONTENT * 100).hexdigest()


def test_file_hashes_subset_of_algorithms(tmp_path):
    f = tmp_path / "sub.bin"
    f.write_bytes(CONTENT)
    result = file_hashes(f, algorithms=("sha256",))
    assert result == {"sha256": EXPECTED_SHA256}


def test_file_hashes_missing_file_raises_oserror(tmp_path):
    with pytest.raises(OSError):
        file_hashes(tmp_path / "does_not_exist.bin")


def test_file_hashes_invalid_algorithm_raises(tmp_path):
    f = tmp_path / "x.bin"
    f.write_bytes(CONTENT)
    with pytest.raises(ValueError, match="bogus"):
        file_hashes(f, algorithms=("md5", "bogus-algo"))


def test_file_hashes_invalid_chunk_size_raises(tmp_path):
    f = tmp_path / "x.bin"
    f.write_bytes(CONTENT)
    with pytest.raises(ValueError, match="chunk_size"):
        file_hashes(f, chunk_size=0)


def test_bytes_hashes_known_content():
    result = bytes_hashes(CONTENT)
    assert set(result) == set(DEFAULT_ALGORITHMS)
    for name in DEFAULT_ALGORITHMS:
        assert result[name] == hashlib.new(name, CONTENT).hexdigest()


def test_bytes_hashes_invalid_algorithm_raises():
    with pytest.raises(ValueError, match="bogus"):
        bytes_hashes(CONTENT, algorithms=("bogus-algo",))
