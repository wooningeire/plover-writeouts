from dataclasses import dataclass
from abc import ABC
from typing import Generator, NamedTuple, cast
from itertools import cycle

from plover.steno import Stroke

from .Stenophoneme import Stenophoneme
from .steno_annotations import AsteriskableKey, AnnotatedChord
from .alignment import AlignmentService, Cell, aligner

_KEYSYMBOL_TO_GRAPHEME_MAPPINGS = {
    tuple(keysymbol.split(" ")): graphemes
    for keysymbol, graphemes in {
        "p": ("p", "pp"),
        "t": ("t", "tt"),
        "?": (),  # glottal stop
        "t^": ("r", "rr"),  # tapped R
        "k": ("k", "c", "ck", "cc", "q", "cq"),
        "x": ("k", "c", "ck", "cc"),
        "b": ("b", "bb"),
        "d": ("d", "dd"),
        "g": ("g", "gg"),
        "ch": ("ch", "t"),
        "jh": ("j", "g"),
        "s": ("s", "c", "sc"),
        "z": ("z", "s"),
        "sh": ("sh", "ti", "ci", "si"),
        "zh": ("sh", "zh", "j", "g", "si", "ti", "ci"),
        "f": ("f", "ph", "ff"),
        "v": ("v",),
        "th": ("th",),
        "dh": ("th",),
        "h": ("h",),
        "m": ("m", "mm"),
        "m!": ("m", "mm"),
        "n": ("n", "nn"),
        "n!": ("n", "nn"),
        "ng": ("n", "ng"),
        "l": ("l", "ll"),
        "ll": ("l", "ll"),
        "lw": ("l", "ll"),
        "l!": ("l", "ll"),
        "r": ("r", "rr"),
        "y": ("y",),
        "w": ("w",),
        "hw": ("w",),

        "e": ("e", "ea"),
        "ao": ("a",),
        "a": ("a", "aa"),
        "ah": ("a",),
        "oa": ("a",),
        "aa": ("a", "au", "aw"),
        "ar": ("a", "aa"),
        "eh": ("a",),
        "ou": ("o", "oe", "oa", "ou", "ow"),
        "ouw": ("o", "oe", "oa", "ou", "ow"),
        "oou": ("o", "oe", "oa", "ou", "ow"),
        "o": ("o", "a", "ou", "au", "ow", "aw"),
        "au": ("o", "a", "ou", "au", "ow", "aw"),
        "oo": ("o", "a", "ou", "au", "ow", "aw"),
        "or": ("o", "a", "ou", "au", "ow", "aw"),
        "our": ("o", "a", "ou", "au", "ow", "aw"),
        "ii": ("e", "i", "ee", "ea", "ie", "ei"),
        "iy": ("i", "y", "ey", "ei"),
        "i": ("i", "y"),
        "@r": ("a", "o", "e", "u", "i", "y", "au", "ou"),
        "@": ("a", "o", "e", "u", "i", "y", "au", "ou"),
        "uh": ("u",),
        "u": ("u", "o", "oo"),
        "uu": ("u", "uu", "oo", "ew", "eu"),
        "iu": ("u", "uu", "oo", "ew", "eu"),
        "ei": ("ai", "ei", "a", "e"),
        "ee": ("ai", "ei", "a", "e"),
        "ai": ("i", "ie", "y", "ye"),
        "ae": ("i", "ie", "y", "ye"),
        "aer": ("i", "ie", "y", "ye"),
        "aai": ("i", "ie", "y", "ye"),
        "oi": ("oi", "oy"),
        "oir": ("oi", "oy"),
        "ow": ("ou", "ow", "ao"),
        "owr": ("ou", "ow", "ao"),
        "oow": ("ou", "ow", "ao"),
        "ir": ("e", "ee", "ea", "ie", "ei", "i", "y", "ey"),
        "@@r": ("a", "e", "i", "o", "u", "y", "au", "ou"),
        "er": ("e",),
        "eir": ("ai", "ei", "a", "e"),
        "ur": ("u", "o", "oo"),
        "i@": ("ia", "ie", "io", "iu"),

        "t s": ("z",),
        "k s": ("x",),
    }.items()
}


