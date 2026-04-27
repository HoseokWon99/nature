from pathlib import Path

from core.hashing import sha256_file, sha256_text


def test_sha256_text_is_stable():
    assert sha256_text("nature") == sha256_text("nature")
    assert sha256_text("nature") != sha256_text("Nature")


def test_sha256_file_is_stable(tmp_path: Path):
    path = tmp_path / "sample.pdf"
    path.write_bytes(b"%PDF-1.7\nsample")

    assert sha256_file(path) == sha256_file(path)
