from __future__ import annotations

from pathlib import Path
import sys

from docx import Document


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: dump_top_paragraphs.py <docx> <count>")
        return 1

    doc = Document(str(Path(sys.argv[1])))
    count = int(sys.argv[2])
    for idx, para in enumerate(doc.paragraphs[:count]):
        print(f"{idx}:{para.style.name}:{para.text.strip()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
