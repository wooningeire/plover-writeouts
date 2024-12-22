from plover.steno import Stroke

from ..theory.theory import (
    ASTERISK_SUBSTROKE,
    LEFT_BANK_CONSONANTS_SUBSTROKE,
    RIGHT_BANK_CONSONANTS_SUBSTROKE,
    VOWELS_SUBSTROKE,
)

def can_add_stroke_on(src_stroke: Stroke, addon_stroke: Stroke):
    return (
        len(src_stroke - ASTERISK_SUBSTROKE) == 0
        or len(addon_stroke - ASTERISK_SUBSTROKE) == 0
        or Stroke.from_keys(((src_stroke - ASTERISK_SUBSTROKE).keys()[-1],)) < Stroke.from_keys(((addon_stroke - ASTERISK_SUBSTROKE).keys()[0],))
    )

def split_stroke_parts(stroke: Stroke):
    left_bank_consonants = stroke & LEFT_BANK_CONSONANTS_SUBSTROKE
    vowels = stroke & VOWELS_SUBSTROKE
    right_bank_consonants = stroke & RIGHT_BANK_CONSONANTS_SUBSTROKE
    asterisk = stroke & ASTERISK_SUBSTROKE

    return left_bank_consonants, vowels, right_bank_consonants, asterisk