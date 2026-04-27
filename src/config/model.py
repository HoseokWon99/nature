from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WorkspaceOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vault_path: Path

    @field_validator("vault_path")
    @classmethod
    def validate_vault_path(cls, value: Path) -> Path:
        path = value.expanduser()
        if not path.exists() or not path.is_dir():
            raise ValueError("vault_path must exist and be a directory")
        return path


class ParsingOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page_image_dpi: int = Field(gt=0)
    ocr_enabled: bool
    ocr_engine: Literal["paddleocr-pp-structure-v3"]
    ocr_language: str = Field(min_length=1)
    min_native_text_chars_per_page: int = Field(ge=0)
    low_confidence_threshold: float = Field(ge=0.0, le=1.0)


class WikiOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overwrite_policy: Literal["conflict", "overwrite", "skip"]
    include_generated_summary: bool
    concept_extraction_enabled: bool
    persist_retrieval_dataset: bool


class EmbeddingOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool
    model_name: str = Field(min_length=1)
    model_revision: str
    device: Literal["auto", "cpu", "cuda", "mps"]
    batch_size: int = Field(gt=0)
    normalize_embeddings: bool
    distance_metric: Literal["cosine", "dot", "l2"]
    normalization_version: str = Field(min_length=1)
    max_chunk_chars: int = Field(gt=0)


class VectorStoreOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")
    database_path: Path
    collection_name: str = Field(min_length=1)

    @field_validator("database_path")
    @classmethod
    def expand_database_path(cls, value: Path) -> Path:
        return value.expanduser()


class RetrieverOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    default_top_k: int = Field(gt=0)
    min_score: float
    include_excerpt: bool


class Options(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"]
    workspace: WorkspaceOptions
    parsing: ParsingOptions
    wiki: WikiOptions
    embedding: EmbeddingOptions
    vector_store: VectorStoreOptions
    retriever: RetrieverOptions
