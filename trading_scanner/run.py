"""Entry point for Trading Scanner."""

import subprocess
import sys
from pathlib import Path


def main():
    app_path = Path(__file__).parent / "ui" / "app.py"
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(app_path), "--server.headless", "true"],
        cwd=str(Path(__file__).parent),
    )


if __name__ == "__main__":
    main()
