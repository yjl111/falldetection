from __future__ import annotations

from pathlib import Path
import re
import sys
import zipfile

from docx import Document


def read_xml(zf: zipfile.ZipFile, name: str) -> str:
    try:
        return zf.read(name).decode("utf-8", errors="ignore")
    except KeyError:
        return ""


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: inspect_docx_structure.py <docx_path>")
        return 1

    path = Path(sys.argv[1])
    doc = Document(str(path))
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

    with zipfile.ZipFile(path) as zf:
        document_xml = read_xml(zf, "word/document.xml")
        footer_xml = "".join(read_xml(zf, name) for name in zf.namelist() if name.startswith("word/footer"))
        header_xml = "".join(read_xml(zf, name) for name in zf.namelist() if name.startswith("word/header"))
        all_xml = document_xml + footer_xml + header_xml

    has_toc_field = " TOC " in all_xml or 'TOC \\o' in all_xml
    page_field_count = all_xml.count(" PAGE ")

    toc_heading_count = sum(1 for p in paragraphs if p in {"目录", "目 录", "目　录"})
    abstract_heading_count = sum(1 for p in paragraphs if p in {"摘要", "Abstract"})
    back_matter = [p for p in paragraphs if p.replace(" ", "") in {"参考文献", "致谢", "声明"}]

    figure_numbers = []
    for p in paragraphs:
        m = re.match(r"^图\s*(\d+)-(\d+)", p)
        if m:
            figure_numbers.append((int(m.group(1)), int(m.group(2)), p))

    print(f"FILE={path}")
    print(f"TOC_FIELD={'YES' if has_toc_field else 'NO'}")
    print(f"PAGE_FIELD_COUNT={page_field_count}")
    print(f"TOC_HEADING_COUNT={toc_heading_count}")
    print(f"ABSTRACT_HEADINGS={abstract_heading_count}")
    print(f"BACK_MATTER={' | '.join(back_matter)}")
    print("FIGURES=")
    for _, _, text in figure_numbers:
        print(text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
