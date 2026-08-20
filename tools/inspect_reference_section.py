from pathlib import Path
import sys

from docx import Document


def safe_print(text: str) -> None:
    encoding = sys.stdout.encoding or "utf-8"
    sys.stdout.buffer.write((text + "\n").encode(encoding, errors="replace"))


def main() -> int:
    if len(sys.argv) != 2:
        safe_print("Usage: inspect_reference_section.py <docx_path>")
        return 1

    doc = Document(str(Path(sys.argv[1])))
    paragraphs = doc.paragraphs
    ref_index = None
    for i, p in enumerate(paragraphs):
        if p.text.strip().replace(" ", "").replace("\u3000", "") == "参考文献":
            ref_index = i
            break

    safe_print(f"REFERENCE_INDEX={ref_index}")
    if ref_index is None:
        return 0

    start = max(0, ref_index - 5)
    end = min(len(paragraphs), ref_index + 40)
    for i in range(start, end):
        p = paragraphs[i]
        txt = p.text.replace("\t", " ").strip()
        safe_print(f"{i}:{p.style.name if p.style else ''}:{txt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
