from enum import Enum, auto
from typing import Optional

from plover.steno import Stroke

from .Trie import Trie
from .config import Phoneme, PHONEMES_TO_CHORDS_LEFT, PHONEMES_TO_CHORDS_RIGHT

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