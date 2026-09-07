"""Reusable Maya controller-shape toolkit.

Importing this package never creates UI. Use :mod:`controller_shape_library.api`
for scripting, or call :func:`controller_shape_library.ui.main_window.show` explicitly.
"""

from . import api

__all__ = ["api"]
__version__ = "1.1.0"
