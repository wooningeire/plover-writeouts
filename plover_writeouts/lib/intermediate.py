from dataclasses import dataclass
from typing import Iterable, cast

from plover.steno import Stroke

from .util import can_add_stroke_on

_ASTERISK_SUBSTROKE = Stroke.from_steno("*")
    
@dataclass(frozen=True)
class _AnnotatedKey:
    key: str
    asterisk: bool

    @staticmethod
    def annotations_from_outline(outline_steno: str):
        return tuple(
            _AnnotatedKey(key, has_asterisk)
            for stroke, has_asterisk in (
                (stroke - _ASTERISK_SUBSTROKE, _ASTERISK_SUBSTROKE in stroke)
                for stroke in (
                    Stroke.from_steno(steno)
                    for steno in outline_steno.split("/")
                )
            )
            for key in stroke.keys() 
        )

_GRAPHEME_TO_STENO_MAPPINGS = {
    grapheme: sorted(
        tuple(_AnnotatedKey.annotations_from_outline(outline_steno) for outline_steno in outline_stenos),
        key=lambda keys: len(keys), reverse=True
    )
    for grapheme, outline_stenos in cast(dict[str, tuple[str, ...]], {
        # Does not need to be fully complete to be effective

        "": ("KWR", "W"),

        "a": ("A", "AEU", "AU"),
        "b": ("PW", "-B"),
        "c": ("S", "K", "KR", "-BG", "-S"),
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
        "s": ("S", "-S", "-F", "-Z"),
        "t": ("T", "-T"),
        "u": ("U", "AOU", "U/W", "AOU/W"),
        "v": ("SR", "-F"),
        "w": ("W", "U"),
        "x": ("KP", "-BGS", "-BG/S"),
        "y": ("KWH", "EU", "AOEU", "EU/KWR", "AOEU/KWR"),
        "z": ("STKPW", "-Z"),

        "th": ("TH", "*T"),
        "sh": ("SH", "-RB"),
        "ch": ("KH", "-FP"),

        "oo": ("AO",),
        "ou": ("U",),
        "ea": ("AOE", "AE"),
        "ae": ("AE", "AEU"),
        "dg": ("SKWR", "-PBLG"),
        "ck": ("K", "-BG"),
        "ti": ("SH", "-RB", "-RB/KWR"),
        "ci": ("SH", "-RB", "-RB/KWR"),
        "mp": ("*PL",),

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
        "ss": ("S", "-S"),
        "tt": ("T", "-T"),
        "vv": ("SR", "-F"),
        "xx": ("KP", "-BGS", "-BG/S"),
        "zz": ("STKPW", "-Z"),
    }).items()
}
"""A list of what counts as a "match" when matching characters to keys."""

@dataclass(frozen=True)
class _Cell:
    """A cell in the Needleman–Wunsch alignment matrix; represents an optimal alignment of the first x characters in a translation to the first y keys in an outline."""

    n_unmatched_chars: int
    """The total number of unmatched characters in the translation using this cell's alignment."""
    n_unmatched_keys: int
    """The total number of unmatched characters in the translation using this cell's alignment."""

    unmatched_char_start_index: int
    """The index where the sequence of trailing unmatched characters for this alignment beigins. This specifies which characters to check when trying to find matches."""
    unmatched_key_start_index: int
    """The index where the sequence of trailing unmatched keys for this alignment beigins. This specifies which keys to check when trying to find matches."""
    
    parent: "_Cell | None"
    """The optimal sub-alignment which this alignment extends upon."""

    x: int
    y: int

    has_match: bool
    asterisk_matches: tuple[bool, ...] = ()

    @property
    def cost(self):
        return self.n_unmatched_chars + self.n_unmatched_keys * 0.5
    
@dataclass(frozen=True)
class Lexeme:
    ortho: str
    steno: tuple[Stroke, ...]
    phono: str

    def __str__(self):
        return f"{self.ortho}.{'/'.join(stroke.rtfcre for stroke in self.steno)}"
    
    __repr__ = __str__

    @staticmethod
    def keys_to_strokes(keys: Iterable[str], asterisk_matches: Iterable[bool]):
        strokes: list[Stroke] = []

        current_stroke = Stroke.from_integer(0)
        for key, asterisk_match in zip(keys, asterisk_matches):
            key_stroke = Stroke.from_keys((key,))
            if asterisk_match:
                key_stroke += _ASTERISK_SUBSTROKE

            if can_add_stroke_on(current_stroke, key_stroke):
                current_stroke += key_stroke
            else:
                strokes.append(current_stroke)
                current_stroke = key_stroke

        if len(current_stroke) > 0:
            strokes.append(current_stroke)

        return tuple(strokes)

