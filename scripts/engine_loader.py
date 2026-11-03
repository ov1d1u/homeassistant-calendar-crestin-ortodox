"""Load the integration's engine module without importing Home Assistant."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMPONENT = ROOT / "custom_components" / "calendar_ortodox"
FIXTURES = ROOT / "tests" / "fixtures" / "site"


def load_engine():
    """Import custom_components/calendar_ortodox/engine.py as a standalone module."""
    name = "calendar_ortodox_engine"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, COMPONENT / "engine.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module
