from dataclasses import dataclass
from typing import Generator, cast

from .steno_annotations import AsteriskableKey, AnnotatedChord


_GRAPHEME_TO_STENO_MAPPINGS = {
    grapheme: sorted(
        tuple(AsteriskableKey.annotations_from_outline(outline_steno) for outline_steno in outline_stenos),
        key=lambda keys: len(keys), reverse=True
    )
    for grapheme, outline_stenos in cast(dict[str, tuple[str, ...]], {
        # Does not need to be fully complete to be effective

        "": ("KWR", "W"),

        "a": ("A", "AEU", "AU"),
        "b": ("PW", "-B"),
        "c": ("S", "K", "KR", "-BG", "-S", "SH", "-RB", "KH", "-FP"),
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
        "s": ("S", "-S", "-F", "-Z", "SH", "-RB"),
        "t": ("T", "-T", "SH", "-RB", "KH", "-FP"),
        "u": ("U", "AOU", "U/W", "AOU/W", "KWRU", "KWRAOU", "KWRU/W", "KWRAOU/W"),
        "v": ("SR", "-F"),
        "w": ("W", "U"),
        "x": ("KP", "-BGS", "-BG/S"),
        "y": ("KWH", "EU", "AOEU", "EU/KWR", "AOEU/KWR"),
        "z": ("STKPW", "-Z", "-F"),

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
        "ss": ("S", "-S", "-F", "-Z", "SH", "-RB"),
        "tt": ("T", "-T"),
        "vv": ("SR", "-F"),
        "xx": ("KP", "-BGS", "-BG/S"),
        "zz": ("STKPW", "-Z", "-F"),

        "tion": ("-GS",),
        "cian": ("-GS",),
        "ction": ("-BGS",),
        "nction": ("-PBGS",),
    }).items()
}
"""A list of what counts as a "match" when matching characters to keys."""

@dataclass(frozen=True)
class _Cell:
    """A cell in the Needleman–Wunsch alignment matrix; represents an optimal alignment of the first x characters in a translation to the first y keys in an outline."""

    n_unmatched_chars: int
    """The total number of unmatched characters in the translation using this cell's alignment."""
    n_unmatched_keys: int
    """The total number of unmatched keys in the outline using this cell's alignment."""
    n_sophemes: int

    unmatched_char_start_index: int
    """The index where the sequence of trailing unmatched characters for this alignment beigins. Used during traceback when a match is not found by this cell."""
    unmatched_key_start_index: int
    """The index where the sequence of trailing unmatched keys for this alignment beigins. Used during traceback when a match is not found by this cell."""
    
    parent: "_Cell | None"
    """The optimal sub-alignment which this alignment extends upon."""

    x: int
    y: int

    has_match: bool
    asterisk_matches: tuple[bool, ...] = ()

    @property
    def cost(self):
        return (self.n_unmatched_keys, self.n_unmatched_chars, self.n_sophemes)

    def __lt__(self, cell: "_Cell"):
        return self.cost < cell.cost
    
    def __gt__(self, cell: "_Cell"):
        return self.cost > cell.cost
    

def match_chars_to_writeout_chords(translation: str, outline_steno: str):
    """Generates an alignment between characters in a translation and keys in a Lapwing-style outline.
    
    Uses a variation of the Needleman–Wunsch algorithm.
    
    Assumptions:
    - Strict left-to-right parsing; no inversions
    """

    annotated_keys = AsteriskableKey.annotations_from_outline(outline_steno)

    def create_mismatch_cell(x: int, y: int, increment_x: bool, increment_y: bool):
        mismatch_parent = matrix[x if increment_x else x + 1][y if increment_y else y + 1]

        return _Cell(
            mismatch_parent.n_unmatched_chars + (1 if increment_x else 0),
            mismatch_parent.n_unmatched_keys + (1 if increment_y else 0),
            mismatch_parent.n_sophemes + 1 if mismatch_parent.has_match else mismatch_parent.n_sophemes,
            mismatch_parent.unmatched_char_start_index,
            mismatch_parent.unmatched_key_start_index,
            mismatch_parent,
            x + 1,
            y + 1,
            False,
        )

    def find_match(x: int, y: int, increment_x: bool, increment_y: bool):
        """Attempt to match any combination of the last m consecutive unmatched characters to the last n consecutive unmatched keys."""

        candidate_chars = translation[:x + 1]
        candidate_keys = annotated_keys[:y + 1]

        # print()
        # print(unmatched_chars, unmatched_keys, x, y)

        candidate_cells = [create_mismatch_cell(x, y, increment_x, increment_y)]


        # When not incrementing x, only consider silent chords

        for i in range((len(candidate_chars) if increment_x else 0) + 1):
            grapheme = candidate_chars[len(candidate_chars) - i:]
            # print("using grapheme", grapheme)
            if grapheme not in _GRAPHEME_TO_STENO_MAPPINGS: continue


            # When not incrementing y, only consider silent letters

            if increment_y:
                chords = _GRAPHEME_TO_STENO_MAPPINGS[grapheme]
            else:
                chords = filter(lambda chord: len(chord) == 0, _GRAPHEME_TO_STENO_MAPPINGS[grapheme])

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
                        parent.n_unmatched_chars,
                        parent.n_unmatched_keys,
                        parent.n_sophemes + 1,
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

    for i in range(len(translation)):
        matrix.append([find_match(i, -1, True, False)])

    for i in range(len(annotated_keys)):
        matrix[0].append(find_match(-1, i, False, True))


    # Populating the matrix

    for x in range(len(translation)):
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

    def traceback_matchings(cell: _Cell) -> Generator[AnnotatedChord[str], None, None]:
        if cell.parent is None: return

        if cell.has_match:
            start_cell = cell.parent
            asterisk_matches = cell.asterisk_matches
        else:
            start_cell = matrix[cell.parent.unmatched_char_start_index][cell.parent.unmatched_key_start_index]
            asterisk_matches = (False,) * (cell.y - start_cell.y)

        yield from traceback_matchings(start_cell)

        yield AnnotatedChord(
            data=translation[start_cell.x:cell.x],
            chord=AnnotatedChord.keys_to_strokes((key.key for key in annotated_keys[start_cell.y:cell.y]), asterisk_matches),
        )

    return tuple(traceback_matchings(matrix[-1][-1]))
