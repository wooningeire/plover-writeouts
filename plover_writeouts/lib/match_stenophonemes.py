from dataclasses import dataclass
from typing import Generator, Sequence, cast


from .Phoneme import Phoneme
from .Sopheme import Sopheme
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
    Phoneme.Z: ("STKPW", "-Z", "-F", "S", "-S"),

    Phoneme.TH: ("TH", "*T"),
    Phoneme.SH: ("SH", "-RB"),
    Phoneme.CH: ("KH", "-FP"),

    Phoneme.NG: ("-PB", "-PBG"),
}

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
        "u": ("U", "W", "AOU", "U/W", "AOU/W", "KWRU", "KWRAOU", "KWRU/W", "KWRAOU/W"),
        "v": ("SR", "-F"),
        "w": ("W", "U"),
        "x": ("KP", "-BGS", "-BG/S"),
        "y": ("KWH", "EU", "AOEU", "EU/KWR", "AOEU/KWR"),
        "z": ("STKPW", "-Z", "-F"),

        "th": ("TH", "*T"),
        "sh": ("SH", "-RB"),
        "ch": ("KH", "-FP"),

        "aa": ("A", "AU"),
        "ee": ("AOE",),
        "ii": ("AOE", "EU"),
        "oo": ("AO",),
        "ou": ("U",),
        "ea": ("AOE", "AE"),
        "ae": ("AE", "AEU"),
        "ai": ("AEU", "AOEU"),
        "ay": ("AEU", "AOEU"),
        "au": ("AU",),
        "aw": ("AU",),
        "oi": ("OEU",),
        "oy": ("OEU",),
        "ou": ("OU",),
        "ow": ("OU",),
        "ei": ("AOE", "E"),
        "ey": ("AOE", "E"),
        "ie": ("AOE", "E"),

        "dg": ("SKWR", "-PBLG"),
        "ck": ("K", "-BG"),
        "ti": ("SH", "-RB", "-RB/KWR"),
        "ci": ("SH", "-RB", "-RB/KWR"),
        "mp": ("*PL",),
        "sc": ("S", "-S"),

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

@dataclass(frozen=True)
class _Cell:
    """A cell in the Needleman–Wunsch alignment matrix; represents an optimal alignment of the first x keysymbols in a transcription to the first y keys in an outline."""

    n_unmatched_chars: int
    """The total number of unmatched keysymbols in the transcription using this cell's alignment."""
    n_unmatched_stenophonemes: int
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
        return (self.n_unmatched_stenophonemes, self.n_unmatched_chars, self.n_matchings)

    def __lt__(self, cell: "_Cell"):
        return self.cost < cell.cost
    
    def __gt__(self, cell: "_Cell"):
        return self.cost > cell.cost
    

def match_chars_to_stenophonemes(translation: str, stenophonemes: Sequence[AnnotatedChord[tuple[Sequence[str], Phoneme | str | None]]]):
    """Generates an alignment between a word's ortho–steno pairs and unilex keysymbol sequence.
    
    Uses a variation of the Needleman–Wunsch algorithm.
    """

    def create_mismatch_cell(x: int, y: int, increment_x: bool, increment_y: bool):
        mismatch_parent = matrix[x if increment_x else x + 1][y if increment_y else y + 1]

        return _Cell(
            mismatch_parent.n_unmatched_chars + (1 if increment_x else 0),
            mismatch_parent.n_unmatched_stenophonemes + (1 if increment_y else 0),
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

        candidate_chars = translation[:x + 1]
        candidate_keys = stenophonemes[:y + 1]

        print()
        print(candidate_chars, candidate_keys, x, y)

        candidate_cells = [create_mismatch_cell(x, y, increment_x, increment_y)]


        # When not incrementing x, only consider silent chords

        for i in range((len(candidate_chars) if increment_x else 0) + 1):
            grapheme = candidate_chars[len(candidate_chars) - i:]
            if grapheme.endswith("i"):
                print("using grapheme", grapheme)
            if grapheme not in _GRAPHEME_TO_STENO_MAPPINGS: continue


            # When not incrementing y, only consider silent letters

            if increment_y:
                chords = _GRAPHEME_TO_STENO_MAPPINGS[grapheme]
            else:
                chords = filter(lambda chord: len(chord) == 0, _GRAPHEME_TO_STENO_MAPPINGS[grapheme])

            for chord in chords:
                keys = tuple(
                    key
                    for candidate_key in candidate_keys
                    for key in AsteriskableKey.annotations_from_strokes(candidate_key.chord)
                )

                if len(chord) > len(keys): continue

                keys = keys[len(keys) - len(chord):]

                if grapheme.endswith("i"):
                    print("testing chord", chord)
                    print(keys)

                if tuple(key.key for key in keys) != tuple(key.key for key in chord): continue

                if any(
                    chord_key.asterisk and not candidate_key.asterisk
                    for candidate_key, chord_key in zip(keys, chord)
                ): continue

                n_stenophonemes_spanned = 0
                n_keys_counted = 0
                while n_keys_counted < len(keys):
                    n_keys_counted += sum(len(stroke) for stroke in candidate_keys[-n_stenophonemes_spanned - 1].chord)
                    n_stenophonemes_spanned += 1

                parent = matrix[x + 1 - len(grapheme)][y + 1 - n_stenophonemes_spanned]
                
                print("found", grapheme, chord)
                candidate_cells.append(
                    _Cell(
                        parent.n_unmatched_chars,
                        parent.n_unmatched_stenophonemes,
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

        for cell in candidate_cells:
            print(cell.cost, tuple(traceback_matchings(cell)))
            print("\t", tuple(traceback_matchings(cell.parent)) if cell.parent is not None else None)

        return min(candidate_cells)


    # Traceback
    def traceback_matchings(cell: _Cell):
        if cell.parent is None: return

        if cell.has_match:
            start_cell = cell.parent
            asterisk_matches = cell.asterisk_matches
        else:
            start_cell = matrix[cell.parent.unmatched_char_start_index][cell.parent.unmatched_key_start_index]
            asterisk_matches = (False,) * (cell.y - start_cell.y)

        yield from traceback_matchings(start_cell)

        yield Sopheme(translation[start_cell.x:cell.x], tuple(stenophonemes[start_cell.y:cell.y]))


    # Base row and column

    matrix = [[_Cell(0, 0, 0, 0, 0, None, 0, 0, False)]]

    for i in range(len(translation)):
        matrix.append([find_match(i, -1, True, False)])

    for i in range(len(stenophonemes)):
        matrix[0].append(find_match(-1, i, False, True))


    # Populating the matrix

    for x in range(len(translation)):
        for y in range(len(stenophonemes)):
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

    return tuple(traceback_matchings(matrix[-1][-1]))
