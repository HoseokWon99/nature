# Parsing Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first working parsing pipeline that ingests a PDF and emits a validated `ParsedDocument` object for the wiki pipeline.

**Architecture:** Implement parsing as `nature.parsing`, isolated from vault/wiki/embedding concerns. Start with deterministic native PDF extraction and quality reporting, then add extension seams for OCR, layout, equations, tables, figures, and references without forcing those advanced recognizers into the first milestone.

**Tech Stack:** Python 3.13, Pydantic v2, PyMuPDF (`pymupdf`) for initial native PDF extraction/rendering, pytest.

---

## File Structure

Create or modify these files:

- Create: `src/nature/__init__.py` - package marker and version export.
- Create: `src/nature/core/errors.py` - structured project exceptions.
- Create: `src/nature/core/hashing.py` - file and text fingerprint helpers.
- Create: `src/nature/core/paths.py` - safe path expansion and fixed Nature paths.
- Create: `src/nature/config/model.py` - Pydantic options models.
- Create: `src/nature/config/loader.py` - load `~/.nature/nature-config.json`.
- Create: `src/nature/parsing/model.py` - parsed document Pydantic models.
- Create: `src/nature/parsing/ingest.py` - source PDF validation and fingerprinting.
- Create: `src/nature/parsing/native.py` - native PDF text extraction.
- Create: `src/nature/parsing/rendering.py` - page rendering interface.
- Create: `src/nature/parsing/sections.py` - native text to section model.
- Create: `src/nature/parsing/quality.py` - confidence and warning generation.
- Create: `src/nature/parsing/pipeline.py` - public parsing orchestration.
- Create: `src/nature/parsing/__init__.py` - parsing exports.
- Modify: `src/main.py` - keep a compatibility shim or remove after CLI exists.
- Create tests mirroring the package under `tests/core/`, `tests/config/`, and `tests/parsing/`.

## Dependency Notes

Add runtime dependencies:

```bash
uv add pydantic pymupdf
```

Add dev dependency if pytest is not already available:

```bash
uv add --dev pytest
```

## Task 1: Core Errors And Hashing

**Files:**
- Create: `src/nature/core/errors.py`
- Create: `src/nature/core/hashing.py`
- Create: `src/nature/core/__init__.py`
- Test: `tests/core/test_hashing.py`

- [ ] **Step 1: Write hashing tests**

```python
from pathlib import Path

from nature.core.hashing import sha256_file, sha256_text


def test_sha256_text_is_stable():
    assert sha256_text("nature") == sha256_text("nature")
    assert sha256_text("nature") != sha256_text("Nature")


def test_sha256_file_is_stable(tmp_path: Path):
    path = tmp_path / "sample.pdf"
    path.write_bytes(b"%PDF-1.7\nsample")

    assert sha256_file(path) == sha256_file(path)
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
pytest tests/core/test_hashing.py -v
```

Expected: import failure because `nature.core.hashing` does not exist.

- [ ] **Step 3: Implement core modules**

```python
# src/nature/core/errors.py
class NatureError(Exception):
    """Base error for structured application failures."""


class InvalidInput(NatureError):
    """Input data is missing, malformed, or unsupported."""


class InvalidConfig(NatureError):
    """Configuration is missing or invalid."""


class UnsafePath(NatureError):
    """A path escapes an allowed boundary."""
```

```python
# src/nature/core/hashing.py
from hashlib import sha256
from pathlib import Path


def sha256_text(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
```

```python
# src/nature/core/__init__.py
from nature.core.errors import InvalidConfig, InvalidInput, NatureError, UnsafePath
from nature.core.hashing import sha256_file, sha256_text

__all__ = [
    "InvalidConfig",
    "InvalidInput",
    "NatureError",
    "UnsafePath",
    "sha256_file",
    "sha256_text",
]
```

- [ ] **Step 4: Run tests and verify pass**

```bash
pytest tests/core/test_hashing.py -v
```

Expected: 2 passed.

## Task 2: Config Models With Pydantic Validation

**Files:**
- Create: `src/nature/config/model.py`
- Create: `src/nature/config/loader.py`
- Create: `src/nature/config/__init__.py`
- Test: `tests/config/test_model.py`

- [ ] **Step 1: Write config validation tests**

