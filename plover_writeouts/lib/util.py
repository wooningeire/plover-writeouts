from plover.steno import Stroke

from .config import (
    ASTERISK_SUBSTROKE,
)

def can_add_stroke_on(src_stroke: Stroke, addon_stroke: Stroke):
    return (
        len(src_stroke) == 0
        or len(addon_stroke) == 0
        or Stroke.from_keys(((src_stroke - ASTERISK_SUBSTROKE).keys()[-1],)) < Stroke.from_keys(((addon_stroke - ASTERISK_SUBSTROKE).keys()[0],))
    )