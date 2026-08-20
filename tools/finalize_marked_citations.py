from __future__ import annotations

from pathlib import Path
import sys

from docx import Document


REPLACEMENTS = {
    "【建议为课题意义与应用价值补充文献引用】": "[1][5]",
    "【建议为OpenCV功能描述补充文献引用】": "[11]",
    "【建议为MongoDB集合设计说明补充文献引用】": "[11]",
    "【建议为GridFS存储机制说明补充文献引用】": "[11]",
    "【建议为认证与权限控制技术说明补充文献引用】": "[9]",
    "【建议为测试环境涉及的关键技术栈补充文献引用】": "[9][10][11]",
}


def inject(text: str, citation: str) -> str:
    stripped = text.rstrip()
    if citation in stripped:
        return stripped
    for mark in ("。", ".", "；", ";"):
        if stripped.endswith(mark):
            return stripped[:-1] + citation + mark
    return stripped + citation


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: finalize_marked_citations.py <source.docx> <target.docx>")
        return 1

    source = Path(sys.argv[1])
    target = Path(sys.argv[2])
    doc = Document(str(source))

    for paragraph in doc.paragraphs:
        text = paragraph.text
        for marker, citation in REPLACEMENTS.items():
            if marker in text:
                cleaned = text.replace(marker, "")
                paragraph.text = inject(cleaned, citation)
                break

    target.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(target))
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
