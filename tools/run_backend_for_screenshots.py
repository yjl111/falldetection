import os
import sys


BACKEND_DIR = r"D:\falldetection\backend"
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

os.chdir(BACKEND_DIR)

import app as thesis_app  # noqa: E402


if __name__ == "__main__":
    thesis_app.app.run(host="127.0.0.1", port=5001, debug=False, use_reloader=False)
