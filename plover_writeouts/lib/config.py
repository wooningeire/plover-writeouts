from enum import Enum, auto
from typing import Optional

from plover.steno import Stroke


class Phoneme(Enum):
    S = auto()
    T = auto()
    K = auto()
    P = auto()
    W = auto()
    H = auto()
    R = auto()

    Z = auto()
    J = auto()
    V = auto()
    D = auto()
    G = auto()
    F = auto()
    N = auto()
    Y = auto()
    B = auto()
    M = auto()
    L = auto()

    CH = auto()
    SH = auto()
    TH = auto()

    EU = auto()
    AOE = auto()
    
    DUMMY = auto()


LEFT_BANK_CONSONANTS_SUBSTROKE = Stroke.from_steno("#@^+STKPWHR")
VOWELS_SUBSTROKE = Stroke.from_steno("AOEU")
RIGHT_BANK_CONSONANTS_SUBSTROKE = Stroke.from_steno("-FRPBLGTSDZ")
ASTERISK_SUBSTROKE = Stroke.from_steno("*")


PHONEMES_TO_CHORDS_LEFT: dict[Phoneme, Stroke] = {
    phoneme: Stroke.from_steno(steno)
    for phoneme, steno in {
        Phoneme.DUMMY: "#",

        Phoneme.S: "S",
        Phoneme.T: "T",
        Phoneme.K: "K",
        Phoneme.P: "P",
        Phoneme.W: "W",
        Phoneme.H: "H",
        Phoneme.R: "R",

        Phoneme.Z: "STKPW",
        Phoneme.J: "SKWR",
        Phoneme.V: "SR",
        Phoneme.D: "TK",
        Phoneme.G: "TKPW",
        Phoneme.F: "TP",
        Phoneme.N: "TPH",
        Phoneme.Y: "KWR",
        Phoneme.B: "PW",
        Phoneme.M: "PH",
        Phoneme.L: "HR",

        Phoneme.SH: "SH",
        Phoneme.TH: "TH",
        Phoneme.CH: "KH",
    }.items()
}

PHONEMES_TO_CHORDS_RIGHT: dict[Phoneme, Stroke] = {
    phoneme: Stroke.from_steno(steno)
    for phoneme, steno in {
        Phoneme.DUMMY: "",

        Phoneme.F: "-F",
        Phoneme.R: "-R",
        Phoneme.P: "-P",
        Phoneme.B: "-B",
        Phoneme.L: "-L",
        Phoneme.G: "-G",
        Phoneme.T: "-T",
        Phoneme.S: "-S",
        Phoneme.D: "-D",
        Phoneme.Z: "-Z",

        Phoneme.V: "-FB",
        Phoneme.N: "-PB",
        Phoneme.M: "-PL",
        Phoneme.K: "-BG",
        Phoneme.J: "-PBLG",
        Phoneme.CH: "-FP",
        Phoneme.SH: "-RB",
        Phoneme.TH: "*T",
    }.items()

    # "SHR": "shr",
    # "THR": "thr",
    # "KHR": "chr",
    # "-FRP": (Phoneme.M, Phoneme.P),
    # "-FRB": (Phoneme.R, Phoneme.V),
}

PHONEMES_TO_CHORDS_RIGHT_F: dict[Phoneme, Stroke] = {
    phoneme: Stroke.from_steno(steno)
    for phoneme, steno in {
        Phoneme.S: "-F",
        Phoneme.Z: "-F",
        Phoneme.V: "-F",
        Phoneme.TH: "-F",
        Phoneme.J: "-F",
        Phoneme.M: "-FR",
    }.items()
}

LINKER_CHORD = Stroke.from_steno("SWH")
assert not (LINKER_CHORD & ~LEFT_BANK_CONSONANTS_SUBSTROKE), "Linker chord must only consist of starter keys"
# INITIAL_VOWEL_CHORD: Optional[Stroke] = Stroke.from_steno("@")

CLUSTERS: dict[tuple[Phoneme, ...], Stroke] = {
    phonemes: Stroke.from_steno(steno)
    for phonemes, steno in {
        (Phoneme.D, Phoneme.S): "STK",
        (Phoneme.D, Phoneme.S, Phoneme.K): "STK",
        (Phoneme.K, Phoneme.N): "K",
        (Phoneme.V,): "W",
        (Phoneme.L, Phoneme.F): "-FL",
        (Phoneme.L, Phoneme.V): "-FL",
        (Phoneme.G, Phoneme.L): "-LG",
        (Phoneme.L, Phoneme.J): "-LG",
        (Phoneme.L, Phoneme.K): "*LG",
        (Phoneme.K, Phoneme.L): "*LG",
        (Phoneme.N, Phoneme.J): "-PBG",
        (Phoneme.N, Phoneme.K): "*PBG",
        (Phoneme.M, Phoneme.J): "-PLG",
        (Phoneme.M, Phoneme.K): "*PLG",
        (Phoneme.R, Phoneme.F): "*FR",
        (Phoneme.R, Phoneme.S): "*FR",
        (Phoneme.R, Phoneme.V): "-FRB",
        (Phoneme.R, Phoneme.CH): "-FRPB",
        (Phoneme.N, Phoneme.CH): "-FRPBLG",
        (Phoneme.R, Phoneme.SH): "*RB",
        (Phoneme.L, Phoneme.SH): "*RB",
        (Phoneme.N, Phoneme.SH): "*RB",
        (Phoneme.M, Phoneme.P): "*PL",
        (Phoneme.T, Phoneme.L): "-LT",
    }.items()
}


TRIE_STROKE_BOUNDARY_KEY = ""
TRIE_LINKER_KEY = "-"


OPTIMIZE_TRIE_SPACE = False