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

    ANY_VOWEL = auto()

    EU = auto()
    AOE = auto()
    
    DUMMY = auto()


LEFT_BANK_CONSONANTS_SUBSTROKE = Stroke.from_steno("#@^+&STKPWHR")
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

PHONEMES_TO_CHORDS_LEFT_ALT: dict[Phoneme, Stroke] = {
    phoneme: Stroke.from_steno(steno)
    for phoneme, steno in {
        Phoneme.V: "W",
    }.items()
}

PHONEMES_TO_CHORDS_RIGHT_ALT: dict[Phoneme, Stroke] = {
    phoneme: Stroke.from_steno(steno)
    for phoneme, steno in {
        Phoneme.S: "-F",
        Phoneme.Z: "-F",
        Phoneme.V: "-F",
        Phoneme.TH: "-F",
        Phoneme.M: "-FR",
        Phoneme.J: "-FR",
        Phoneme.K: "*G",
    }.items()
}

LINKER_CHORD = Stroke.from_steno("SWH")
assert not (LINKER_CHORD & ~LEFT_BANK_CONSONANTS_SUBSTROKE), "Linker chord must only consist of starter keys"
INITIAL_VOWEL_CHORD: Optional[Stroke] = Stroke.from_steno("@")

VARIATION_CYCLER_STROKE = Stroke.from_steno("+TPHEGT")
# VARIATION_CYCLER_STROKE_BACKWARD = Stroke.from_steno("+*")

PROHIBITED_STROKES = {
    Stroke.from_steno(steno)
    for steno in ("AEU",)
}

CLUSTERS: dict[tuple[Phoneme, ...], Stroke] = {
    phonemes: Stroke.from_steno(steno)
    for phonemes, steno in {
        (Phoneme.D, Phoneme.S): "STK",
        (Phoneme.D, Phoneme.S, Phoneme.T): "STK",
        (Phoneme.D, Phoneme.S, Phoneme.K): "STK",
        (Phoneme.K, Phoneme.N): "K",
        (Phoneme.K, Phoneme.M, Phoneme.P): "KP",
        (Phoneme.K, Phoneme.M, Phoneme.B): "KPW",
        (Phoneme.L, Phoneme.F): "-FL",
        (Phoneme.L, Phoneme.V): "-FL",
        (Phoneme.G, Phoneme.L): "-LG",
        (Phoneme.L, Phoneme.J): "-LG",
        (Phoneme.K, Phoneme.L): "*LG",
        (Phoneme.N, Phoneme.J): "-PBG",
        (Phoneme.M, Phoneme.J): "-PLG",
        (Phoneme.R, Phoneme.F): "*FR",
        (Phoneme.R, Phoneme.S): "*FR",
        (Phoneme.R, Phoneme.V): "-FRB",
        (Phoneme.L, Phoneme.CH): "-LG",
        (Phoneme.R, Phoneme.CH): "-FRPB",
        (Phoneme.N, Phoneme.CH): "-FRPBLG",
        (Phoneme.L, Phoneme.SH): "*RB",
        (Phoneme.R, Phoneme.SH): "*RB",
        (Phoneme.N, Phoneme.SH): "*RB",
        (Phoneme.M, Phoneme.P): "*PL",
        (Phoneme.T, Phoneme.L): "-LT",
    }.items()
}

VOWEL_CONSCIOUS_CLUSTERS: "dict[tuple[Phoneme | Stroke, ...], Stroke]" = {
    tuple(
        Stroke.from_steno(phoneme) if isinstance(phoneme, str) else phoneme
        for phoneme in phonemes
    ): Stroke.from_steno(steno)
    for phonemes, steno in {
        (Phoneme.ANY_VOWEL, Phoneme.N, Phoneme.T): "SPW",
        (Phoneme.ANY_VOWEL, Phoneme.N, Phoneme.D): "SPW",
        (Phoneme.ANY_VOWEL, Phoneme.M, Phoneme.P): "KPW",
        (Phoneme.ANY_VOWEL, Phoneme.M, Phoneme.B): "KPW",
        (Phoneme.ANY_VOWEL, Phoneme.N, Phoneme.K): "SKPW",
        (Phoneme.ANY_VOWEL, Phoneme.N, Phoneme.G): "SKPW",
        (Phoneme.ANY_VOWEL, Phoneme.N, Phoneme.J): "SKPW",
        ("E", Phoneme.K, Phoneme.S): "SKW",
        ("E", Phoneme.K, Phoneme.S, Phoneme.T): "STKW",
        ("E", Phoneme.K, Phoneme.S, Phoneme.K): "SKW",
        ("E", Phoneme.K, Phoneme.S, Phoneme.P): "SKPW",
        (Phoneme.ANY_VOWEL, Phoneme.N): "TPH",
        (Phoneme.ANY_VOWEL, Phoneme.N, Phoneme.S): "STPH",
        (Phoneme.ANY_VOWEL, Phoneme.M): "PH",
    }.items()
}


DIPHTHONG_TRANSITIONS_BY_FIRST_VOWEL: dict[Stroke, Phoneme] = {
    Stroke.from_steno(steno): phoneme
    for steno, phoneme in {
        "E": Phoneme.Y,
        "OE": Phoneme.W,
        "OU": Phoneme.W,
        "EU": Phoneme.Y,
        "AOE": Phoneme.Y,
        "AOU": Phoneme.W,
        "AEU": Phoneme.Y,
        "OEU": Phoneme.Y,
        "AOEU": Phoneme.Y,
    }.items()
}


class TransitionCosts:
    VOWEL_ELISION = 5
    CLUSTER = 2
    ALT_CONSONANT = 3


TRIE_STROKE_BOUNDARY_KEY = ""
TRIE_LINKER_KEY = "-"


OPTIMIZE_TRIE_SPACE = False