"""Top-level PyInstaller entry point.

PyInstaller executes this file as a script, so it intentionally uses an
absolute package import rather than the relative import used by __main__.py.
"""

import os
import sys
from pathlib import Path

if hasattr(sys, "_MEIPASS"):
    runtime = Path(sys._MEIPASS) / "tcl"
    os.environ.setdefault("TCL_LIBRARY", str(runtime / "tcl8.6"))
    os.environ.setdefault("TK_LIBRARY", str(runtime / "tk8.6"))

from office_to_markdown.app import main

if __name__ == "__main__":
    main()
