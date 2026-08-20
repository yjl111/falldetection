from pathlib import Path
import re
import sys


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: extract_mermaid_blocks.py <source_md> <output_dir>")
        return 1

    source = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    text = source.read_text(encoding="utf-8")
    matches = re.findall(r"```mermaid\r?\n(.*?)\r?\n```", text, re.S)

    output_dir.mkdir(parents=True, exist_ok=True)
    for index, block in enumerate(matches, start=1):
        target = output_dir / f"mermaid_{index}.mmd"
        target.write_text(block.strip() + "\n", encoding="utf-8")
        print(target)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