```python
from pathlib import Path

import pytest
from pydantic import ValidationError

from nature.config.model import NatureOptions


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
    config = NatureOptions.model_validate(valid_config(tmp_path))
    assert config.workspace.vault_path == tmp_path


def test_invalid_overwrite_policy_fails(tmp_path: Path):
    data = valid_config(tmp_path)
    data["wiki"]["overwrite_policy"] = "replace"

    with pytest.raises(ValidationError):
        NatureOptions.model_validate(data)
```

- [ ] **Step 2: Run tests and verify failure**

```bash
pytest tests/config/test_model.py -v
```

Expected: import failure because `nature.config.model` does not exist.

- [ ] **Step 3: Implement Pydantic options models**

```python
# src/nature/config/model.py
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


class NatureOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"]
    workspace: WorkspaceOptions
    parsing: ParsingOptions
    wiki: WikiOptions
    embedding: EmbeddingOptions
    vector_store: VectorStoreOptions
    retriever: RetrieverOptions
```

```python
# src/nature/config/loader.py
from pathlib import Path

from pydantic import ValidationError

from nature.config.model import NatureOptions
from nature.core.errors import InvalidConfig

CONFIG_PATH = Path("~/.nature/nature-config.json").expanduser()
STATE_DIR = Path("~/.nature").expanduser()
CACHE_DIR = STATE_DIR / "cache"


def load_config(path: Path = CONFIG_PATH) -> NatureOptions:
    try:
        raw = path.expanduser().read_text(encoding="utf-8")
        config = NatureOptions.model_validate_json(raw)
    except (OSError, ValidationError) as error:
        raise InvalidConfig(str(error)) from error

    STATE_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    CACHE_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    config.vector_store.database_path.parent.mkdir(parents=True, exist_ok=True)
    return config
```

```python
# src/nature/config/__init__.py
from nature.config.loader import CACHE_DIR, CONFIG_PATH, STATE_DIR, load_config
from nature.config.model import NatureOptions

__all__ = ["CACHE_DIR", "CONFIG_PATH", "STATE_DIR", "NatureOptions", "load_config"]
```

- [ ] **Step 4: Run tests and verify pass**

```bash
pytest tests/config/test_model.py -v
```

Expected: 2 passed.

## Task 3: Parsed Document Models

**Files:**
- Create: `src/nature/parsing/model.py`
- Create: `src/nature/parsing/__init__.py`
- Test: `tests/parsing/test_model.py`

- [ ] **Step 1: Write parsed model tests**

```python
from nature.parsing.model import (
    DocumentMetadata,
    PageSpan,
    ParsedDocument,
    QualityReport,
    Section,
)


def test_parsed_document_minimal_shape():
    document = ParsedDocument(
        id="sha256:abc",
        document_slug="paper-one",
        kind="paper",
        source_path="/tmp/source.pdf",
        fingerprint="abc",
        metadata=DocumentMetadata(title="Paper", page_count=1),
        sections=[
            Section(
                id="sec-001",
                title="Document",
                level=1,
                order=1,
                page_span=PageSpan(start=1, end=1),
                markdown="Hello",
            )
        ],
        quality=QualityReport(overall_confidence=1.0),
    )

    assert document.sections[0].id == "sec-001"
    assert document.quality.overall_confidence == 1.0
```

- [ ] **Step 2: Run tests and verify failure**

```bash
pytest tests/parsing/test_model.py -v
```

Expected: import failure because `nature.parsing.model` does not exist.

- [ ] **Step 3: Implement parsed models**

