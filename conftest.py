from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_PATHS = [ROOT / "apps" / "api", ROOT / "packages" / "ingestion"]

for source_path in SOURCE_PATHS:
    source = str(source_path)
    if source not in sys.path:
        sys.path.insert(0, source)
