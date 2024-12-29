from abc import ABC

from plover.steno import Stroke

from .spec import TheorySpec
from .service import TheoryService

from ..stenophoneme.Stenophoneme import Stenophoneme


@TheoryService.theory
class amphitheory(TheorySpec, ABC):
    ALL_KEYS = Stroke.from_steno("@STKPWHRAO*EUFRPBLGTSDZ")


    LEFT_BANK_CONSONANTS_SUBSTROKE = Stroke.from_steno("@STKPWHR")
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

            Stenophoneme.NG: "TPH",
        }.items()
    }

    PHONEMES_TO_CHORDS_VOWELS: dict[Stenophoneme, Stroke] = {
        phoneme: Stroke.from_steno(steno)
        for phoneme, steno in {
            Stenophoneme.AA: "AEU",
            Stenophoneme.A: "A",
            Stenophoneme.EE: "AOE",
            Stenophoneme.E: "E",
            Stenophoneme.II: "AOEU",
            Stenophoneme.I: "EU",
            Stenophoneme.OO: "OE",
            Stenophoneme.O: "O",
            Stenophoneme.UU: "AOU",
            Stenophoneme.U: "U",
            Stenophoneme.AU: "AU",
            Stenophoneme.OI: "OEU",
            Stenophoneme.OU: "OU",
            Stenophoneme.AE: "AE",
            Stenophoneme.AO: "AO",
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
    INITIAL_VOWEL_CHORD = Stroke.from_steno("@")

    CYCLER_STROKE = Stroke.from_steno("@")
    # CYCLER_STROKE_BACKWARD = Stroke.from_steno("+*")

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
            (Stenophoneme.E, Stenophoneme.K, Stenophoneme.S): "SKW",
            (Stenophoneme.E, Stenophoneme.K, Stenophoneme.S, Stenophoneme.T): "STKW",
            (Stenophoneme.E, Stenophoneme.K, Stenophoneme.S, Stenophoneme.K): "SKW",
            (Stenophoneme.E, Stenophoneme.K, Stenophoneme.S, Stenophoneme.P): "SKPW",
            (Stenophoneme.ANY_VOWEL, Stenophoneme.N): "TPH",
            (Stenophoneme.ANY_VOWEL, Stenophoneme.N, Stenophoneme.S): "STPH",
            (Stenophoneme.ANY_VOWEL, Stenophoneme.N, Stenophoneme.F): "TPW",
            (Stenophoneme.ANY_VOWEL, Stenophoneme.N, Stenophoneme.V): "TPW",
            (Stenophoneme.ANY_VOWEL, Stenophoneme.M): "PH",
        }.items()
    }


    DIPHTHONG_TRANSITIONS_BY_FIRST_VOWEL: dict[Stenophoneme, Stenophoneme] = {
        prev_vowel_phoneme: phoneme
        for prev_vowel_phoneme, phoneme in {
            Stenophoneme.E: Stenophoneme.Y,
            Stenophoneme.OO: Stenophoneme.W,
            Stenophoneme.OU: Stenophoneme.W,
            Stenophoneme.I: Stenophoneme.Y,
            Stenophoneme.EE: Stenophoneme.Y,
            Stenophoneme.UU: Stenophoneme.W,
            Stenophoneme.AA: Stenophoneme.Y,
            Stenophoneme.OI: Stenophoneme.Y,
            Stenophoneme.II: Stenophoneme.Y,
        }.items()
    }

    class TransitionCosts(TheorySpec.TransitionCosts, ABC):
        VOWEL_ELISION = 5
        CLUSTER = 2
        ALT_CONSONANT = 3