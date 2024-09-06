from typing import Optional

from plover.steno import Stroke

from .Stenophoneme import Stenophoneme


ALL_KEYS = Stroke.from_steno("STKPWHRAO*EUFRPBLGTSDZ")


LEFT_BANK_CONSONANTS_SUBSTROKE = Stroke.from_steno("STKPWHR") # Stroke.from_steno("#@^+&STKPWHR")
VOWELS_SUBSTROKE = Stroke.from_steno("AOEU")
RIGHT_BANK_CONSONANTS_SUBSTROKE = Stroke.from_steno("-FRPBLGTSDZ")
ASTERISK_SUBSTROKE = Stroke.from_steno("*")


PHONEMES_TO_CHORDS_LEFT: dict[Stenophoneme, Stroke] = {
    phoneme: Stroke.from_steno(steno)
    for phoneme, steno in {
        Stenophoneme.S: "S",
        Stenophoneme.T: "T",
        Stenophoneme.K: "K",
        Stenophoneme.P: "P",
        Stenophoneme.W: "W",
        Stenophoneme.H: "H",
        Stenophoneme.R: "R",

        Stenophoneme.Z: "STKPW",
        Stenophoneme.J: "SKWR",
        Stenophoneme.V: "SR",
        Stenophoneme.D: "TK",
        Stenophoneme.G: "TKPW",
        Stenophoneme.F: "TP",
        Stenophoneme.N: "TPH",
        Stenophoneme.Y: "KWR",
        Stenophoneme.B: "PW",
        Stenophoneme.M: "PH",
        Stenophoneme.L: "HR",

        Stenophoneme.SH: "SH",
        Stenophoneme.TH: "TH",
        Stenophoneme.CH: "KH",
    }.items()
}

PHONEMES_TO_CHORDS_RIGHT: dict[Stenophoneme, Stroke] = {
    phoneme: Stroke.from_steno(steno)
    for phoneme, steno in {
        Stenophoneme.DUMMY: "",

        Stenophoneme.F: "-F",
        Stenophoneme.R: "-R",
        Stenophoneme.P: "-P",
        Stenophoneme.B: "-B",
        Stenophoneme.L: "-L",
        Stenophoneme.G: "-G",
        Stenophoneme.T: "-T",
        Stenophoneme.S: "-S",
        Stenophoneme.D: "-D",
        Stenophoneme.Z: "-Z",

        Stenophoneme.V: "-FB",
        Stenophoneme.N: "-PB",
        Stenophoneme.M: "-PL",
        Stenophoneme.K: "-BG",
        Stenophoneme.J: "-PBLG",
        Stenophoneme.CH: "-FP",
        Stenophoneme.SH: "-RB",
        Stenophoneme.TH: "*T",
    }.items()

    # "SHR": "shr",
    # "THR": "thr",
    # "KHR": "chr",
    # "-FRP": (Phoneme.M, Phoneme.P),
    # "-FRB": (Phoneme.R, Phoneme.V),
}

PHONEMES_TO_CHORDS_LEFT_ALT: dict[Stenophoneme, Stroke] = {
    phoneme: Stroke.from_steno(steno)
    for phoneme, steno in {
        Stenophoneme.F: "W",
        Stenophoneme.V: "W",
        Stenophoneme.Z: "S*",
    }.items()
}

PHONEMES_TO_CHORDS_RIGHT_ALT: dict[Stenophoneme, Stroke] = {
    phoneme: Stroke.from_steno(steno)
    for phoneme, steno in {
        Stenophoneme.S: "-F",
        Stenophoneme.Z: "-F",
        Stenophoneme.V: "-F",
        Stenophoneme.TH: "-F",
        Stenophoneme.M: "-FR",
        Stenophoneme.J: "-FR",
        Stenophoneme.K: "*G",
    }.items()
}

LINKER_CHORD = Stroke.from_steno("SWH")
assert not (LINKER_CHORD & ~LEFT_BANK_CONSONANTS_SUBSTROKE), "Linker chord must only consist of starter keys"
INITIAL_VOWEL_CHORD: Optional[Stroke] = None # Stroke.from_steno("@")

VARIATION_CYCLER_STROKE = Stroke.from_steno("#TPHEGT") # Stroke.from_steno("+TPHEGT")
# VARIATION_CYCLER_STROKE_BACKWARD = Stroke.from_steno("+*")

PROHIBITED_STROKES = {
    Stroke.from_steno(steno)
    for steno in ("AEU",)
}

