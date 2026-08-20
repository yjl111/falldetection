from pathlib import Path
import sys
import zipfile


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: inspect_docx_raw_fields.py <docx_path>")
        return 1

    path = Path(sys.argv[1])
    with zipfile.ZipFile(path) as zf:
        document_xml = zf.read("word/document.xml").decode("utf-8", errors="ignore")
        footer_xml = "".join(
            zf.read(name).decode("utf-8", errors="ignore")
            for name in zf.namelist()
            if name.startswith("word/footer")
        )

    for label, text, keyword in [
        ("DOC_TOC", document_xml, "TOC"),
        ("FOOTER_PAGE", footer_xml, "PAGE"),
    ]:
        idx = text.find(keyword)
        print(f"{label}_FOUND={'YES' if idx >= 0 else 'NO'}")
        if idx >= 0:
            start = max(0, idx - 120)
            end = min(len(text), idx + 120)
            print(text[start:end])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
