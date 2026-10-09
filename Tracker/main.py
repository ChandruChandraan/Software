"""
Firing Simulator Headless Tracker Service Launcher.
Headless entry point executing without GUI windows, streaming marksmanship telemetry
to Unreal Engine (Port 47000) and Backend Server (Port 47001).
"""

import sys
from pathlib import Path

# Ensure package root is in sys.path
_base_dir = Path(__file__).resolve().parent
if str(_base_dir) not in sys.path:
    sys.path.insert(0, str(_base_dir))

from headless_tracker import run_daemon


def main():
    """Launch the headless tracker daemon."""
    run_daemon()


if __name__ == "__main__":
    main()
