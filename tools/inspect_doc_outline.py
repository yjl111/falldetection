from __future__ import annotations

from pathlib import Path
import sys

from docx import Document


def norm(text: str) -> str:
    return text.strip().replace("\u3000", " ")


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: inspect_doc_outline.py <docx>")
        return 1

    doc = Document(str(Path(sys.argv[1])))
    for idx, p in enumerate(doc.paragraphs):
        text = norm(p.text)
        if not text:
            continue
        if text.startswith("第") and "章" in text[:8]:
            print(f"{idx}:{p.style.name}:{text}")
        elif text in {
            "摘  要",
            "Abstract",
            "ABSTRACT",
            "目  录",
            "参考文献",
            "致  谢",
            "附  录",
        }:
            print(f"{idx}:{p.style.name}:{text}")
        elif any(text.startswith(prefix) for prefix in ("1.", "1 ", "1　", "2.", "3.", "4.", "5.", "6.", "7.")):
            print(f"{idx}:{p.style.name}:{text}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
