from dataclasses import dataclass
from typing import Generator, Sequence, cast

from .Phoneme import Phoneme
from .steno_annotations import AnnotatedChord, AsteriskableKey


_PHONEME_TO_STENO_MAPPINGS = {
    Phoneme.B: ("PW", "-B"),
    Phoneme.D: ("TK", "-D"),
    Phoneme.F: ("TP", "-F"),
    Phoneme.G: ("SKWR", "TKPW", "-PBLG", "-G"),
    Phoneme.H: ("H",),
    Phoneme.J: ("SKWR", "-PBLG", "-G"),
    Phoneme.K: ("K", "-BG", "*G"),
    Phoneme.L: ("HR", "-L"),
    Phoneme.M: ("PH", "-PL"),
    Phoneme.N: ("TPH", "-PB"),
    Phoneme.P: ("P", "-P"),
    Phoneme.R: ("R", "-R"),
    Phoneme.S: ("S", "-S", "-F", "-Z"),
    Phoneme.T: ("T", "-T", "SH", "-RB", "KH", "-FP"),
    Phoneme.V: ("SR", "-F"),
    Phoneme.W: ("W", "U"),
    Phoneme.Y: ("KWH", "KWR"),
    Phoneme.Z: ("STKPW", "-Z", "-F"),

    Phoneme.TH: ("TH", "*T"),
    Phoneme.SH: ("SH", "-RB"),
    Phoneme.CH: ("KH", "-FP"),

    Phoneme.NG: ("-PB", "-PBG"),
}

_KEYSYMBOL_TO_STENO_MAPPINGS = {
    tuple(keysymbol.split(" ")): sorted(
        tuple(AsteriskableKey.annotations_from_outline(outline_steno) for outline_steno in outline_stenos),
        key=lambda keys: len(keys), reverse=True
    )
    for keysymbol, outline_stenos in cast(dict[str, tuple[str, ...]], {
        # How does each keysymbol appear as it does in Lapwing?

        "p": _PHONEME_TO_STENO_MAPPINGS[Phoneme.P],
        "t": _PHONEME_TO_STENO_MAPPINGS[Phoneme.T],
        "?": (),  # glottal stop
        "t^": (*_PHONEME_TO_STENO_MAPPINGS[Phoneme.T], *_PHONEME_TO_STENO_MAPPINGS[Phoneme.R]),  # tapped R
        "k": _PHONEME_TO_STENO_MAPPINGS[Phoneme.K],
        "x": _PHONEME_TO_STENO_MAPPINGS[Phoneme.K],
        "b": _PHONEME_TO_STENO_MAPPINGS[Phoneme.B],
        "d": _PHONEME_TO_STENO_MAPPINGS[Phoneme.D],
        "g": _PHONEME_TO_STENO_MAPPINGS[Phoneme.G],
        "ch": _PHONEME_TO_STENO_MAPPINGS[Phoneme.CH],
        "jh": _PHONEME_TO_STENO_MAPPINGS[Phoneme.J],
        "s": _PHONEME_TO_STENO_MAPPINGS[Phoneme.S],
        "z": _PHONEME_TO_STENO_MAPPINGS[Phoneme.Z],
        "sh": _PHONEME_TO_STENO_MAPPINGS[Phoneme.SH],
        "zh": (*_PHONEME_TO_STENO_MAPPINGS[Phoneme.SH], *_PHONEME_TO_STENO_MAPPINGS[Phoneme.J]),
        "f": _PHONEME_TO_STENO_MAPPINGS[Phoneme.F],
        "v": _PHONEME_TO_STENO_MAPPINGS[Phoneme.V],
        "th": _PHONEME_TO_STENO_MAPPINGS[Phoneme.TH],
        "dh": _PHONEME_TO_STENO_MAPPINGS[Phoneme.TH],
        "h": _PHONEME_TO_STENO_MAPPINGS[Phoneme.H],
        "m": _PHONEME_TO_STENO_MAPPINGS[Phoneme.M],
        "m!": _PHONEME_TO_STENO_MAPPINGS[Phoneme.M],
        "n": _PHONEME_TO_STENO_MAPPINGS[Phoneme.N],
        "n!": _PHONEME_TO_STENO_MAPPINGS[Phoneme.N],
        "ng": _PHONEME_TO_STENO_MAPPINGS[Phoneme.NG],
        "l": _PHONEME_TO_STENO_MAPPINGS[Phoneme.L],
        "ll": _PHONEME_TO_STENO_MAPPINGS[Phoneme.L],
        "lw": _PHONEME_TO_STENO_MAPPINGS[Phoneme.L],
        "l!": _PHONEME_TO_STENO_MAPPINGS[Phoneme.L],
        "r": _PHONEME_TO_STENO_MAPPINGS[Phoneme.R],
        "y": _PHONEME_TO_STENO_MAPPINGS[Phoneme.Y],
        "w": _PHONEME_TO_STENO_MAPPINGS[Phoneme.W],
        "hw": _PHONEME_TO_STENO_MAPPINGS[Phoneme.W],

        "e": ("E",),
        "ao": ("O", "AU",),
        "a": ("A",),
        "ah": ("A",),
        "oa": ("A",),
        "aa": ("AU",),
        "ar": ("A",),
        "eh": ("A",),
        "ou": ("OE",),
        "ouw": ("OE",),
        "oou": ("OE",),
        "o": ("O", "AU"),
        "au": ("O", "AU"),
        "oo": ("O", "AU"),
        "or": ("O", "AU"),
        "our": ("O", "AU"),
        "ii": ("AOE", "EU", "E"),
        "iy": ("AOE", "EU"),
        "i": ("EU",),
        "@r": ("A", "O", "E", "U", "EU"),
        "@": ("A", "O", "E", "U", "EU"),
        "uh": ("U",),
        "u": ("U", "AO", "O", "OE"),
        "uu": ("AOU", "AO"),
        "iu": ("AOU", "AO"),
        "ei": ("E", "AEU"),
        "ee": ("E", "AEU"),
        "ai": ("AOEU",),
        "ae": ("AOEU",),
        "aer": ("AOEU",),
        "aai": ("AOEU",),
        "oi": ("OEU",),
        "oir": ("OEU",),
        "ow": ("OU",),
        "owr": ("OU",),
        "oow": ("OU",),
        "ir": ("AOE", "EU"),
        "@@r": ("A", "O", "E", "U", "EU"),
        "er": ("E", "U"),
        "eir": ("E", "AEU"),
        "ur": ("U",),
        "i@": ("KWRA", "KWRO", "KWRE", "KWRU", "KWREU", "KWHA", "KWHO", "KWHE", "KWHU", "KWHEU"),
        "k s": ("KP",),
        "sh n": ("-GS",),
        "k sh n": ("-BGS",),
    }).items()
}

