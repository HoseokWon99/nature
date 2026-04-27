import os
from pathlib import Path


def ensure_file(filepath: Path, content: str = ""):
    if filepath.exists():
        return
    os.makedirs(filepath.parent, exist_ok=True)
    with open(filepath, "w") as f:
        f.write(content)

