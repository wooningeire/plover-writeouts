from abc import ABC

from plover.steno import Stroke

from ..stenophoneme.Stenophoneme import Stenophoneme

class TheorySpec(ABC):
    ALL_KEYS: Stroke


    LEFT_BANK_CONSONANTS_SUBSTROKE: Stroke
    VOWELS_SUBSTROKE: Stroke
    RIGHT_BANK_CONSONANTS_SUBSTROKE: Stroke
    ASTERISK_SUBSTROKE: Stroke


    PHONEMES_TO_CHORDS_LEFT: dict[Stenophoneme, Stroke]
    PHONEMES_TO_CHORDS_RIGHT: dict[Stenophoneme, Stroke]
    PHONEMES_TO_CHORDS_LEFT_ALT: dict[Stenophoneme, Stroke]
    PHONEMES_TO_CHORDS_RIGHT_ALT: dict[Stenophoneme, Stroke]

    LINKER_CHORD: Stroke
    INITIAL_VOWEL_CHORD: "Stroke | None" = None # Stroke.from_steno("@")

    VARIATION_CYCLER_STROKE = Stroke.from_steno("#TPHEGT") # Stroke.from_steno("+TPHEGT")
    # VARIATION_CYCLER_STROKE_BACKWARD = Stroke.from_steno("+*")

    PROHIBITED_STROKES: set[Stroke]

    CLUSTERS: dict[tuple[Stenophoneme, ...], Stroke]

    VOWEL_CONSCIOUS_CLUSTERS: "dict[tuple[Stenophoneme | Stroke, ...], Stroke]"


    DIPHTHONG_TRANSITIONS_BY_FIRST_VOWEL: dict[Stroke, Stenophoneme]


    TRIE_STROKE_BOUNDARY_KEY: str
    TRIE_LINKER_KEY: str


    OPTIMIZE_TRIE_SPACE: bool
