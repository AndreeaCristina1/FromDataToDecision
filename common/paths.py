# -*- coding: utf-8 -*-
"""Paths used by all scripts. Everything is relative to the repository root, so the scripts run on any machine."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DATA = ROOT / "data"
RAW = DATA / "raw"
RAW_TEMPO = RAW / "tempo_panel"
PROCESSED = DATA / "processed"

STAGE1_RESULTS = ROOT / "stage1_describe" / "results"
STAGE2_RESULTS = ROOT / "stage2_forecast" / "results"
SD_DIR = ROOT / "stage3_system_dynamics"
SD_RESULTS = SD_DIR / "results"
SD_SIMULATORS = SD_DIR / "simulators"
DESIGN_DIR = ROOT / "stage4_design"
DESIGN_RESULTS = DESIGN_DIR / "results"
FIGURES = ROOT / "figures"
VERIFICATION = ROOT / "verification"


def utf8_console() -> None:
    """Windows consoles may use a legacy code page; switch to UTF-8 so that printing never fails."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def ensure(path: Path) -> Path:
    """Create the directory if needed and return it."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path: Path, obj) -> None:
    """Write an object that may contain NumPy scalars or arrays as readable UTF-8 JSON."""
    def default(x):
        if hasattr(x, "tolist"):
            return x.tolist()
        raise TypeError(type(x))
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1, default=default), encoding="utf-8")