_STENO_CLUSTER_TO_KEYSYMBOL_MAPPINGS = {
    "sh n": "-GS",
    "k sh n": "-BGS",
    "k s": "KP",
    

}

# _GRAPHEME_TO_STENOPHONEME_MAPPINGS = {
#     grapheme: sorted(
#         tuple(AsteriskableKey.annotations_from_outline(outline_steno) for outline_steno in outline_stenos),
#         key=lambda keys: len(keys), reverse=True
#     )
#     for grapheme, outline_stenos in cast(dict[str, tuple[str, ...]], {
#         # Does not need to be fully complete to be effective

#         "": ((None, "KWR"), (None, "W")),

#         "a": ("A", "AEU", "AU"),
#         "b": _mappings(Stenophoneme.B),
#         "c": (*_mappings(Stenophoneme.S), *_mappings(Stenophoneme.K), *_mappings(Stenophoneme.SH), *_mappings(Stenophoneme.CH), (Stenophoneme.S, "KR"),),
#         "d": _mappings(Stenophoneme.D),
#         "e": ("E", "AOE", "AEU", "E/KWR", "AOE/KWR", "AEU/KWR"),
#         "f": _mappings(Stenophoneme.F),
#         "g": (*_mappings(Stenophoneme.G), *_mappings(Stenophoneme.J)),
#         "h": _mappings(Stenophoneme.H),
#         "i": ("EU", "AOEU", "EU/KWR", "AOEU/KWR"),
#         "j": ("SKWR", "-PBLG", "-G"),
#         "k": ("K", "-BG", "*G"),
#         "l": ("HR", "-L"),
#         "m": ("PH", "-PL"),
#         "n": ("TPH", "-PB"),
#         "o": ("O", "OE", "O/W", "OE/W"),
#         "p": ("P", "-P"),
#         "q": ("K", "-BG"),
#         "r": ("R", "-R"),
#         "s": ("S", "-S", "-F", "-Z", "SH", "-RB"),
#         "t": ("T", "-T", "SH", "-RB", "KH", "-FP"),
#         "u": ("U", "W", "AOU", "U/W", "AOU/W", "KWRU", "KWRAOU", "KWRU/W", "KWRAOU/W"),
#         "v": ("SR", "-F"),
#         "w": ("W", "U"),
#         "x": ("KP", "-BGS", "-BG/S"),
#         "y": ("KWH", "EU", "AOEU", "EU/KWR", "AOEU/KWR"),
#         "z": ("STKPW", "-Z", "-F"),

#         "th": ("TH", "*T"),
#         "sh": ("SH", "-RB"),
#         "ch": ("KH", "-FP"),

#         "aa": ("A", "AU"),
#         "ee": ("AOE",),
#         "ii": ("AOE", "EU"),
#         "oo": ("AO",),
#         "ou": ("U",),
#         "ea": ("AOE", "AE"),
#         "ae": ("AE", "AEU"),
#         "ai": ("AEU", "AOEU"),
#         "ay": ("AEU", "AOEU"),
#         "au": ("AU",),
#         "aw": ("AU",),
#         "oi": ("OEU",),
#         "oy": ("OEU",),
#         "ou": ("OU",),
#         "ow": ("OU",),
#         "ei": ("AOE", "E"),
#         "ey": ("AOE", "E"),
#         "ie": ("AOE", "E"),

#         "dg": ("SKWR", "-PBLG"),
#         "ck": ("K", "-BG"),
#         "ti": ("SH", "-RB", "-RB/KWR"),
#         "ci": ("SH", "-RB", "-RB/KWR"),
#         "mp": ("*PL",),
#         "sc": _mappings(Stenophoneme.S),

#         "bb": ("PW", "-B"),
#         "cc": ("S", "K", "KR", "-BG", "-S"),
#         "dd": ("TK", "-D"),
#         "ff": ("TP", "-F"),
#         "gg": ("SKWR", "TKPW", "-PBLG", "-G"),
#         "jj": ("SKWR", "-PBLG", "-G"),
#         "kk": ("K", "-BG", "*G"),
#         "ll": ("HR", "-L"),
#         "mm": ("PH", "-PL"),
#         "nn": ("TPH", "-PB"),
#         "pp": ("P", "-P"),
#         "rr": ("R", "-R"),
#         "ss": ("S", "-S", "-F", "-Z", "SH", "-RB"),
#         "tt": ("T", "-T"),
#         "vv": ("SR", "-F"),
#         "xx": ("KP", "-BGS", "-BG/S"),
#         "zz": ("STKPW", "-Z", "-F"),

