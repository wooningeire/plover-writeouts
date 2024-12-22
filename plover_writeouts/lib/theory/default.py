from abc import ABC

from plover.steno import Stroke

from .spec import TheorySpec

class DefaultSpec(TheorySpec, ABC):
    ALL_KEYS = Stroke.from_steno("STKPWHRAO*EUFRPBLGTSDZ")


    LEFT_BANK_CONSONANTS_SUBSTROKE = Stroke.from_steno("STKPWHR")
    VOWELS_SUBSTROKE = Stroke.from_steno("AOEU")
    RIGHT_BANK_CONSONANTS_SUBSTROKE = Stroke.from_steno("-FRPBLGTSDZ")
    ASTERISK_SUBSTROKE = Stroke.from_steno("*")

