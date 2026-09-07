"""Maya Script Editor launcher for Controller-Shape-Library."""

from __future__ import annotations

import os
import sys
import importlib

_ROOT = os.path.dirname(os.path.abspath(__file__))
# Always prefer this checkout, even if another copy of the package was added
# to Maya's long-lived sys.path earlier in the session.
_root_key = os.path.normcase(os.path.normpath(_ROOT))
sys.path[:] = [path for path in sys.path
               if os.path.normcase(os.path.normpath(path or os.curdir)) != _root_key]
sys.path.insert(0, _ROOT)

# Maya keeps imported modules for the whole application session. Reload the
# complete package so shelf launches always see newly installed API/features.
importlib.invalidate_caches()
for _module_name in sorted(
    [name for name in sys.modules
     if name == "controller_shape_library" or name.startswith("controller_shape_library.")],
    key=lambda name: name.count("."),
    reverse=True,
):
    del sys.modules[_module_name]

from controller_shape_library.ui.main_window import show

show()