```python
# src/nature/parsing/model.py
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class PageSpan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start: int = Field(ge=1)
    end: int = Field(ge=1)


class SourceRegion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page: int = Field(ge=1)
    bbox: tuple[float, float, float, float]
    extraction_method: str


class DocumentMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = ""
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    venue: str = ""
    doi: str = ""
    arxiv_id: str = ""
    language: str = "en"
    page_count: int = Field(ge=0)


class Section(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    level: int = Field(ge=1)
    order: int = Field(ge=1)
    page_span: PageSpan
    markdown: str
    equation_ids: list[str] = Field(default_factory=list)
    table_ids: list[str] = Field(default_factory=list)
    figure_ids: list[str] = Field(default_factory=list)
    reference_ids: list[str] = Field(default_factory=list)


class Equation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str = ""
    latex: str
    section_id: str
    source: SourceRegion
    confidence: float = Field(ge=0.0, le=1.0)
    meaning: str = ""


class TableCell(BaseModel):
    model_config = ConfigDict(extra="forbid")

    row: int = Field(ge=0)
    column: int = Field(ge=0)
    value: str
    row_span: int = Field(default=1, ge=1)
    column_span: int = Field(default=1, ge=1)


class Table(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str = ""
    caption: str = ""
    section_id: str
    columns: list[str] = Field(default_factory=list)
    cells: list[TableCell] = Field(default_factory=list)
    source: SourceRegion
    confidence: float = Field(ge=0.0, le=1.0)
    warnings: list[str] = Field(default_factory=list)


class Figure(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str = ""
    caption: str = ""
    section_id: str
    image_path: Path
    source: SourceRegion
    confidence: float = Field(ge=0.0, le=1.0)
    mention_section_ids: list[str] = Field(default_factory=list)


class Reference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    raw_text: str
    title: str = ""
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    doi: str = ""
    url: str = ""


class QualityWarning(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    target_id: str = ""
    severity: str = "warning"


class QualityReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overall_confidence: float = Field(ge=0.0, le=1.0)
    warnings: list[QualityWarning] = Field(default_factory=list)


class ParsedDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    document_slug: str
    kind: str
    source_path: Path
    fingerprint: str
    metadata: DocumentMetadata
    sections: list[Section] = Field(default_factory=list)
    equations: list[Equation] = Field(default_factory=list)
    tables: list[Table] = Field(default_factory=list)
    figures: list[Figure] = Field(default_factory=list)
    references: list[Reference] = Field(default_factory=list)
    quality: QualityReport
```

```python
# src/nature/parsing/__init__.py
from nature.parsing.model import ParsedDocument

__all__ = ["ParsedDocument"]
```

- [ ] **Step 4: Run tests and verify pass**

```bash
pytest tests/parsing/test_model.py -v
```

Expected: 1 passed.

## Task 4: PDF Ingest

**Files:**
- Create: `src/nature/parsing/ingest.py`
- Test: `tests/parsing/test_ingest.py`

- [ ] **Step 1: Write ingest tests**

```python
from pathlib import Path

import pytest

from nature.core.errors import InvalidInput
from nature.parsing.ingest import ingest_pdf


def test_ingest_pdf_returns_fingerprint(tmp_path: Path):
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.7\nsample")

    result = ingest_pdf(pdf)

    assert result.path == pdf
    assert result.fingerprint
    assert result.document_id.startswith("sha256:")


def test_ingest_rejects_non_pdf_suffix(tmp_path: Path):
    text = tmp_path / "paper.txt"
    text.write_text("not a pdf")

    with pytest.raises(InvalidInput):
        ingest_pdf(text)
```

- [ ] **Step 2: Run tests and verify failure**

```bash
pytest tests/parsing/test_ingest.py -v
```

Expected: import failure because `nature.parsing.ingest` does not exist.

- [ ] **Step 3: Implement ingest**

```python
# src/nature/parsing/ingest.py
from dataclasses import dataclass
from pathlib import Path

from nature.core.errors import InvalidInput
from nature.core.hashing import sha256_file


@dataclass(frozen=True)
class IngestedPdf:
    path: Path
    fingerprint: str
    document_id: str


def ingest_pdf(path: Path) -> IngestedPdf:
    source = path.expanduser()
    if not source.exists() or not source.is_file():
        raise InvalidInput(f"PDF does not exist: {source}")
    if source.suffix.lower() != ".pdf":
        raise InvalidInput(f"Expected .pdf file: {source}")

    fingerprint = sha256_file(source)
    return IngestedPdf(
        path=source,
        fingerprint=fingerprint,
        document_id=f"sha256:{fingerprint}",
    )
```

- [ ] **Step 4: Run tests and verify pass**

```bash
pytest tests/parsing/test_ingest.py -v
```

Expected: 2 passed.

## Task 5: Native PDF Extraction

**Files:**
- Create: `src/nature/parsing/native.py`
- Test: `tests/parsing/test_native.py`

- [ ] **Step 1: Write native extraction test**

```python
import fitz

from nature.parsing.native import extract_native_pdf


def test_extract_native_pdf_reads_text_and_page_count(tmp_path):
    pdf = tmp_path / "paper.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Introduction\nThis is a test paper.")
    doc.save(pdf)
    doc.close()

    result = extract_native_pdf(pdf)

    assert result.page_count == 1
    assert "Introduction" in result.pages[0].text
```