#         "tion": ("-GS",),
#         "cian": ("-GS",),
#         "ction": ("-BGS",),
#         "nction": ("-PBGS",),
#     }).items()
# }
# """A list of what counts as a "match" when matching characters to keys."""


_PHONEME_TO_STENO_MAPPINGS = {
    Stenophoneme.B: ("PW", "-B"),
    Stenophoneme.D: ("TK", "-D"),
    Stenophoneme.F: ("TP", "-F"),
    Stenophoneme.G: ("SKWR", "TKPW", "-PBLG", "-G"),
    Stenophoneme.H: ("H",),
    Stenophoneme.J: ("SKWR", "-PBLG", "-G"),
    Stenophoneme.K: ("K", "-BG", "*G"),
    Stenophoneme.L: ("HR", "-L"),
    Stenophoneme.M: ("PH", "-PL"),
    Stenophoneme.N: ("TPH", "-PB"),
    Stenophoneme.P: ("P", "-P"),
    Stenophoneme.R: ("R", "-R"),
    Stenophoneme.S: ("S", "-S", "-F", "-Z", "KR"),
    Stenophoneme.T: ("T", "-T", "SH", "-RB", "KH", "-FP"),
    Stenophoneme.V: ("SR", "-F"),
    Stenophoneme.W: ("W", "U"),
    Stenophoneme.Y: ("KWH", "KWR"),
    Stenophoneme.Z: ("STKPW", "-Z", "-F", "S", "-S"),

    Stenophoneme.TH: ("TH", "*T"),
    Stenophoneme.SH: ("SH", "-RB"),
    Stenophoneme.CH: ("KH", "-FP"),

    Stenophoneme.NG: ("-PB", "-PBG"),

    Stenophoneme.AA: ("A", "AEU", "AE"),
    Stenophoneme.A: ("A", "AE"),
    Stenophoneme.EE: ("AOE", "EU", "E"),
    Stenophoneme.E: ("E", "AEU"),
    Stenophoneme.II: ("AOEU",),
    Stenophoneme.I: ("EU",),
    Stenophoneme.OO: ("OE", "AU", "O"),
    Stenophoneme.O: ("AU", "O"),
    Stenophoneme.UU: ("AOU", "U", "AO"),
    Stenophoneme.U: ("U", "AO"),
    Stenophoneme.OI: ("OEU",),
    Stenophoneme.OU: ("OU", "AO"),
}

@dataclass(frozen=True)
class _Mapping:
    phoneme: "Stenophoneme | str | None"
    keys: tuple[AsteriskableKey, ...]

_mappings = lambda phoneme: tuple(zip(cycle((phoneme,)), _PHONEME_TO_STENO_MAPPINGS[phoneme]))
_vowels = lambda *phonemes: tuple(zip(phonemes, phonemes))
_no_phoneme = lambda stenos: tuple(zip(cycle((None,)), stenos))

_any_vowel_mapping = (
    (Stenophoneme.A, "A"),
    (Stenophoneme.O, "O"),
    (Stenophoneme.E, "E"),
    (Stenophoneme.U, "U"),
    (Stenophoneme.U, "AO"),
    (Stenophoneme.AA, "AE"),
    (Stenophoneme.AU, "AU"),
    (Stenophoneme.OO, "OE"),
    (Stenophoneme.OU, "OU"),
    (Stenophoneme.I, "EU"),
    (Stenophoneme.EE, "AOE"),
    (Stenophoneme.UU, "AOU"),
    (Stenophoneme.AA, "AEU"),
    (Stenophoneme.OI, "OEU"),
    (Stenophoneme.II, "AOEU"),
)

