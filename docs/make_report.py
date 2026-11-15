"""Compatibility entry point for the current evidence-backed report."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).resolve().parents[1]/"scripts/build_report.py"),run_name="__main__")
