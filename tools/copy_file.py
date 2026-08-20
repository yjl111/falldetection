from pathlib import Path
import shutil
import sys


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: copy_file.py <source> <target>")
        return 1

    source = Path(sys.argv[1].strip('"'))
    target = Path(sys.argv[2].strip('"'))

    if not source.exists():
        print(f"SOURCE_NOT_FOUND: {source}")
        return 2

    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