_KEYSYMBOL_TO_STENO_MAPPINGS = {
    tuple(keysymbol.split(" ")): sorted(
        tuple(_Mapping(phoneme, AsteriskableKey.annotations_from_outline(outline_steno)) for phoneme, outline_steno in mapping),
        key=lambda mapping: len(mapping.keys),
        reverse=True,
    )
    for keysymbol, mapping in cast(dict[str, tuple[tuple[Stenophoneme | str, str], ...]], {
        # How does each keysymbol appear as it does in Lapwing?

        "p": _mappings(Stenophoneme.P),
        "t": _mappings(Stenophoneme.T),
        "?": (),  # glottal stop
        "t^": (*_mappings(Stenophoneme.T), *_mappings(Stenophoneme.R)),  # tapped R
        "k": _mappings(Stenophoneme.K),
        "x": _mappings(Stenophoneme.K),
        "b": _mappings(Stenophoneme.B),
        "d": _mappings(Stenophoneme.D),
        "g": _mappings(Stenophoneme.G),
        "ch": _mappings(Stenophoneme.CH),
        "jh": _mappings(Stenophoneme.J),
        "s": _mappings(Stenophoneme.S),
        "z": _mappings(Stenophoneme.Z),
        "sh": _mappings(Stenophoneme.SH),
        "zh": (*_mappings(Stenophoneme.SH), *_mappings(Stenophoneme.J)),
        "f": _mappings(Stenophoneme.F),
        "v": _mappings(Stenophoneme.V),
        "th": _mappings(Stenophoneme.TH),
        "dh": _mappings(Stenophoneme.TH),
        "h": _mappings(Stenophoneme.H),
        "m": _mappings(Stenophoneme.M),
        "m!": _mappings(Stenophoneme.M),
        "n": _mappings(Stenophoneme.N),
        "n!": _mappings(Stenophoneme.N),
        "ng": _mappings(Stenophoneme.NG),
        "l": _mappings(Stenophoneme.L),
        "ll": _mappings(Stenophoneme.L),
        "lw": _mappings(Stenophoneme.L),
        "l!": _mappings(Stenophoneme.L),
        "r": _mappings(Stenophoneme.R),
        "y": _mappings(Stenophoneme.Y),
        "w": _mappings(Stenophoneme.W),
        "hw": _mappings(Stenophoneme.W),

        "e": (*_mappings(Stenophoneme.E), *_mappings(Stenophoneme.EE), *_mappings(Stenophoneme.AA)),
        "ao": (*_mappings(Stenophoneme.A), *_mappings(Stenophoneme.AA), *_mappings(Stenophoneme.O), *_mappings(Stenophoneme.U)),
        "a": (*_mappings(Stenophoneme.A), *_mappings(Stenophoneme.AA)),
        "ah": _mappings(Stenophoneme.O),
        "oa": (*_mappings(Stenophoneme.A), *_mappings(Stenophoneme.O), *_mappings(Stenophoneme.U)),
        "aa": _mappings(Stenophoneme.O),
        "ar": _mappings(Stenophoneme.A),
        "eh": _mappings(Stenophoneme.A),
        "ou": _mappings(Stenophoneme.OO),
        "ouw": _mappings(Stenophoneme.OO),
        "oou": _mappings(Stenophoneme.OO),
        "o": _mappings(Stenophoneme.O),
        "au": (*_mappings(Stenophoneme.O), *_mappings(Stenophoneme.A)),
        "oo": _mappings(Stenophoneme.O),
        "or": _mappings(Stenophoneme.O),
        "our": _mappings(Stenophoneme.O),
        "ii": _mappings(Stenophoneme.EE),
        "iy": _mappings(Stenophoneme.EE),
        "i": (*_mappings(Stenophoneme.I), *_mappings(Stenophoneme.EE)),
        "@r": _any_vowel_mapping,
        "@": _any_vowel_mapping,
        "uh": _mappings(Stenophoneme.U),
        "u": (*_mappings(Stenophoneme.U), *_mappings(Stenophoneme.O), *_mappings(Stenophoneme.OO)),
        "uu": _mappings(Stenophoneme.UU),
        "iu": _mappings(Stenophoneme.UU),
        "ei": (*_mappings(Stenophoneme.E), *_mappings(Stenophoneme.AA)),
        "ee": (*_mappings(Stenophoneme.E), *_mappings(Stenophoneme.AA), *_mappings(Stenophoneme.A)),
        "ai": _mappings(Stenophoneme.II),
        "ae": _mappings(Stenophoneme.II),
        "aer": _mappings(Stenophoneme.II),
        "aai": _mappings(Stenophoneme.II),
        "oi": _mappings(Stenophoneme.OI),
        "oir": _mappings(Stenophoneme.OI),
        "ow": _mappings(Stenophoneme.OU),
        "owr": _mappings(Stenophoneme.OU),
        "oow": _mappings(Stenophoneme.OU),
        "ir": _mappings(Stenophoneme.EE),
        "@@r": _any_vowel_mapping,
        "er": (*_mappings(Stenophoneme.E), *_mappings(Stenophoneme.U)),
        "eir": _mappings(Stenophoneme.E),
        "ur": (*_mappings(Stenophoneme.U), *_mappings(Stenophoneme.UU)),
        "i@": _vowels("KWRA", "KWRO", "KWRE", "KWRU", "KWREU", "KWHA", "KWHO", "KWHE", "KWHU", "KWHEU"),
        
        "k s": _no_phoneme("KP",),
        "sh n": _no_phoneme("-GS",),
        "zh n": _no_phoneme("-GS",),
        "k sh n": _no_phoneme("-BGS",),
        "k zh n": _no_phoneme("-BGS",),
        "m p": _no_phoneme("*PL"),
    }).items()
}

