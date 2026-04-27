# Agents

## Overview

- **Name**: nature
- **Description**: Science & Engineering knowledge llm wiki generator

## Features

1. Parse paper & textbook pdf files
2. Generate wiki under a given obsidian vault
3. Extract and save embeddings
4. Retriever

## Skills

- **Language**: Python 3.13
- **Package Manager**: UV
- **Build Tool**: UV, Make
- **OCR**: PaddleOCR(PP-StructureV3)
- **Embeddings**: Sentence-Transformer
- **Vector Store**: SQLite-Vector

## Commands

1. `make build`: Build source and wheel distributions
2. `make test`: Run the test suite
3. `make run`: Run the application entry point
4. `uv add <package>`: Add a runtime dependency
5. `uv add --dev <package>`: Add a development dependency

## Conventions

1. For functions, classes, methods, the exported come before the unexported
2. Constants are unexported by default unless they are part of a public API.

## Rules

1. Prefer list comprehension for performance
2. OOP design
3. SRP & DRY
4. Use `id` for an object's own identifier in schemas; use explicit names like `section_id` or `equation_ids` only when referencing another object.

## Architecture

- **Workflow**: `@docs/architecture/workflow.md`
- **Parsing Pipeline**: `@docs/architecture/parsing-pipeline.md` 
