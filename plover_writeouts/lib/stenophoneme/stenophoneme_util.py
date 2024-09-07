from typing import Optional

from plover.steno import Stroke

from ..util.Trie import Trie
from ..theory.theory import PHONEMES_TO_CHORDS_LEFT, PHONEMES_TO_CHORDS_RIGHT
from ..stenophoneme.Stenophoneme import Stenophoneme

_CONSONANT_CHORDS: dict[Stroke, tuple[Stenophoneme, ...]] = {
    **{
        stroke: (phoneme,)
        for phoneme, stroke in PHONEMES_TO_CHORDS_LEFT.items()
    },
    **{
        stroke: (phoneme,)
        for phoneme, stroke in PHONEMES_TO_CHORDS_RIGHT.items()
    },

    **{
        Stroke.from_steno(steno): phonemes
        for steno, phonemes in {
            "PHR": (Stenophoneme.P, Stenophoneme.L),
            "TPHR": (Stenophoneme.F, Stenophoneme.L),
        }.items()
    },
}

def _build_consonants_trie():
    consonants_trie: Trie[str, tuple[Stenophoneme, ...]] = Trie()
    for stroke, _phoneme in _CONSONANT_CHORDS.items():
        current_head = consonants_trie.get_dst_node_else_create_chain(consonants_trie.ROOT, stroke.keys())
        consonants_trie.set_translation(current_head, _phoneme)
    return consonants_trie.frozen()
_consonants_trie = _build_consonants_trie()


def split_consonant_phonemes(consonants_stroke: Stroke):
    keys = consonants_stroke.keys()
    
    chord_start_index = 0
    while chord_start_index < len(keys):
        current_node = _consonants_trie.ROOT

        longest_chord_end_index = chord_start_index

        entry: tuple[Stenophoneme, ...] = ()

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

        yield from entry

        chord_start_index = longest_chord_end_index + 1