class _Cost(NamedTuple):
    n_unmatched_keysymbols: int
    n_unmatched_chars: int
    n_chunks: int

@dataclass(frozen=True)
class Orthokeysymbol:
    keysymbols: tuple[str, ...]
    chars: str

    def __str__(self):
        keysymbols_string = " ".join(self.keysymbols)
        if len(self.keysymbols) > 1:
            keysymbols_string = f"({keysymbols_string})"

        return f"{self.chars}.{keysymbols_string}"
    
    __repr__ = __str__


@aligner
class _match_chars_to_keysymbols(AlignmentService, ABC):
    MAPPINGS = _KEYSYMBOL_TO_GRAPHEME_MAPPINGS
    
    @staticmethod
    def initial_cost():
        return _Cost(0, 0, 0)
    
    @staticmethod
    def mismatch_cost(mismatch_parent: Cell[_Cost, None], increment_x: bool, increment_y: bool):
        return _Cost(
            mismatch_parent.cost.n_unmatched_keysymbols + (1 if increment_x else 0),
            mismatch_parent.cost.n_unmatched_chars + (1 if increment_y else 0),
            mismatch_parent.cost.n_chunks + 1 if mismatch_parent.has_match else mismatch_parent.cost.n_chunks,
        )
    
    @staticmethod
    def is_match(actual_chars: str, candidate_chars: str):
        return actual_chars == candidate_chars
    
    @staticmethod
    def match_cost(parent: Cell[_Cost, None]):
        return _Cost(
            parent.cost.n_unmatched_keysymbols,
            parent.cost.n_unmatched_chars,
            parent.cost.n_chunks + 1,
        )
    
    @staticmethod
    def match_data(subseq_keysymbols: tuple[str, ...], subseq_chars: str, pre_subseq_keysymbols: tuple[str, ...], pre_subseq_chars: str):
        return None

    @staticmethod
    def construct_match(keysymbols: tuple[str, ...], translation: str, start_cell: Cell[_Cost, None], end_cell: Cell[_Cost, None], _: None):
        return Orthokeysymbol(
            keysymbols[start_cell.x:end_cell.x],
            translation[start_cell.y:end_cell.y],
        )


_NONPHONETIC_KEYSYMBOLS = tuple("*~-.<>{}#=$")

def match_transcription_to_chars(transcription: str, translation: str):
    phonetic_keysymbols = []
    for keysymbol in transcription.split(" "):
        if len(keysymbol) == 0: continue
        if any(ch in keysymbol for ch in _NONPHONETIC_KEYSYMBOLS): continue

        phonetic_keysymbols.append(keysymbol.replace("[", "").replace("]", ""))
    return _match_chars_to_keysymbols(tuple(phonetic_keysymbols), translation)



