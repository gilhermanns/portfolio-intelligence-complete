#!/usr/bin/env python
"""Thin wrapper so the CLI can be run as `python scripts/price_option.py ...`
without installing the package."""
from options_vol_lab.cli import main

if __name__ == "__main__":
    main()
