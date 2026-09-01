"""Top-level PyInstaller entry point.

PyInstaller executes this file as a script, so it intentionally uses an
absolute package import rather than the relative import used by __main__.py.
"""

from office_to_markdown.app import main

if __name__ == "__main__":
    main()