- [ ] **Step 2: Run tests and verify failure**

```bash
pytest tests/parsing/test_native.py -v
```

Expected: import failure because `nature.parsing.native` does not exist.

- [ ] **Step 3: Implement native extraction**

```python
# src/nature/parsing/native.py
from dataclasses import dataclass
from pathlib import Path

import fitz


@dataclass(frozen=True)
class NativePage:
    page_number: int
    text: str


@dataclass(frozen=True)
class NativePdf:
    page_count: int
    title: str
    author: str
    pages: list[NativePage]


def extract_native_pdf(path: Path) -> NativePdf:
    with fitz.open(path) as document:
        metadata = document.metadata or {}
        pages = [
            NativePage(page_number=index + 1, text=page.get_text("text"))
            for index, page in enumerate(document)
        ]
        return NativePdf(
            page_count=document.page_count,
            title=metadata.get("title") or "",
            author=metadata.get("author") or "",
            pages=pages,
        )
```

- [ ] **Step 4: Run tests and verify pass**

```bash
pytest tests/parsing/test_native.py -v
```

Expected: 1 passed.

## Task 6: Section Assembly

**Files:**
- Create: `src/nature/parsing/sections.py`
- Test: `tests/parsing/test_sections.py`

- [ ] **Step 1: Write section assembly test**

```python
from nature.parsing.native import NativePage, NativePdf
from nature.parsing.sections import build_sections_from_native


def test_build_sections_from_native_creates_single_section():
    native = NativePdf(
        page_count=1,
        title="",
        author="",
        pages=[NativePage(page_number=1, text="Introduction\nThis is the body.")],
    )

    sections = build_sections_from_native(native)

    assert len(sections) == 1
    assert sections[0].id == "sec-001"
    assert sections[0].title == "Document"
    assert "Introduction" in sections[0].markdown
```

- [ ] **Step 2: Run tests and verify failure**

```bash
pytest tests/parsing/test_sections.py -v
```

Expected: import failure because `nature.parsing.sections` does not exist.

- [ ] **Step 3: Implement section assembly**

```python
# src/nature/parsing/sections.py
from nature.parsing.model import PageSpan, Section
from nature.parsing.native import NativePdf


def build_sections_from_native(native: NativePdf) -> list[Section]:
    text = "\n\n".join(
        page.text.strip()
        for page in native.pages
        if page.text.strip()
    )
    if not text:
        text = ""

    end_page = max(native.page_count, 1)
    return [
        Section(
            id="sec-001",
            title="Document",
            level=1,
            order=1,
            page_span=PageSpan(start=1, end=end_page),
            markdown=text,
        )
    ]
```

- [ ] **Step 4: Run tests and verify pass**

```bash
pytest tests/parsing/test_sections.py -v
```

Expected: 1 passed.

## Task 7: Quality Reporting

**Files:**
- Create: `src/nature/parsing/quality.py`
- Test: `tests/parsing/test_quality.py`

- [ ] **Step 1: Write quality tests**

```python
from nature.config.model import ParsingOptions
from nature.parsing.native import NativePage, NativePdf
from nature.parsing.quality import assess_native_quality


def test_quality_warns_when_native_text_is_sparse():
    config = ParsingOptions(
        page_image_dpi=200,
        ocr_enabled=True,
        ocr_engine="paddleocr-pp-structure-v3",
        ocr_language="en",
        min_native_text_chars_per_page=80,
        low_confidence_threshold=0.75,
    )
    native = NativePdf(page_count=1, title="", author="", pages=[NativePage(1, "short")])

    report = assess_native_quality(native, config)

    assert report.overall_confidence < 1.0
    assert report.warnings[0].code == "sparse-native-text"
```

- [ ] **Step 2: Run tests and verify failure**

```bash
pytest tests/parsing/test_quality.py -v
```

Expected: import failure because `nature.parsing.quality` does not exist.

- [ ] **Step 3: Implement quality assessment**