@dataclass(frozen=True)
class Sopheme:
    orthokeysymbols: tuple[Orthokeysymbol, ...]
    steno: tuple[Stroke, ...]
    phoneme: "Stenophoneme | str | None"

    def __str__(self):
        out = " ".join(str(orthokeysymbol) for orthokeysymbol in self.orthokeysymbols)
        if len(self.orthokeysymbols) > 1 and self.phoneme is not None:
            out = f"({out})"

        if self.phoneme is not None:
            out += f"[{self.phoneme}]"
        elif len(self.steno) > 0:
            out += f"[[{'/'.join(stroke.rtfcre for stroke in self.steno)}]]"
            
        return out
    
    __repr__ = __str__

@aligner
class _match_orthokeysymbols_to_keys(AlignmentService, ABC):
    MAPPINGS = _KEYSYMBOL_TO_STENO_MAPPINGS
    
    @staticmethod
    def initial_cost():
        return _Cost(0, 0, 0)
    
    @staticmethod
    def mismatch_cost(mismatch_parent: Cell[_Cost, None], increment_x: bool, increment_y: bool):
        return _Cost(
            mismatch_parent.cost.n_unmatched_keysymbols + (1 if increment_x else 0),
            mismatch_parent.cost.n_unmatched_chars + (1 if increment_y else 0),
            mismatch_parent.cost.n_chunks + 1 if mismatch_parent.has_match else mismatch_parent.cost.n_chunks,
        )
    
    @staticmethod
    def generate_candidate_x_key(candidate_subseq_x: tuple[Orthokeysymbol, ...]) -> tuple[str, ...]:
        keysymbols = []

        if len(candidate_subseq_x) > 0 and len(candidate_subseq_x[0].keysymbols) == 0:
            keysymbols.append("")

        for orthokeysymbol in candidate_subseq_x:
            for keysymbol in orthokeysymbol.keysymbols:
                keysymbols.append(keysymbol)

        if len(candidate_subseq_x) > 0 and len(candidate_subseq_x[-1].keysymbols) == 0:
            keysymbols.append("")

        return tuple(keysymbols)
    
    @staticmethod
    def generate_candidate_y_key(mapping: _Mapping) -> tuple[AsteriskableKey, ...]:
        return tuple(key for key in mapping.keys)
    
    @staticmethod
    def y_seq_len(candidate_y: _Mapping) -> int:
        return len(candidate_y.keys)
    
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
    def match_cost(parent: Cell[_Cost, None]):
        return _Cost(
            parent.cost.n_unmatched_keysymbols,
            parent.cost.n_unmatched_chars,
            parent.cost.n_chunks + 1,
        )
    
    @staticmethod
    def match_data(subseq_keysymbols: tuple[str, ...], subseq_keys: tuple[AsteriskableKey, ...], pre_subseq_keysymbols: tuple[Orthokeysymbol, ...], pre_subseq_keys: _Mapping):
        return (
            tuple(key.asterisk for key in subseq_keys),
            pre_subseq_keys.phoneme,
        )

    @staticmethod
    def construct_match(orthokeysymbols: tuple[Orthokeysymbol, ...], keys: tuple[AsteriskableKey, ...], start_cell: Cell[_Cost, None], end_cell: Cell[_Cost, None], match_data: "tuple[tuple[bool, ...], Stenophoneme | str] | None"):
        return Sopheme(
            orthokeysymbols[start_cell.x:end_cell.x],
            AnnotatedChord.keys_to_strokes((key.key for key in keys[start_cell.y:end_cell.y]), match_data[0] if match_data is not None else (False,) * (end_cell.y - start_cell.y)),
            match_data[1] if match_data is not None else None,
        )

def match_orthokeysymbols_to_chords(orthokeysymbols: tuple[Orthokeysymbol, ...], outline_steno: str):
    return _match_orthokeysymbols_to_keys(orthokeysymbols, AsteriskableKey.annotations_from_outline(outline_steno))


def match_sophemes(translation: str, transcription: str, outline_steno: str):
    orthokeysymbols = match_transcription_to_chars(transcription, translation)
    return match_orthokeysymbols_to_chords(orthokeysymbols, outline_steno)