CLUSTERS: dict[tuple[Stenophoneme, ...], Stroke] = {
    phonemes: Stroke.from_steno(steno)
    for phonemes, steno in {
        (Stenophoneme.D, Stenophoneme.S): "STK",
        (Stenophoneme.D, Stenophoneme.S, Stenophoneme.T): "STK",
        (Stenophoneme.D, Stenophoneme.S, Stenophoneme.K): "STK",
        (Stenophoneme.K, Stenophoneme.N): "K",
        (Stenophoneme.K, Stenophoneme.M, Stenophoneme.P): "KP",
        (Stenophoneme.K, Stenophoneme.M, Stenophoneme.B): "KPW",
        (Stenophoneme.L, Stenophoneme.F): "-FL",
        (Stenophoneme.L, Stenophoneme.V): "-FL",
        (Stenophoneme.G, Stenophoneme.L): "-LG",
        (Stenophoneme.L, Stenophoneme.J): "-LG",
        (Stenophoneme.K, Stenophoneme.L): "*LG",
        (Stenophoneme.N, Stenophoneme.J): "-PBG",
        (Stenophoneme.M, Stenophoneme.J): "-PLG",
        (Stenophoneme.R, Stenophoneme.F): "*FR",
        (Stenophoneme.R, Stenophoneme.S): "*FR",
        (Stenophoneme.R, Stenophoneme.M): "*FR",
        (Stenophoneme.R, Stenophoneme.V): "-FRB",
        (Stenophoneme.L, Stenophoneme.CH): "-LG",
        (Stenophoneme.R, Stenophoneme.CH): "-FRPB",
        (Stenophoneme.N, Stenophoneme.CH): "-FRPBLG",
        (Stenophoneme.L, Stenophoneme.SH): "*RB",
        (Stenophoneme.R, Stenophoneme.SH): "*RB",
        (Stenophoneme.N, Stenophoneme.SH): "*RB",
        (Stenophoneme.M, Stenophoneme.P): "*PL",
        (Stenophoneme.T, Stenophoneme.L): "-LT",
    }.items()
}

VOWEL_CONSCIOUS_CLUSTERS: "dict[tuple[Stenophoneme | Stroke, ...], Stroke]" = {
    tuple(
        Stroke.from_steno(phoneme) if isinstance(phoneme, str) else phoneme
        for phoneme in phonemes
    ): Stroke.from_steno(steno)
    for phonemes, steno in {
        (Stenophoneme.ANY_VOWEL, Stenophoneme.N, Stenophoneme.T): "SPW",
        (Stenophoneme.ANY_VOWEL, Stenophoneme.N, Stenophoneme.D): "SPW",
        (Stenophoneme.ANY_VOWEL, Stenophoneme.M, Stenophoneme.P): "KPW",
        (Stenophoneme.ANY_VOWEL, Stenophoneme.M, Stenophoneme.B): "KPW",
        (Stenophoneme.ANY_VOWEL, Stenophoneme.N, Stenophoneme.K): "SKPW",
        (Stenophoneme.ANY_VOWEL, Stenophoneme.N, Stenophoneme.G): "SKPW",
        (Stenophoneme.ANY_VOWEL, Stenophoneme.N, Stenophoneme.J): "SKPW",
        ("E", Stenophoneme.K, Stenophoneme.S): "SKW",
        ("E", Stenophoneme.K, Stenophoneme.S, Stenophoneme.T): "STKW",
        ("E", Stenophoneme.K, Stenophoneme.S, Stenophoneme.K): "SKW",
        ("E", Stenophoneme.K, Stenophoneme.S, Stenophoneme.P): "SKPW",
        (Stenophoneme.ANY_VOWEL, Stenophoneme.N): "TPH",
        (Stenophoneme.ANY_VOWEL, Stenophoneme.N, Stenophoneme.S): "STPH",
        (Stenophoneme.ANY_VOWEL, Stenophoneme.N, Stenophoneme.F): "TPWH",
        (Stenophoneme.ANY_VOWEL, Stenophoneme.N, Stenophoneme.V): "TPWH",
        (Stenophoneme.ANY_VOWEL, Stenophoneme.M): "PH",
    }.items()
}


DIPHTHONG_TRANSITIONS_BY_FIRST_VOWEL: dict[Stroke, Stenophoneme] = {
    Stroke.from_steno(steno): phoneme
    for steno, phoneme in {
        "E": Stenophoneme.Y,
        "OE": Stenophoneme.W,
        "OU": Stenophoneme.W,
        "EU": Stenophoneme.Y,
        "AOE": Stenophoneme.Y,
        "AOU": Stenophoneme.W,
        "AEU": Stenophoneme.Y,
        "OEU": Stenophoneme.Y,
        "AOEU": Stenophoneme.Y,
    }.items()
}


class TransitionCosts:
    VOWEL_ELISION = 5
    CLUSTER = 2
    ALT_CONSONANT = 3


TRIE_STROKE_BOUNDARY_KEY = ""
TRIE_LINKER_KEY = "-"


OPTIMIZE_TRIE_SPACE = False