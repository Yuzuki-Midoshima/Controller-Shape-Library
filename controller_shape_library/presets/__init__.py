"""Built-in controller shape definitions."""

from .arrows import SHAPES as ARROW_SHAPES
from .arrow_variants import SHAPES as ARROW_VARIANTS
from .basic import SHAPES as BASIC_SHAPES
from .custom import SHAPES as CUSTOM_SHAPES
from .direction import SHAPES as DIRECTION_SHAPES
from .additional_rotation import SHAPES as ADDITIONAL_ROTATION_SHAPES
from .additional_volume import SHAPES as ADDITIONAL_VOLUME_SHAPES
from .panel import SHAPES as PANEL_SHAPES
from .rig import SHAPES as RIG_SHAPES
from .rotation import SHAPES as ROTATION_SHAPES
from .special import SHAPES as SPECIAL_SHAPES
from .utility_shapes import SHAPES as UTILITY_SHAPES
from .volume import SHAPES as VOLUME_SHAPES

SHAPES = {}
for _collection in (
    BASIC_SHAPES, UTILITY_SHAPES, VOLUME_SHAPES, ADDITIONAL_VOLUME_SHAPES,
    ARROW_SHAPES, ARROW_VARIANTS, ROTATION_SHAPES, ADDITIONAL_ROTATION_SHAPES,
    DIRECTION_SHAPES, RIG_SHAPES, SPECIAL_SHAPES, PANEL_SHAPES, CUSTOM_SHAPES,
):
    SHAPES.update(_collection)

__all__ = ["SHAPES"]
