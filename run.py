"""
Entry point used by PyInstaller. Wraps app.main so the build can resolve a
single .py file at the repo root.
"""
from app.main import main
import sys

if __name__ == "__main__":
    sys.exit(main())
