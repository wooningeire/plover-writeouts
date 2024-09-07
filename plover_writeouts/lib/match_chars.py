from dataclasses import dataclass
from typing import Generator, cast, NamedTuple
from abc import ABC

from plover_writeouts.lib.alignment import Sliceable

from .steno_annotations import AsteriskableKey, AnnotatedChord

from .alignment import AlignmentService, Cell, aligner


_GRAPHEME_TO_STENO_MAPPINGS = {
    grapheme: sorted(
        tuple(AsteriskableKey.annotations_from_outline(outline_steno) for outline_steno in outline_stenos),
        key=lambda keys: len(keys), reverse=True
    )
    for grapheme, outline_stenos in cast(dict[str, tuple[str, ...]], {
        # Does not need to be fully complete to be effective

        "": ("KWR", "W"),

        "a": ("A", "AEU", "AU"),
        "b": ("PW", "-B"),
        "c": ("S", "K", "KR", "-BG", "-S", "SH", "-RB", "KH", "-FP"),
        "d": ("TK", "-D"),
        "e": ("E", "AOE", "AEU", "E/KWR", "AOE/KWR"),
        "f": ("TP", "-F"),
        "g": ("SKWR", "TKPW", "-PBLG", "-G"),
        "h": ("H",),
        "i": ("EU", "AOEU", "EU/KWR", "AOEU/KWR"),
        "j": ("SKWR", "-PBLG", "-G"),
        "k": ("K", "-BG", "*G"),
        "l": ("HR", "-L"),
        "m": ("PH", "-PL"),
        "n": ("TPH", "-PB"),
        "o": ("O", "OE", "O/W", "OE/W"),
        "p": ("P", "-P"),
        "q": ("K", "-BG"),
        "r": ("R", "-R"),
        "s": ("S", "-S", "-F", "-Z", "SH", "-RB"),
        "t": ("T", "-T", "SH", "-RB", "KH", "-FP"),
        "u": ("U", "W", "AOU", "U/W", "AOU/W", "KWRU", "KWRAOU", "KWRU/W", "KWRAOU/W"),
        "v": ("SR", "-F"),
        "w": ("W", "U"),
        "x": ("KP", "-BGS", "-BG/S"),
        "y": ("KWH", "EU", "AOEU", "EU/KWR", "AOEU/KWR"),
        "z": ("STKPW", "-Z", "-F"),

        "th": ("TH", "*T"),
        "sh": ("SH", "-RB"),
        "ch": ("KH", "-FP"),

        "aa": ("A", "AU"),
        "ee": ("AOE",),
        "ii": ("AOE", "EU"),
        "oo": ("AO",),
        "ou": ("U", "OU"),
        "ea": ("AOE", "AE"),
        "ae": ("AE", "AEU"),
        "ai": ("AEU", "AOEU"),
        "ay": ("AEU", "AOEU"),
        "au": ("AU",),
        "aw": ("AU",),
        "oi": ("OEU",),
        "oy": ("OEU",),
        "ow": ("OU",),
        "ei": ("AOE", "E"),
        "ey": ("AOE", "E"),
        "ie": ("AOE", "E"),

        "dg": ("SKWR", "-PBLG"),
        "ck": ("K", "-BG"),
        "ti": ("SH", "-RB", "-RB/KWR"),
        "ci": ("SH", "-RB", "-RB/KWR"),
        "mp": ("*PL",),
        "sc": ("S", "-S"),

        "bb": ("PW", "-B"),
        "cc": ("S", "K", "KR", "-BG", "-S"),
        "dd": ("TK", "-D"),
        "ff": ("TP", "-F"),
        "gg": ("SKWR", "TKPW", "-PBLG", "-G"),
        "jj": ("SKWR", "-PBLG", "-G"),
        "kk": ("K", "-BG", "*G"),
        "ll": ("HR", "-L"),
        "mm": ("PH", "-PL"),
        "nn": ("TPH", "-PB"),
        "pp": ("P", "-P"),
        "rr": ("R", "-R"),
        "ss": ("S", "-S", "-F", "-Z", "SH", "-RB"),
        "tt": ("T", "-T"),
        "vv": ("SR", "-F"),
        "xx": ("KP", "-BGS", "-BG/S"),
        "zz": ("STKPW", "-Z", "-F"),

        "tion": ("-GS",),
        "cian": ("-GS",),
        "ction": ("-BGS",),
        "nction": ("-PBGS",),
    }).items()
}
"""A list of what counts as a "match" when matching characters to keys."""

class _Cost(NamedTuple):
    n_unmatched_chars: int
    """The total number of unmatched characters in the translation using this cell's alignment."""
    n_unmatched_keys: int
    """The total number of unmatched keys in the outline using this cell's alignment."""
    n_chunks: int
    

@aligner
class match_chars_to_chords(AlignmentService, ABC):
    MAPPINGS = _GRAPHEME_TO_STENO_MAPPINGS

    @staticmethod
    def process_input(translation: str, outline_steno: str) -> tuple[str, tuple[AsteriskableKey, ...]]:
        return (translation, AsteriskableKey.annotations_from_outline(outline_steno))
    
    @staticmethod
    def initial_cost():
        return _Cost(0, 0, 0)
    
    @staticmethod
    def mismatch_cost(mismatch_parent: Cell[_Cost, tuple[bool, ...]], increment_x: bool, increment_y: bool):
        return _Cost(
            mismatch_parent.cost.n_unmatched_chars + (1 if increment_x else 0),
            mismatch_parent.cost.n_unmatched_keys + (1 if increment_y else 0),
            mismatch_parent.cost.n_chunks + 1 if mismatch_parent.has_match else mismatch_parent.cost.n_chunks,
        )
    
    @staticmethod
    def is_match(actual_chord: tuple[AsteriskableKey, ...], candidate_chord: tuple[AsteriskableKey, ...]):
        return (
            tuple(key.key for key in actual_chord) == tuple(key.key for key in candidate_chord)
            and all(
                not canidate_key.asterisk or actual_key.asterisk
                for actual_key, canidate_key in zip(actual_chord, candidate_chord)
            )
        )
    
    @staticmethod
    def match_cost(parent: Cell[_Cost, tuple[bool, ...]]):
        return _Cost(
            parent.cost.n_unmatched_chars,
            parent.cost.n_unmatched_keys,
            parent.cost.n_chunks + 1,
        )
    
    @staticmethod
    def match_data(subseq_chars: str, subseq_keys: tuple[AsteriskableKey, ...], pre_subseq_chars: str, pre_subseq_keys: tuple[AsteriskableKey, ...]):
        return tuple(key.asterisk for key in subseq_keys)

    @staticmethod
    def construct_match(translation: str, keys: tuple[AsteriskableKey, ...], start_cell: Cell[_Cost, tuple[bool, ...]], end_cell: Cell[_Cost, tuple[bool, ...]], asterisk_matches: "tuple[bool, ...] | None"):
        return AnnotatedChord(
            data=translation[start_cell.x:end_cell.x],
            chord=AnnotatedChord.keys_to_strokes((key.key for key in keys[start_cell.y:end_cell.y]), asterisk_matches or (False,) * (end_cell.y - start_cell.y)),
        )