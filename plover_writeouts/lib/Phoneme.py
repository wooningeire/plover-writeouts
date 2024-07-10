from collections import defaultdict
from enum import Enum, auto
from typing import Optional

from plover.steno import Stroke

from .DagTrie import Trie, NondeterministicTrie

class Phoneme(Enum):
    S = auto()
    T = auto()
    K = auto()
    P = auto()
    W = auto()
    H = auto()
    R = auto()

    Z = auto()
    J = auto()
    V = auto()
    D = auto()
    G = auto()
    F = auto()
    N = auto()
    Y = auto()
    B = auto()
    M = auto()
    L = auto()

    CH = auto()
    SH = auto()
    TH = auto()


PHONEMES_TO_CHORDS_LEFT: dict[Phoneme, Stroke] = {
    phoneme: Stroke.from_steno(steno)
    for phoneme, steno in {
        Phoneme.S: "S",
        Phoneme.T: "T",
        Phoneme.K: "K",
        Phoneme.P: "P",
        Phoneme.W: "W",
        Phoneme.H: "H",
        Phoneme.R: "R",

        Phoneme.Z: "STKPW",
        Phoneme.J: "SKWR",
        Phoneme.V: "SR",
        Phoneme.D: "TK",
        Phoneme.G: "TKPW",
        Phoneme.F: "TP",
        Phoneme.N: "TPH",
        Phoneme.Y: "KWR",
        Phoneme.B: "PW",
        Phoneme.M: "PH",
        Phoneme.L: "HR",
    }.items()
}

PHONEMES_TO_CHORDS_RIGHT: dict[Phoneme, Stroke] = {
    phoneme: Stroke.from_steno(steno)
    for phoneme, steno in {
        Phoneme.F: "-F",
        Phoneme.R: "-R",
        Phoneme.P: "-P",
        Phoneme.B: "-B",
        Phoneme.L: "-L",
        Phoneme.G: "-G",
        Phoneme.T: "-T",
        Phoneme.S: "-S",
        Phoneme.D: "-D",
        Phoneme.Z: "-Z",

        Phoneme.V: "-FB",
        Phoneme.N: "-PB",
        Phoneme.M: "-PL",
        Phoneme.K: "-BG",
        Phoneme.CH: "-FP",
        Phoneme.SH: "-RB",
        Phoneme.J: "-PBLG",
    }.items()

    # "SHR": "shr",
    # "THR": "thr",
    # "KHR": "chr",
    # "-FRP": (Phoneme.M, Phoneme.P),
    # "-FRB": (Phoneme.R, Phoneme.V),
}

PHONEMES_TO_CHORDS_RIGHT_F: dict[Phoneme, Stroke] = {
    phoneme: Stroke.from_steno(steno)
    for phoneme, steno in {
        Phoneme.S: "-F",
        Phoneme.Z: "-F",
        Phoneme.V: "-F",
        Phoneme.TH: "-F",
        Phoneme.J: "-F",
        Phoneme.M: "-FR",
    }.items()
}

_CONSONANT_CHORDS: dict[Stroke, Phoneme] = {
    **{
        stroke: phoneme
        for phoneme, stroke in PHONEMES_TO_CHORDS_LEFT.items()
    },
    **{
        stroke: phoneme
        for phoneme, stroke in PHONEMES_TO_CHORDS_RIGHT.items()
    },
}

_consonants_trie: Trie[str, Phoneme] = Trie()
for _stroke, _phoneme in _CONSONANT_CHORDS.items():
    _current_head = _consonants_trie.get_dst_node_else_create_chain(_consonants_trie.ROOT, _stroke.keys())
    _consonants_trie.set_translation(_current_head, _phoneme)

def split_consonant_phonemes(consonants_stroke: Stroke):
    entries_found: list[Phoneme] = []

    keys = consonants_stroke.keys()
    
    chord_start_index = 0
    while chord_start_index < len(keys):
        current_node = _consonants_trie.ROOT

        longest_chord_end_index = chord_start_index

        entry: Optional[Phoneme] = None

        for seek_index in range(chord_start_index, len(keys)):
            key = keys[seek_index]
            
            current_node = _consonants_trie.get_dst_node(current_node, key)
            if current_node is None:
                break

            new_entry = _consonants_trie.get_translation(current_node)
            if new_entry is None:
                continue
        
            entry = new_entry
            longest_chord_end_index = seek_index

        if entry is not None:
            entries_found.append(entry)

        chord_start_index = longest_chord_end_index + 1

    return tuple(entries_found)