@dataclass(frozen=True)
class _Cell:
    """A cell in the Needleman–Wunsch alignment matrix; represents an optimal alignment of the first x keysymbols in a transcription to the first y keys in an outline."""

    n_unmatched_keysymbols: int
    """The total number of unmatched keysymbols in the transcription using this cell's alignment."""
    n_unmatched_keys: int
    """The total number of unmatched keys in the outline using this cell's alignment."""
    n_matchings: int

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
        return (self.n_unmatched_keys, self.n_unmatched_keysymbols, self.n_matchings)

    def __lt__(self, cell: "_Cell"):
        return self.cost < cell.cost
    
    def __gt__(self, cell: "_Cell"):
        return self.cost > cell.cost
    

def match_keysymbols_to_writeout_chords(keysymbols: Sequence[str], outline_steno: str):
    """Generates an alignment between a word's ortho–steno pairs and unilex keysymbol sequence.
    
    Uses a variation of the Needleman–Wunsch algorithm.
    """

    annotated_keys = AsteriskableKey.annotations_from_outline(outline_steno)


    def create_mismatch_cell(x: int, y: int, increment_x: bool, increment_y: bool):
        mismatch_parent = matrix[x if increment_x else x + 1][y if increment_y else y + 1]

        return _Cell(
            mismatch_parent.n_unmatched_keysymbols + (1 if increment_x else 0),
            mismatch_parent.n_unmatched_keys + (1 if increment_y else 0),
            mismatch_parent.n_matchings + 1 if mismatch_parent.has_match else mismatch_parent.n_matchings,
            mismatch_parent.unmatched_char_start_index,
            mismatch_parent.unmatched_key_start_index,
            mismatch_parent,
            x + 1,
            y + 1,
            False,
        )

    def find_match(x: int, y: int, increment_x: bool, increment_y: bool):
        """Attempt to match any combination of the last m consecutive unmatched characters to the last n consecutive unmatched keys."""

        candidate_chars = keysymbols[:x + 1]
        candidate_keys = annotated_keys[:y + 1]

        # print()
        # print(unmatched_chars, unmatched_keys, x, y)

        candidate_cells = [create_mismatch_cell(x, y, increment_x, increment_y)]


        # When not incrementing x, only consider silent chords

        for i in range((len(candidate_chars) if increment_x else 0) + 1):
            grapheme = candidate_chars[len(candidate_chars) - i:]
            # print("using grapheme", grapheme)
            if grapheme not in _KEYSYMBOL_TO_STENO_MAPPINGS: continue


            # When not incrementing y, only consider silent letters

            if increment_y:
                chords = _KEYSYMBOL_TO_STENO_MAPPINGS[grapheme]
            else:
                chords = filter(lambda chord: len(chord) == 0, _KEYSYMBOL_TO_STENO_MAPPINGS[grapheme])

            for chord in chords:
                # print("testing chord", chord)
                sub_candidate_keys = candidate_keys[len(candidate_keys) - len(chord):]
                if tuple(key.key for key in sub_candidate_keys) != tuple(key.key for key in chord): continue

                if any(
                    chord_key.asterisk and not candidate_key.asterisk
                    for candidate_key, chord_key in zip(sub_candidate_keys, chord)
                ): continue

                parent = matrix[x + 1 - len(grapheme)][y + 1 - len(chord)]
                
                # print("found", grapheme, chord)
                candidate_cells.append(
                    _Cell(
                        parent.n_unmatched_keysymbols,
                        parent.n_unmatched_keys,
                        parent.n_matchings + 1,
                        x + 1,
                        y + 1,
                        parent,
                        x + 1,
                        y + 1,
                        True,
                        tuple(key.asterisk for key in chord),
                    )
                )

        return min(candidate_cells)


    # Base row and column

    matrix = [[_Cell(0, 0, 0, 0, 0, None, 0, 0, False)]]

    for i in range(len(keysymbols)):
        matrix.append([find_match(i, -1, True, False)])

    for i in range(len(annotated_keys)):
        matrix[0].append(find_match(-1, i, False, True))


    # Populating the matrix

    for x in range(len(keysymbols)):
        for y in range(len(annotated_keys)):
            # Increment x: add a character from the translation
            x_candidate = find_match(x, y, True, False)

            # Increment y: add a key from the outline
            y_candidate = find_match(x, y, False, True)

            # Increment xy: both
            xy_candidate = find_match(x, y, True, True)


            matrix[x + 1].append(min(x_candidate, y_candidate, xy_candidate))


    # Display the cost matrix
    # COL_WIDTH = 16
    # print(f"{'.'.ljust(COL_WIDTH) * 2}{''.join(str(key).ljust(COL_WIDTH) for key in annotated_keys)}")
    # for r, ch in zip(matrix, f".{translation}"):
    #     print(f"{ch.ljust(COL_WIDTH)}{''.join(str(cell.cost).ljust(COL_WIDTH) for cell in r)}")


    # Traceback

    def traceback_matchings(cell: _Cell) -> Generator[AnnotatedChord[Sequence[str]], None, None]:
        if cell.parent is None: return

        if cell.has_match:
            start_cell = cell.parent
            asterisk_matches = cell.asterisk_matches
        else:
            start_cell = matrix[cell.parent.unmatched_char_start_index][cell.parent.unmatched_key_start_index]
            asterisk_matches = (False,) * (cell.y - start_cell.y)

        yield from traceback_matchings(start_cell)

        yield AnnotatedChord(
            data=keysymbols[start_cell.x:cell.x],
            chord=AnnotatedChord.keys_to_strokes((key.key for key in annotated_keys[start_cell.y:cell.y]), asterisk_matches),
        )

    return tuple(traceback_matchings(matrix[-1][-1]))
