import json
from pathlib import Path

from pydantic import ValidationError

from config.model import Options
from core.errors import InvalidConfig

_CONFIG_PATH = Path("~/.nature/nature-config.json").expanduser()
_STATE_DIR = Path("~/.nature").expanduser()
_CACHE_DIR = _STATE_DIR / "cache"


def load_config(path: Path = _CONFIG_PATH) -> Options:
    try:
        config_path = path.expanduser()
        _ensure_config(config_path)
        raw = config_path.read_text(encoding="utf-8")
        config = Options.model_validate_json(raw)
    except (OSError, ValidationError) as error:
        raise InvalidConfig(str(error)) from error

    _STATE_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    _CACHE_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    config.vector_store.database_path.parent.mkdir(parents=True, exist_ok=True)
    return config


def _ensure_config(path: Path) -> None:
    if path.exists():
        return

    opts = {
        "schema_version": "1.0",
        "workspace": {
            "vault_path": "__SET_OBSIDIAN_VAULT_PATH__",
        },
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

    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    payload = json.dumps(opts, indent=2)
    path.write_text(payload, encoding="utf-8")
