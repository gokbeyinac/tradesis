"""Streamlit entry point for deployment."""

import subprocess
import sys
from pathlib import Path

# Add trading_scanner to path
sys.path.insert(0, str(Path(__file__).parent / "trading_scanner"))

# Re-export the app
exec(open(Path(__file__).parent / "trading_scanner" / "ui" / "app.py").read())
