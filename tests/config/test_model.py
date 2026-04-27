from pathlib import Path

import pytest
from pydantic import ValidationError

from config.model import Options


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
            "database_path": "~/.nature/vector-store.sqlite",
            "collection_name": "default",
        },
        "retriever": {
            "default_top_k": 8,
            "min_score": 0.0,
            "include_excerpt": True,
        },
    }


def test_valid_config_expands_vault_path(tmp_path: Path):
    config = Options.model_validate(valid_config(tmp_path))
    assert config.workspace.vault_path == tmp_path


def test_invalid_overwrite_policy_fails(tmp_path: Path):
    data = valid_config(tmp_path)
    data["wiki"]["overwrite_policy"] = "replace"

    with pytest.raises(ValidationError):
        Options.model_validate(data)
