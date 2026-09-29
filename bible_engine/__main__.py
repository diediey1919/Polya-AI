"""
Package executable entry point for Polya Philological Bible Engine.
Allows running: python3 -m bible_engine {status,migrate}
"""

import sys
from bible_engine.cli import main

if __name__ == "__main__":
    sys.exit(main())
