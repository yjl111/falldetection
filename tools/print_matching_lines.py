from pathlib import Path
import sys


def safe_print(text: str) -> None:
    encoding = sys.stdout.encoding or "utf-8"
    sys.stdout.buffer.write((text + "\n").encode(encoding, errors="replace"))


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: print_matching_lines.py <file> <keyword1> [<keyword2> ...]")
        return 1

    path = Path(sys.argv[1])
    keywords = sys.argv[2:]
    lines = path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines, start=1):
        if any(keyword in line for keyword in keywords):
            safe_print(f"{index}:{line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