```python
# src/nature/parsing/quality.py
from nature.config.model import ParsingOptions
from nature.parsing.model import QualityReport, QualityWarning
from nature.parsing.native import NativePdf


def assess_native_quality(native: NativePdf, config: ParsingOptions) -> QualityReport:
    if native.page_count == 0:
        return QualityReport(
            overall_confidence=0.0,
            warnings=[
                QualityWarning(
                    code="empty-document",
                    message="PDF contains no pages.",
                    severity="error",
                )
            ],
        )

    sparse_pages = [
        page.page_number
        for page in native.pages
        if len(page.text.strip()) < config.min_native_text_chars_per_page
    ]
    if sparse_pages:
        return QualityReport(
            overall_confidence=config.low_confidence_threshold,
            warnings=[
                QualityWarning(
                    code="sparse-native-text",
                    message=f"Native extraction is sparse on pages: {sparse_pages}.",
                    severity="warning",
                )
            ],
        )

    return QualityReport(overall_confidence=1.0)
```

- [ ] **Step 4: Run tests and verify pass**

```bash
pytest tests/parsing/test_quality.py -v
```

Expected: 1 passed.

## Task 8: Public Parsing Pipeline

**Files:**
- Create: `src/nature/parsing/pipeline.py`
- Modify: `src/nature/parsing/__init__.py`
- Test: `tests/parsing/test_pipeline.py`

- [ ] **Step 1: Write pipeline integration test**

```python
import fitz

from nature.config.model import ParsingOptions
from nature.parsing.pipeline import ParseInput, parse_document


def parsing_config() -> ParsingOptions:
    return ParsingOptions(
        page_image_dpi=200,
        ocr_enabled=True,
        ocr_engine="paddleocr-pp-structure-v3",
        ocr_language="en",
        min_native_text_chars_per_page=10,
        low_confidence_threshold=0.75,
    )


def test_parse_document_returns_parsed_document(tmp_path):
    pdf = tmp_path / "paper.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Introduction\nThis paper has enough text.")
    doc.save(pdf)
    doc.close()

    parsed = parse_document(
        ParseInput(source_path=pdf, document_slug="paper-one", kind="paper"),
        parsing_config(),
    )

    assert parsed.document_slug == "paper-one"
    assert parsed.metadata.page_count == 1
    assert parsed.sections[0].markdown
    assert parsed.quality.overall_confidence == 1.0
```

- [ ] **Step 2: Run tests and verify failure**

```bash
pytest tests/parsing/test_pipeline.py -v
```

Expected: import failure because `nature.parsing.pipeline` does not exist.

- [ ] **Step 3: Implement pipeline**

```python
# src/nature/parsing/pipeline.py
from dataclasses import dataclass
from pathlib import Path

from nature.config.model import ParsingOptions
from nature.parsing.ingest import ingest_pdf
from nature.parsing.model import DocumentMetadata, ParsedDocument
from nature.parsing.native import extract_native_pdf
from nature.parsing.quality import assess_native_quality
from nature.parsing.sections import build_sections_from_native


@dataclass(frozen=True)
class ParseInput:
    source_path: Path
    document_slug: str
    kind: str = "paper"


def parse_document(input: ParseInput, config: ParsingOptions) -> ParsedDocument:
    ingested = ingest_pdf(input.source_path)
    native = extract_native_pdf(ingested.path)
    sections = build_sections_from_native(native)
    quality = assess_native_quality(native, config)

    return ParsedDocument(
        id=ingested.document_id,
        document_slug=input.document_slug,
        kind=input.kind,
        source_path=ingested.path,
        fingerprint=ingested.fingerprint,
        metadata=DocumentMetadata(
            title=native.title,
            authors=[native.author] if native.author else [],
            page_count=native.page_count,
        ),
        sections=sections,
        quality=quality,
    )
```

```python
# src/nature/parsing/__init__.py
from nature.parsing.model import ParsedDocument
from nature.parsing.pipeline import ParseInput, parse_document

__all__ = ["ParseInput", "ParsedDocument", "parse_document"]
```

- [ ] **Step 4: Run tests and verify pass**

```bash
pytest tests/parsing/test_pipeline.py -v
```

Expected: 1 passed.

## Task 9: Page Rendering Adapter

**Files:**
- Create: `src/nature/parsing/rendering.py`
- Test: `tests/parsing/test_rendering.py`

- [ ] **Step 1: Write rendering test**

```python
import fitz

from nature.parsing.rendering import render_pdf_pages


def test_render_pdf_pages_writes_pngs(tmp_path):
    pdf = tmp_path / "paper.pdf"
    output_dir = tmp_path / "pages"
    doc = fitz.open()
    doc.new_page()
    doc.save(pdf)
    doc.close()

    pages = render_pdf_pages(pdf, output_dir, dpi=72)

    assert len(pages) == 1
    assert pages[0].page_number == 1
    assert pages[0].image_path.exists()
```

