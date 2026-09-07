"""Built-in controller shape definitions."""

from .arrows import SHAPES as ARROW_SHAPES
from .basic import SHAPES as BASIC_SHAPES
from .custom import SHAPES as CUSTOM_SHAPES
from .direction import SHAPES as DIRECTION_SHAPES
from .mox import SHAPES as MOX_SHAPES
from .panel import SHAPES as PANEL_SHAPES

SHAPES = {}
for _collection in (
    BASIC_SHAPES, ARROW_SHAPES, DIRECTION_SHAPES, PANEL_SHAPES,
    MOX_SHAPES, CUSTOM_SHAPES,
):
    SHAPES.update(_collection)

__all__ = ["SHAPES"]
