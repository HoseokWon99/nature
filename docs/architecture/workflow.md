# Workflow

Nature loads required machine-local defaults from `~/.nature/nature-config.json` before running parsing, wiki, embedding, or retrieval. The full config shape is defined in `../configuration.md`.

```mermaid
flowchart TD
    A[PDF papers and textbooks] --> B[Parse documents]
    B --> C{Needs OCR?}
    C -- Yes --> D[PaddleOCR PP-StructureV3]
    C -- No --> E[Extract native text and structure]
    D --> F[Normalize extracted content]
    E --> F
    F --> G[Structured document model]
    G --> H[Generate Obsidian wiki notes]
    H --> I[Save Markdown in vault]
    H --> J[Build in-memory retrieval dataset]
    J --> K[Generate embeddings with Sentence-Transformer]
    K --> L[Store vectors and metadata in SQLite-Vector]
    L --> M[Retriever]
    M --> N[Relevant notes and source chunks]
```

## Steps

1. Collect paper and textbook PDF files.
2. Parse each document and run OCR when native text or layout extraction is insufficient.
3. Normalize extracted text, tables, figures, equations, sections, and metadata into a structured document model.
4. Generate Obsidian-compatible Markdown notes in the target vault.
5. Build an in-memory retrieval dataset from the wiki notes and parsed source mappings.
6. Pass the retrieval dataset directly to Sentence-Transformer embedding generation.
7. Store vectors and metadata in SQLite-Vector.
8. Retrieve relevant notes and source chunks for user queries.
