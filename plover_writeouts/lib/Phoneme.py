from collections import defaultdict
from enum import Enum, auto
from typing import Optional

from plover.steno import Stroke

from .DagTrie import DagTrie

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


_CONSONANT_CHORDS: dict[str, Phoneme] = {
    # LEFT BANK

    "S": Phoneme.S,
    "T": Phoneme.T,
    "K": Phoneme.K,
    "P": Phoneme.P,
    "W": Phoneme.W,
    "H": Phoneme.H,
    "R": Phoneme.R,

    "STKPW": Phoneme.Z,
    "SKWR": Phoneme.J,
    "SR": Phoneme.V,
    "TK": Phoneme.D,
    "TKPW": Phoneme.G,
    "TP": Phoneme.F,
    "TPH": Phoneme.N,
    "K": Phoneme.K,
    "KWR": Phoneme.Y,
    "PW": Phoneme.B,
    "PH": Phoneme.M,
    "HR": Phoneme.L,

    # RIGHT BANK

    "-F": Phoneme.F,
    "-R": Phoneme.R,
    "-P": Phoneme.P,
    "-B": Phoneme.B,
    "-L": Phoneme.L,
    "-G": Phoneme.G,
    "-T": Phoneme.T,
    "-S": Phoneme.S,
    "-D": Phoneme.D,
    "-Z": Phoneme.Z,

    "-FB": Phoneme.V,
    "-PB": Phoneme.N,
    "-PL": Phoneme.M,
    "-BG": Phoneme.K,
    "-FP": Phoneme.CH,
    "-PBLG": Phoneme.J,

    # "SHR": "shr",
    # "THR": "thr",
    # "KHR": "chr",
    # "-FRP": (Phoneme.M, Phoneme.P),
    # "-FRB": (Phoneme.R, Phoneme.V),
}

_consonants_trie: DagTrie[str, tuple[Phoneme, Stroke]] = DagTrie()
for chord, entry in _CONSONANT_CHORDS.items():
    stroke = Stroke.from_steno(chord)
    current_head = _consonants_trie.ROOT
    for key in stroke.keys():
        current_head = _consonants_trie.get_dst_node_else_create(current_head, key)
    
    _consonants_trie.set_translation(current_head, (entry, stroke))

def split_consonant_phonemes(consonants: Stroke):
    entries_found: list[tuple[Phoneme, Stroke]] = []

    keys = consonants.keys()
    
    chord_start_index = 0
    while chord_start_index < len(keys):
        current_node = _consonants_trie.ROOT

        longest_chord_end_index = chord_start_index

        entry: Optional[tuple[Phoneme, Stroke]] = None

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