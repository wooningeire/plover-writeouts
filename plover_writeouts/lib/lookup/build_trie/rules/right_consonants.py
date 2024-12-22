from typing import Optional

import plover.log

from ....util.Trie import TransitionCostInfo
from ....util.util import can_add_stroke_on
from ....theory.theory import (
    Stenophoneme,
    TRIE_STROKE_BOUNDARY_KEY,
    TRIE_LINKER_KEY,
    PHONEMES_TO_CHORDS_RIGHT,
    PHONEMES_TO_CHORDS_RIGHT_ALT,
    TransitionCosts,
)
from ....theory.theory import amphitheory

from ..state import EntryBuilderState
from .elision import allow_elide_previous_vowel_using_first_right_consonant


def add_right_consonant(state: EntryBuilderState, left_consonant_node: Optional[int]):
    if state.right_consonant_src_node is None or state.consonant.phoneme not in PHONEMES_TO_CHORDS_RIGHT:
        return None, None, None
    

    right_stroke = PHONEMES_TO_CHORDS_RIGHT[state.consonant.phoneme]
    right_stroke_keys = right_stroke.keys()
    
    right_consonant_node = state.trie.get_first_dst_node_else_create_chain(state.right_consonant_src_node, right_stroke_keys, TransitionCostInfo(0, state.translation))


    if state.last_right_alt_consonant_node is not None:
        state.trie.link_chain(state.last_right_alt_consonant_node, right_consonant_node, right_stroke_keys, TransitionCostInfo(TransitionCosts.VOWEL_ELISION if state.is_first_consonant else 0, state.translation))

    # Skeletals and right-bank consonant addons
    can_use_main_prev = (
        state.last_consonant is None
        or state.last_consonant.phoneme in PHONEMES_TO_CHORDS_RIGHT and can_add_stroke_on(PHONEMES_TO_CHORDS_RIGHT[state.last_consonant.phoneme], right_stroke)
    )
    if state.prev_left_consonant_node is not None and not can_use_main_prev:
        state.trie.link_chain(state.prev_left_consonant_node, right_consonant_node, right_stroke_keys, TransitionCostInfo(0, state.translation))


    pre_rtl_stroke_boundary_node = state.right_elision_squish_src_node
    rtl_stroke_boundary_node = None

    if left_consonant_node is not None and state.consonant.phoneme is not Stenophoneme.DUMMY:
        pre_rtl_stroke_boundary_node = right_consonant_node
        rtl_stroke_boundary_node = state.trie.get_first_dst_node_else_create(right_consonant_node, TRIE_STROKE_BOUNDARY_KEY, TransitionCostInfo(0, state.translation))
        state.trie.link(rtl_stroke_boundary_node, left_consonant_node, TRIE_LINKER_KEY, TransitionCostInfo(0, state.translation))
        

    if state.is_first_consonant:
        allow_elide_previous_vowel_using_first_right_consonant(state, right_stroke, right_consonant_node)


    right_consonant_f_node = _add_right_alt_consonant(state, right_consonant_node)

    rtl_stroke_boundary_adjacent_nodes = (pre_rtl_stroke_boundary_node, rtl_stroke_boundary_node)
    return right_consonant_node, right_consonant_f_node, rtl_stroke_boundary_adjacent_nodes if rtl_stroke_boundary_node is not None else None

def _add_right_alt_consonant(state: EntryBuilderState, right_consonant_node: int):
    if state.right_consonant_src_node is None or state.consonant.phoneme not in PHONEMES_TO_CHORDS_RIGHT_ALT:
        return None
    
    right_alt_stroke = PHONEMES_TO_CHORDS_RIGHT_ALT[state.consonant.phoneme]
    right_stroke = amphitheory.right_consonant_chord(state.consonant)

    should_use_alt_from_prev = (
        state.last_consonant is None
        or state.last_consonant.phoneme in PHONEMES_TO_CHORDS_RIGHT and (
            can_add_stroke_on(amphitheory.right_consonant_chord(state.last_consonant), right_stroke)
            or not can_add_stroke_on(amphitheory.right_consonant_chord(state.last_consonant), right_alt_stroke)
        )
    )
    should_use_alt_from_next = (
        state.next_consonant is None
        or state.next_consonant.phoneme in PHONEMES_TO_CHORDS_RIGHT and (
            can_add_stroke_on(right_stroke, PHONEMES_TO_CHORDS_RIGHT[state.next_consonant.phoneme])
            or not can_add_stroke_on(right_alt_stroke, PHONEMES_TO_CHORDS_RIGHT[state.next_consonant.phoneme])
        )
    )
    if should_use_alt_from_prev and should_use_alt_from_next:
        return None


    right_alt_stroke_keys = right_alt_stroke.keys()


    right_alt_consonant_node = state.trie.get_first_dst_node_else_create_chain(state.right_consonant_src_node, right_alt_stroke_keys, TransitionCostInfo(TransitionCosts.ALT_CONSONANT, state.translation))
    if state.last_right_alt_consonant_node is not None:
        state.trie.link_chain(
            state.last_right_alt_consonant_node, right_alt_consonant_node, right_alt_stroke_keys,
            TransitionCostInfo(TransitionCosts.ALT_CONSONANT + (TransitionCosts.VOWEL_ELISION if state.is_first_consonant else 0), state.translation)
        )

    if state.prev_left_consonant_node is not None and not should_use_alt_from_prev:
        state.trie.link_chain(state.prev_left_consonant_node, right_alt_consonant_node, right_alt_stroke_keys, TransitionCostInfo(0, state.translation))
        
    if state.is_first_consonant:
        allow_elide_previous_vowel_using_first_right_consonant(state, right_alt_stroke, right_consonant_node, TransitionCosts.ALT_CONSONANT)

    return right_alt_consonant_node