- [ ] **Step 2: Run tests and verify failure**

```bash
pytest tests/parsing/test_rendering.py -v
```

Expected: import failure because `nature.parsing.rendering` does not exist.

- [ ] **Step 3: Implement rendering**

```python
# src/nature/parsing/rendering.py
from dataclasses import dataclass
from pathlib import Path

import fitz


@dataclass(frozen=True)
class RenderedPage:
    page_number: int
    image_path: Path


def render_pdf_pages(path: Path, output_dir: Path, dpi: int) -> list[RenderedPage]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rendered: list[RenderedPage] = []
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)

    with fitz.open(path) as document:
        for index, page in enumerate(document):
            image_path = output_dir / f"page-{index + 1:03d}.png"
            pixmap = page.get_pixmap(matrix=matrix)
            pixmap.save(image_path)
            rendered.append(RenderedPage(page_number=index + 1, image_path=image_path))

    return rendered
```

- [ ] **Step 4: Run tests and verify pass**

```bash
pytest tests/parsing/test_rendering.py -v
```

Expected: 1 passed.

## Task 10: OCR/Layout Extension Interfaces

**Files:**
- Create: `src/nature/parsing/ocr.py`
- Create: `src/nature/parsing/layout.py`
- Test: `tests/parsing/test_extension_interfaces.py`

- [ ] **Step 1: Write extension interface tests**

```python
from pathlib import Path

from nature.parsing.layout import LayoutRegion
from nature.parsing.ocr import OcrBlock


def test_extension_models_are_plain_data():
    region = LayoutRegion(
        id="region-001",
        page=1,
        kind="paragraph",
        bbox=(0.0, 0.0, 10.0, 10.0),
        confidence=0.9,
    )
    block = OcrBlock(
        id="ocr-001",
        page=1,
        text="hello",
        bbox=(0.0, 0.0, 10.0, 10.0),
        confidence=0.9,
        image_path=Path("page-001.png"),
    )

    assert region.kind == "paragraph"
    assert block.text == "hello"
```

- [ ] **Step 2: Run tests and verify failure**

```bash
pytest tests/parsing/test_extension_interfaces.py -v
```

Expected: import failure because OCR/layout modules do not exist.

- [ ] **Step 3: Implement extension models**

```python
# src/nature/parsing/layout.py
from dataclasses import dataclass


@dataclass(frozen=True)
class LayoutRegion:
    id: str
    page: int
    kind: str
    bbox: tuple[float, float, float, float]
    confidence: float
```

```python
# src/nature/parsing/ocr.py
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class OcrBlock:
    id: str
    page: int
    text: str
    bbox: tuple[float, float, float, float]
    confidence: float
    image_path: Path
```

- [ ] **Step 4: Run tests and verify pass**

```bash
pytest tests/parsing/test_extension_interfaces.py -v
```

Expected: 1 passed.

## Task 11: Full Test Run And Build Check

**Files:**
- Modify only files required by previous failing tests.

- [ ] **Step 1: Run all tests**

```bash
make test
```

Expected: all tests pass.

- [ ] **Step 2: Run build**

```bash
make build
```

Expected: source and wheel distributions build successfully.

- [ ] **Step 3: Review package imports**

```bash
python -m compileall src tests
```

Expected: all Python files compile.

## Out Of Scope For This Plan

- PaddleOCR PP-StructureV3 integration beyond interface seams.
- Table structure recognition from layout regions.
- Formula recognition into LaTeX.
- Figure extraction and metadata attachment.
- Reference parsing beyond future extension points.
- CLI commands and end-to-end `nature run`.

Those should be implemented as follow-up plans after the native parsing slice is merged and tested.

## Self-Review

Spec coverage:

- Ingest and fingerprint: Task 4.
- Native PDF extraction: Task 5.
- Page rendering: Task 9.
- Parsed data schema: Task 3.
- Section model: Task 6.
- Quality reporting: Task 7.
- Public pipeline output: Task 8.
- OCR/layout seams: Task 10.

Placeholder scan:

- No task uses placeholder markers or unspecified implementation language.

Type consistency:

- `ParsedDocument`, `ParsingOptions`, `ParseInput`, and `RetrievalDataset` references match the architecture docs and the planned package layout.
