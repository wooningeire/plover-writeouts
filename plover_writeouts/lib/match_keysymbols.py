from dataclasses import dataclass
from typing import Generator, Sequence, cast
from itertools import cycle

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
    Phoneme.Z: ("STKPW", "-Z", "-F", "S", "-S"),

    Phoneme.TH: ("TH", "*T"),
    Phoneme.SH: ("SH", "-RB"),
    Phoneme.CH: ("KH", "-FP"),

    Phoneme.NG: ("-PB", "-PBG"),
}

@dataclass(frozen=True)
class _Mapping:
    phoneme: Phoneme | str
    keys: tuple[AsteriskableKey, ...]

_mappings = lambda phoneme: tuple(zip(cycle((phoneme,)), _PHONEME_TO_STENO_MAPPINGS[phoneme]))
_vowels = lambda *phonemes: tuple(zip(phonemes, phonemes))

_KEYSYMBOL_TO_STENO_MAPPINGS = {
    tuple(keysymbol.split(" ")): sorted(
        tuple(_Mapping(phoneme, AsteriskableKey.annotations_from_outline(outline_steno)) for phoneme, outline_steno in mapping),
        key=lambda mapping: len(mapping.keys),
        reverse=True,
    )
    for keysymbol, mapping in cast(dict[str, tuple[tuple[Phoneme | str, str], ...]], {
        # How does each keysymbol appear as it does in Lapwing?

        "p": _mappings(Phoneme.P),
        "t": _mappings(Phoneme.T),
        "?": (),  # glottal stop
        "t^": (*_mappings(Phoneme.T), *_mappings(Phoneme.R)),  # tapped R
        "k": _mappings(Phoneme.K),
        "x": _mappings(Phoneme.K),
        "b": _mappings(Phoneme.B),
        "d": _mappings(Phoneme.D),
        "g": _mappings(Phoneme.G),
        "ch": _mappings(Phoneme.CH),
        "jh": _mappings(Phoneme.J),
        "s": _mappings(Phoneme.S),
        "z": _mappings(Phoneme.Z),
        "sh": _mappings(Phoneme.SH),
        "zh": (*_mappings(Phoneme.SH), *_mappings(Phoneme.J)),
        "f": _mappings(Phoneme.F),
        "v": _mappings(Phoneme.V),
        "th": _mappings(Phoneme.TH),
        "dh": _mappings(Phoneme.TH),
        "h": _mappings(Phoneme.H),
        "m": _mappings(Phoneme.M),
        "m!": _mappings(Phoneme.M),
        "n": _mappings(Phoneme.N),
        "n!": _mappings(Phoneme.N),
        "ng": _mappings(Phoneme.NG),
        "l": _mappings(Phoneme.L),
        "ll": _mappings(Phoneme.L),
        "lw": _mappings(Phoneme.L),
        "l!": _mappings(Phoneme.L),
        "r": _mappings(Phoneme.R),
        "y": _mappings(Phoneme.Y),
        "w": _mappings(Phoneme.W),
        "hw": _mappings(Phoneme.W),

        "e": _vowels("E", "AOE", "AEU"),
        "ao": _vowels("A", "O", "AO", "AU",),
        "a": _vowels("A",),
        "ah": _vowels("AU"),
        "oa": _vowels("A", "AO", "O"),
        "aa": _vowels("AU",),
        "ar": _vowels("A",),
        "eh": _vowels("A",),
        "ou": _vowels("OE",),
        "ouw": _vowels("OE",),
        "oou": _vowels("OE",),
        "o": _vowels("O", "AU"),
        "au": _vowels("O", "AU"),
        "oo": _vowels("O", "AU"),
        "or": _vowels("O", "AU"),
        "our": _vowels("O", "AU"),
        "ii": _vowels("AOE", "EU", "E"),
        "iy": _vowels("AOE", "EU"),
        "i": _vowels("EU",),
        "@r": _vowels("A", "O", "E", "U", "EU"),
        "@": _vowels("A", "O", "E", "U", "EU"),
        "uh": _vowels("U",),
        "u": _vowels("U", "AO", "O", "OE"),
        "uu": _vowels("AOU", "AO"),
        "iu": _vowels("AOU", "AO"),
        "ei": _vowels("E", "AEU"),
        "ee": _vowels("E", "AEU"),
        "ai": _vowels("AOEU",),
        "ae": _vowels("AOEU",),
        "aer": _vowels("AOEU",),
        "aai": _vowels("AOEU",),
        "oi": _vowels("OEU",),
        "oir": _vowels("OEU",),
        "ow": _vowels("OU",),
        "owr": _vowels("OU",),
        "oow": _vowels("OU",),
        "ir": _vowels("AOE", "EU"),
        "@@r": _vowels("A", "O", "E", "U", "EU"),
        "er": _vowels("E", "U"),
        "eir": _vowels("E", "AEU"),
        "ur": _vowels("U",),
        "i@": _vowels("KWRA", "KWRO", "KWRE", "KWRU", "KWREU", "KWHA", "KWHO", "KWHE", "KWHU", "KWHEU"),
        "k s": _vowels("KP",),
        "sh n": _vowels("-GS",),
        "k sh n": _vowels("-BGS",),
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

    phoneme_match: "Phoneme | str | None" = None

    @property
    def cost(self):
        return (self.n_unmatched_keys, self.n_unmatched_keysymbols, self.n_matchings)

    def __lt__(self, cell: "_Cell"):
        return self.cost < cell.cost
    
    def __gt__(self, cell: "_Cell"):
        return self.cost > cell.cost
    

def match_keysymbols_to_writeout_chords(keysymbols: tuple[str, ...], outline_steno: str):
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
                mappings = _KEYSYMBOL_TO_STENO_MAPPINGS[grapheme]
            else:
                mappings = filter(lambda mapping: len(mapping.keys) == 0, _KEYSYMBOL_TO_STENO_MAPPINGS[grapheme])

            for mapping in mappings:
                # print("testing chord", chord)
                sub_candidate_keys = candidate_keys[len(candidate_keys) - len(mapping.keys):]
                if tuple(key.key for key in sub_candidate_keys) != tuple(key.key for key in mapping.keys): continue

                if any(
                    chord_key.asterisk and not candidate_key.asterisk
                    for candidate_key, chord_key in zip(sub_candidate_keys, mapping.keys)
                ): continue

                parent = matrix[x + 1 - len(grapheme)][y + 1 - len(mapping.keys)]
                
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
                        tuple(key.asterisk for key in mapping.keys),
                        mapping.phoneme,
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

    def traceback_matchings(cell: _Cell) -> Generator[AnnotatedChord[tuple[Sequence[str], Phoneme | str | None]], None, None]:
        if cell.parent is None: return

        if cell.has_match:
            start_cell = cell.parent
            asterisk_matches = cell.asterisk_matches
        else:
            start_cell = matrix[cell.parent.unmatched_char_start_index][cell.parent.unmatched_key_start_index]
            asterisk_matches = (False,) * (cell.y - start_cell.y)

        yield from traceback_matchings(start_cell)

        yield AnnotatedChord(
            data=(keysymbols[start_cell.x:cell.x], cell.phoneme_match),
            chord=AnnotatedChord.keys_to_strokes((key.key for key in annotated_keys[start_cell.y:cell.y]), asterisk_matches),
        )

    return tuple(traceback_matchings(matrix[-1][-1]))
