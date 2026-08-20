from pathlib import Path
import sys


def safe_print(text: str) -> None:
    encoding = sys.stdout.encoding or "utf-8"
    sys.stdout.buffer.write((text + "\n").encode(encoding, errors="replace"))


def main() -> int:
    if len(sys.argv) != 4:
        print("Usage: print_line_range.py <file> <start> <end>")
        return 1

    path = Path(sys.argv[1])
    start = int(sys.argv[2])
    end = int(sys.argv[3])
    lines = path.read_text(encoding="utf-8").splitlines()

    for index in range(max(start, 1), min(end, len(lines)) + 1):
        safe_print(f"{index}:{lines[index - 1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
