from abc import ABC

from plover.steno import Stroke

from .spec import TheorySpec
from .service import TheoryService
from ..stenophoneme.Stenophoneme import Stenophoneme

@TheoryService.theory
class lapwing(TheorySpec, ABC):
    ALL_KEYS = Stroke.from_steno("STKPWHRAO*EUFRPBLGTSDZ")


    LEFT_BANK_CONSONANTS_SUBSTROKE = Stroke.from_steno("STKPWHR")
    VOWELS_SUBSTROKE = Stroke.from_steno("AOEU")
    RIGHT_BANK_CONSONANTS_SUBSTROKE = Stroke.from_steno("-FRPBLGTSDZ")
    ASTERISK_SUBSTROKE = Stroke.from_steno("*")

    PHONEMES_TO_CHORDS_LEFT = {
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

    PHONEMES_TO_CHORDS_VOWELS = {
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

    LINKER_CHORD = Stroke.from_steno("KWR")
    INITIAL_VOWEL_CHORD = None

    CYCLER_STROKE = Stroke.from_steno("#TPHEGT")
    # CYCLER_STROKE_BACKWARD = Stroke.from_steno("+*")

    PROHIBITED_STROKES = set()

    CLUSTERS = {}

    VOWEL_CONSCIOUS_CLUSTERS = {}


    DIPHTHONG_TRANSITIONS_BY_FIRST_VOWEL = {}

    class TransitionCosts(TheorySpec.TransitionCosts, ABC):
        VOWEL_ELISION = 0
        CLUSTER = 0
        ALT_CONSONANT = 0