def match_graphemes_to_writeout_chords(translation: str, outline_steno: str):
    """Generates an alignment between characters in a translation and keys in a Lapwing-style outline.
    
    Uses a variation of the Needleman–Wunsch algorithm.
    
    Assumptions:
    - Strict left-to-right parsing; no inversions
    """

    annotated_keys = _AnnotatedKey.annotations_from_outline(outline_steno)


    # Base row and column

    matrix = [[_Cell(0, 0, 0, 0, None, 0, 0, False)]]

    for i in range(len(translation)):
        matrix.append([_Cell(i + 1, 0, 0, 0, matrix[-1][0], i + 1, 0, False)])

    for i in range(len(annotated_keys)):
        matrix[0].append(_Cell(0, i + 1, 0, 0, matrix[0][-1], 0, i + 1, False))


    # Populating the matrix

    # log = []
    # l = lambda *x: log.append(" ".join(str(s) for s in x))
        
    def find_match(x: int, y: int):
        """Attempt to match any combination of the last m consecutive unmatched characters to the last n consecutive unmatched keys."""

        base = matrix[x][y]

        candidate_chars = translation[:x + 1]
        candidate_keys = annotated_keys[:y + 1]

        # l()
        # l(unmatched_chars, unmatched_keys, x, y)

        for i in reversed(range(1, len(candidate_chars) + 1)):
            grapheme = candidate_chars[-i:]
            # l("using grapheme", grapheme)
            if grapheme not in _GRAPHEME_TO_STENO_MAPPINGS: continue

            for chord in _GRAPHEME_TO_STENO_MAPPINGS[grapheme]:
                # l("testing chord", chord)
                sub_candidate_keys = candidate_keys[-len(chord):]
                if tuple(key.key for key in sub_candidate_keys) != tuple(key.key for key in chord): continue

                if any(
                    chord_key.asterisk and not candidate_key.asterisk
                    for candidate_key, chord_key in zip(sub_candidate_keys, chord)
                ): continue
                
                # l("found", grapheme, chord)
                return _Cell(
                    base.n_unmatched_chars + 1 - len(grapheme),
                    base.n_unmatched_keys + 1 - len(chord),
                    x + 1,
                    y + 1,
                    matrix[x + 1 - len(grapheme)][y + 1 - len(chord)],
                    x + 1,
                    y + 1,
                    True,
                    tuple(key.asterisk for key in chord),
                )

        # l("not found")
        return _Cell(
            base.n_unmatched_chars + 1,
            base.n_unmatched_keys + 1,
            base.unmatched_char_start_index,
            base.unmatched_key_start_index,
            base,
            x + 1,
            y + 1,
            False,
        )
    
    
    for x in range(len(translation)):
        for y in range(len(annotated_keys)):
            # Increment x: add a character from the translation
            x_base = matrix[x][y + 1]
            x_candidate = _Cell(
                x_base.n_unmatched_chars + 1,
                x_base.n_unmatched_keys,
                x_base.unmatched_char_start_index,
                x_base.unmatched_key_start_index,
                x_base,
                x + 1,
                y + 1,
                False,
            )

            # Increment y: add a key from the outline
            y_base = matrix[x + 1][y]
            y_candidate = _Cell(
                y_base.n_unmatched_chars,
                y_base.n_unmatched_keys + 1,
                y_base.unmatched_char_start_index,
                y_base.unmatched_key_start_index,
                y_base,
                x + 1,
                y + 1,
                False,
            )

            # Increment xy: both
            xy_candidate = find_match(x, y)


            matrix[x + 1].append(min(x_candidate, y_candidate, xy_candidate, key=lambda cell: cell.cost))


    # # Display the cost matrix
    # l(f".	.	{'	'.join(keys)}")
    # for r, ch in zip(matrix, f".{translation}"):
    #     l(f"{ch}	{'	'.join(str(cell.cost) for cell in r)}")
    
    # l()
    # l()

    # print("\n".join(log))
    

    # Traceback
    
    lexemes: list[Lexeme] = []

    current_cell = matrix[-1][-1]
    while current_cell.parent is not None:
        if current_cell.has_match:
            start_cell = current_cell.parent
            asterisk_matches = current_cell.asterisk_matches
        else:
            start_cell = matrix[current_cell.parent.unmatched_char_start_index][current_cell.parent.unmatched_key_start_index]
            asterisk_matches = (False,) * (current_cell.y - start_cell.y)

        lexemes.append(Lexeme(
            ortho=translation[start_cell.x:current_cell.x],
            steno=Lexeme.keys_to_strokes((key.key for key in annotated_keys[start_cell.y:current_cell.y]), asterisk_matches),
            phono="",
        ))

        current_cell = start_cell

    return tuple(reversed(lexemes))