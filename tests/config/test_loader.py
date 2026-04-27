import json
from pathlib import Path

import pytest

from config.loader import load_config
from core.errors import InvalidConfig


def valid_config(vault: Path) -> dict:
    return {
        "schema_version": "1.0",
        "workspace": {"vault_path": str(vault)},
        "parsing": {
            "page_image_dpi": 200,
            "ocr_enabled": True,
            "ocr_engine": "paddleocr-pp-structure-v3",
            "ocr_language": "en",
            "min_native_text_chars_per_page": 80,
            "low_confidence_threshold": 0.75,
        },
        "wiki": {
            "overwrite_policy": "conflict",
            "include_generated_summary": True,
            "concept_extraction_enabled": False,
            "persist_retrieval_dataset": False,
        },
        "embedding": {
            "enabled": True,
            "model_name": "sentence-transformers/all-MiniLM-L6-v2",
            "model_revision": "",
            "device": "auto",
            "batch_size": 32,
            "normalize_embeddings": True,
            "distance_metric": "cosine",
            "normalization_version": "1",
            "max_chunk_chars": 4000,
        },
        "vector_store": {
            "database_path": str(vault / "vector-store.sqlite"),
            "collection_name": "default",
        },
        "retriever": {
            "default_top_k": 8,
            "min_score": 0.0,
            "include_excerpt": True,
        },
    }


def test_load_config_creates_missing_config_file(tmp_path: Path):
    path = tmp_path / ".nature" / "nature-config.json"

    with pytest.raises(InvalidConfig):
        load_config(path)

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["workspace"]["vault_path"] == "__SET_OBSIDIAN_VAULT_PATH__"


def test_load_config_does_not_overwrite_existing_config(tmp_path: Path):
    path = tmp_path / ".nature" / "nature-config.json"
    path.parent.mkdir()
    path.write_text(json.dumps(valid_config(tmp_path)), encoding="utf-8")

    config = load_config(path)

    assert config.workspace.vault_path == tmp_path
    assert json.loads(path.read_text(encoding="utf-8"))["workspace"]["vault_path"] == str(
        tmp_path
    )
