# Configuration

Nature uses a user-level JSON configuration file at:

```text
~/.nature/nature-config.json
```

This file stores machine-local defaults that should not be embedded in generated vault files, such as the default Obsidian vault path, model settings, and SQLite-Vector database location.

Runtime commands may accept explicit arguments such as `document_slug` or `source_pdf`, but required environment defaults should come from this config file.

## Required Configuration

```json
{
  "schema_version": "1.0",
  "workspace": {
    "vault_path": "/absolute/path/to/obsidian-vault"
  },
  "parsing": {
    "page_image_dpi": 200,
    "ocr_enabled": true,
    "ocr_engine": "paddleocr-pp-structure-v3",
    "ocr_language": "en",
    "min_native_text_chars_per_page": 80,
    "low_confidence_threshold": 0.75
  },
  "wiki": {
    "overwrite_policy": "conflict",
    "include_generated_summary": true,
    "concept_extraction_enabled": false,
    "persist_retrieval_dataset": false
  },
  "embedding": {
    "enabled": true,
    "model_name": "sentence-transformers/all-MiniLM-L6-v2",
    "model_revision": "",
    "device": "auto",
    "batch_size": 32,
    "normalize_embeddings": true,
    "distance_metric": "cosine",
    "normalization_version": "1",
    "max_chunk_chars": 4000
  },
  "vector_store": {
    "database_path": "~/.nature/vector-store.sqlite",
    "collection_name": "default"
  },
  "retriever": {
    "default_top_k": 8,
    "min_score": 0.0,
    "include_excerpt": true
  }
}
```

## Field Rules

### `schema_version`

Required string. The Pydantic root options model should reject unsupported major versions.

### `workspace`

- `vault_path`: Required absolute path to the target Obsidian vault.

The vault path may use `~`, but must be expanded before validation. The vault path must exist and be writable before wiki runs.

Nature-owned state and cache paths are fixed and are not user-configurable:

- State directory: `~/.nature`
- Cache directory: `~/.nature/cache`

### `parsing`

- `page_image_dpi`: Required positive integer used when rendering PDF pages for OCR and layout detection.
- `ocr_enabled`: Required boolean. If false, parsing should use native PDF extraction only.
- `ocr_engine`: Required string. Initial supported value: `paddleocr-pp-structure-v3`.
- `ocr_language`: Required string language code passed to OCR when supported.
- `min_native_text_chars_per_page`: Required integer threshold for deciding whether native text extraction is sufficient.
- `low_confidence_threshold`: Required float from `0.0` to `1.0` for parser quality warnings and fallback decisions.

### `wiki`

- `overwrite_policy`: Required enum: `conflict`, `overwrite`, or `skip`.
- `include_generated_summary`: Required boolean.
- `concept_extraction_enabled`: Required boolean.
- `persist_retrieval_dataset`: Required boolean. Default should be false because the wiki-to-embedding handoff uses an in-memory Python object. This option exists only for debugging or audit runs.

### `embedding`

- `enabled`: Required boolean.
- `model_name`: Required Sentence-Transformer model name or local model path.
- `model_revision`: Required string. Use an empty string when no explicit revision is pinned.
- `device`: Required enum: `auto`, `cpu`, `cuda`, or `mps`.
- `batch_size`: Required positive integer.
- `normalize_embeddings`: Required boolean.
- `distance_metric`: Required enum: `cosine`, `dot`, or `l2`.
- `normalization_version`: Required string. Increment when chunk text normalization behavior changes.
- `max_chunk_chars`: Required positive integer. Longer retrieval records should be split deterministically before embedding.

### `vector_store`

- `database_path`: Required path to the SQLite-Vector database.
- `collection_name`: Required logical collection name for the active vault and embedding configuration.

The vector database path should usually live outside the Obsidian vault because it is machine state, not human-facing knowledge.

### `retriever`

- `default_top_k`: Required positive integer.
- `min_score`: Required float. Interpretation depends on the configured distance metric.
- `include_excerpt`: Required boolean.

## Pydantic Model Validation

Configuration loading should parse JSON into Pydantic models before any pipeline runs. Validation should live with the options models, not in a separate validation layer.

1. `~/.nature/nature-config.json` exists and parses as JSON.
2. `NatureOptions.model_validate_json(...)` validates the parsed shape.
3. Required sections and fields are enforced by Pydantic model fields.
4. Enums are represented with `Literal` or `Enum` types.
5. Numeric ranges use Pydantic field constraints.
6. Paths expand `~` in field validators.
7. `workspace.vault_path` exists, is a directory, and is writable.
8. Fixed directories `~/.nature` and `~/.nature/cache` exist or can be created.
9. `vector_store.database_path` parent directory exists or can be created.
10. Cross-field checks, such as embedding metric compatibility, use model validators.

Pydantic `ValidationError` should be wrapped in a structured `invalid-config` error at the application boundary.

Recommended model ownership:

```text
nature.config.model
├── NatureOptions
├── WorkspaceOptions
├── ParsingOptions
├── WikiOptions
├── EmbeddingOptions
├── VectorStoreOptions
└── RetrieverOptions
```

`nature.config.loader` should only read JSON, call the Pydantic model, create fixed internal directories, and return `NatureOptions`.

## Pipeline Usage

Parsing reads:

- `parsing.*`

Parsing uses the fixed cache directory `~/.nature/cache`.

Wiki reads:

- `workspace.vault_path`
- `wiki.*`

Wiki still receives `document_slug` as a command or API parameter because document slugs are source-specific, not global configuration.

Embedding reads:

- `embedding.*`
- `vector_store.*`
- `workspace.vault_path`

Embedding receives `RetrievalDataset` directly from wiki. It should not read retrieval records from disk unless `wiki.persist_retrieval_dataset` was enabled for a debug or audit workflow.

Retriever reads:

- `workspace.vault_path`
- `vector_store.*`
- `retriever.*`

## Security

The config file should not store API keys or credentials. If future providers require secrets, store them in environment variables or an OS keychain and reference only the secret name in this file.

The application should create `~/.nature` with user-only permissions when possible.

## Minimal Bootstrap

The application should provide an initialization command that writes a config template:

```text
nature init --vault /absolute/path/to/obsidian-vault
```

The command should:

1. Create `~/.nature/`.
2. Create `~/.nature/cache/`.
3. Write `~/.nature/nature-config.json` if it does not already exist.
4. Validate the configured vault path.
5. Refuse to overwrite an existing config unless an explicit overwrite flag is provided.
