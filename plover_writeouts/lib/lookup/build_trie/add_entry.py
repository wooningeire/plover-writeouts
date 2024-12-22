from typing import Optional

import plover.log

from ...util.Trie import TransitionCostInfo, NondeterministicTrie
from ...theory.theory import (
    TRIE_STROKE_BOUNDARY_KEY,
    TRIE_LINKER_KEY,
    INITIAL_VOWEL_CHORD,
    PHONEMES_TO_CHORDS_VOWELS,
)

from .state import EntryBuilderState, OutlineSounds
from .find_clusters import Cluster, handle_clusters
from .rules.left_consonants import add_left_consonant
from .rules.right_consonants import add_right_consonant

def add_entry(trie: NondeterministicTrie[str, str], phonemes: OutlineSounds, translation: str):
    state = EntryBuilderState(trie, phonemes, translation)
    state.left_consonant_src_node = trie.ROOT


    upcoming_clusters: dict[tuple[int, int], list[Cluster]] = {}

    for group_index, (consonants, vowel) in enumerate(phonemes.nonfinals):
        state.group_index = group_index

        vowels_src_node: Optional[int] = None
        if len(consonants) == 0 and not state.is_first_consonant_set:
            vowels_src_node = trie.get_first_dst_node_else_create(state.left_consonant_src_node, TRIE_LINKER_KEY, TransitionCostInfo(0, translation))

        for phoneme_index, consonant in enumerate(consonants):
            state.phoneme_index = phoneme_index


            left_consonant_node, left_alt_consonant_node = add_left_consonant(state)


            right_consonant_node = state.right_consonant_src_node
            right_alt_consonant_node = state.last_right_alt_consonant_node
            if not state.is_first_consonant_set:
                right_consonant_node, right_alt_consonant_node, rtl_stroke_boundary_adjacent_nodes = add_right_consonant(state, left_consonant_node)
                if rtl_stroke_boundary_adjacent_nodes is not None:
                    state.right_elision_squish_src_node, state.left_elision_boundary_src_node = rtl_stroke_boundary_adjacent_nodes

            handle_clusters(upcoming_clusters, left_consonant_node, right_consonant_node, state, False)

            state.left_consonant_src_node = state.prev_left_consonant_node = left_consonant_node
            state.last_left_alt_consonant_node = left_alt_consonant_node
            state.right_consonant_src_node = right_consonant_node
            state.last_right_alt_consonant_node = right_alt_consonant_node

        state.phoneme_index = len(consonants)

        state.left_elision_squish_src_node = state.left_consonant_src_node
        # can't really do anything all that special with vowels, so only proceed through a vowel transition
        # if it matches verbatim
        if vowels_src_node is None:
            vowels_src_node = state.left_consonant_src_node
        postvowels_node = trie.get_first_dst_node_else_create(vowels_src_node, PHONEMES_TO_CHORDS_VOWELS[vowel.phoneme].rtfcre, TransitionCostInfo(0, translation))

        handle_clusters(upcoming_clusters, state.left_consonant_src_node, state.right_consonant_src_node, state, True)


        state.right_consonant_src_node = postvowels_node
        state.left_consonant_src_node = trie.get_first_dst_node_else_create(postvowels_node, TRIE_STROKE_BOUNDARY_KEY, TransitionCostInfo(0, translation))

        if INITIAL_VOWEL_CHORD is not None and state.is_first_consonant_set and len(consonants) == 0:
            trie.link_chain(trie.ROOT, state.left_consonant_src_node, INITIAL_VOWEL_CHORD.keys(), TransitionCostInfo(0, translation))

        state.prev_left_consonant_node = None


    state.group_index = len(phonemes.nonfinals)
    for phoneme_index, consonant in enumerate(phonemes.final_consonants):
        state.phoneme_index = phoneme_index

        right_consonant_node, right_alt_consonant_node, _ = add_right_consonant(state, None)

        handle_clusters(upcoming_clusters, None, right_consonant_node, state, False)

        state.right_consonant_src_node = right_consonant_node
        state.last_right_alt_consonant_node = right_alt_consonant_node

        state.left_consonant_src_node = None

    if state.right_consonant_src_node is None:
        # The outline contains no vowels and is likely a brief
        return

    trie.set_translation(state.right_consonant_src_node, translation)



