from dataclasses import dataclass
from typing import cast

from plover.steno import Stroke

from .util import can_add_stroke_on, split_stroke_parts

_VOWELS = set("aeiou")

_GRAPHEME_TO_STENO_MAPPINGS = {
    grapheme: sorted(
        tuple(
            tuple(
                key
                for steno in outline_steno.split("/")
                for key in Stroke.from_steno(steno).keys() 
            )
            for outline_steno in outline_stenos
        ),
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
        "q": ("KW",),
        "r": ("R", "-R"),
        "s": ("S", "-S"),
        "t": ("T", "-T"),
        "u": ("U", "AOU", "U/W", "AOU/W"),
        "v": ("SR", "-F"),
        "w": ("W", "U"),
        "x": ("KP", "-BGS", "-BG/S"),
        "y": ("KWH", "EU"),
        "z": ("STKPW", "-Z"),

        "dg": ("SKWR", "-PBLG"),
        "oo": ("AO",),
        "ou": ("U",),
        "ea": ("AOE", "AE"),
        "ti": ("SH", "-RB/KWR"),
        "ci": ("SH", "-RB/KWR"),
    }).items()
}
"""A list of what counts as a "match" when matching characters to keys."""

@dataclass(frozen=True)
class Cell:
    """A cell in the Needleman–Wunsch alignment matrix; represents an optimal alignment of the first x characters in a translation to the first y keys in an outline."""

    n_unmatched_chars: int
    """The total number of unmatched characters in the translation using this cell's alignment."""
    n_unmatched_keys: int
    """The total number of unmatched characters in the translation using this cell's alignment."""

    unmatched_char_start_index: int
    """The index where the sequence of trailing unmatched characters for this alignment beigins. This specifies which characters to check when trying to find matches."""
    unmatched_key_start_index: int
    """The index where the sequence of trailing unmatched keys for this alignment beigins. This specifies which keys to check when trying to find matches."""
    
    parent: "Cell | None"
    """The optimal sub-alignment which this alignment extends upon."""

    x: int
    y: int

    has_match: bool

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
    def keys_to_strokes(keys: tuple[str, ...]):
        strokes: list[Stroke] = []

        current_stroke = Stroke.from_integer(0)
        for key in keys:
            key_stroke = Stroke.from_keys((key,))
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

    keys = tuple(
        key
        for stroke_steno in outline_steno.split("/")
        for key in Stroke.from_steno(stroke_steno).keys()
    )


    # Base row and column

    matrix = [[Cell(0, 0, 0, 0, None, 0, 0, False)]]

    for i in range(len(translation)):
        matrix.append([Cell(i + 1, 0, 0, 0, matrix[-1][0], i + 1, 0, False)])

    for i in range(len(keys)):
        matrix[0].append(Cell(0, i + 1, 0, 0, matrix[0][-1], 0, i + 1, False))


    # Populating the matrix

    # log = []
    # l = lambda *x: log.append(" ".join(str(s) for s in x))
        
    def find_match(x: int, y: int):
        """Attempt to match any combination of the last m consecutive unmatched characters to the last n consecutive unmatched keys."""

        base = matrix[x][y]

        candidate_chars = translation[:x + 1]
        candidate_keys = keys[:y + 1]

        # l()
        # l(unmatched_chars, unmatched_keys, x, y)

        for i in reversed(range(len(candidate_chars) + 1)):
            grapheme = candidate_chars[-i:]
            # l("using grapheme", grapheme)
            if grapheme not in _GRAPHEME_TO_STENO_MAPPINGS: continue

            for chord in _GRAPHEME_TO_STENO_MAPPINGS[grapheme]:
                # l("testing chord", chord)
                if candidate_keys[-len(chord):] != chord: continue
                
                # l("found", grapheme, chord)
                return Cell(
                    base.n_unmatched_chars + 1 - len(grapheme),
                    base.n_unmatched_keys + 1 - len(chord),
                    x + 1,
                    y + 1,
                    matrix[x + 1 - len(grapheme)][y + 1 - len(chord)],
                    x + 1,
                    y + 1,
                    True,
                )

        # l("not found")
        return Cell(
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
        for y in range(len(keys)):
            # Increment x: add a character from the translation
            x_base = matrix[x][y + 1]
            x_candidate = Cell(
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
            y_candidate = Cell(
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
        else:
            start_cell = matrix[current_cell.parent.unmatched_char_start_index][current_cell.parent.unmatched_key_start_index]

        lexemes.append(Lexeme(
            ortho=translation[start_cell.x:current_cell.x],
            steno=Lexeme.keys_to_strokes(keys[start_cell.y:current_cell.y]),
            phono="",
        ))

        current_cell = start_cell

    return tuple(reversed(lexemes))