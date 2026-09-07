"""Run Maya-independent tests with the Qt application required by font presets."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6 import QtGui


application = QtGui.QGuiApplication.instance() or QtGui.QGuiApplication([])
suite = unittest.defaultTestLoader.discover(
    "tests", pattern="test_controller_shape_data.py")
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(not result.wasSuccessful())
