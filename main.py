#!/usr/bin/env python3
"""Uruchamia RemApps bezpośrednio z folderu projektu."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from remapps.app import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
