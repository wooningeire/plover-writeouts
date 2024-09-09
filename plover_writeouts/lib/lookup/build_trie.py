from typing import NamedTuple, Optional, Any
import dataclasses
from dataclasses import dataclass
from abc import ABC, abstractmethod

from plover.steno import Stroke
import plover.log

from ..stenophoneme.Stenophoneme import vowel_phonemes
from ..util.Trie import ReadonlyTrie, TransitionCostInfo, Trie, NondeterministicTrie
from ..util.util import can_add_stroke_on
from ..theory.theory import (
    Stenophoneme,
    LEFT_BANK_CONSONANTS_SUBSTROKE,
    TRIE_STROKE_BOUNDARY_KEY,
    TRIE_LINKER_KEY,
    INITIAL_VOWEL_CHORD,
    CLUSTERS,
    VOWEL_CONSCIOUS_CLUSTERS,
    PHONEMES_TO_CHORDS_LEFT,
    PHONEMES_TO_CHORDS_LEFT_ALT,
    PHONEMES_TO_CHORDS_VOWELS,
    PHONEMES_TO_CHORDS_RIGHT,
    PHONEMES_TO_CHORDS_RIGHT_ALT,
    TransitionCosts,
)


class ConsonantVowelGroup(NamedTuple):
    consonants: tuple[Stenophoneme, ...]
    vowel: Stenophoneme

@dataclass(frozen=True)
class OutlinePhonemes:
    nonfinals: tuple[ConsonantVowelGroup, ...]
    final_consonants: tuple[Stenophoneme, ...]

    def get_consonants(self, group_index: int):
        if group_index == len(self.nonfinals):
            return self.final_consonants
        return self.nonfinals[group_index].consonants

    def get_consonant(self, group_index: int, phoneme_index: int):
        return self.get_consonants(group_index)[phoneme_index]

    def __getitem__(self, key: tuple[int, int]):
        group_index, phoneme_index = key

        if group_index == len(self.nonfinals):
            return self.final_consonants[phoneme_index]
        if phoneme_index == len(self.nonfinals[group_index].consonants):
            return self.nonfinals[group_index].vowel
        return self.nonfinals[group_index].consonants[phoneme_index]
    
    def decrement_consonant_index(self, group_index: int, phoneme_index: int):
        current_consonants = self.get_consonants(group_index)

        phoneme_index -= 1

        while phoneme_index == -1:
            if group_index == 0:
                return None
        
            group_index -= 1
            current_consonants = self.get_consonants(group_index)
            phoneme_index = len(current_consonants) - 1

        return group_index, phoneme_index
    
    def increment_consonant_index(self, group_index: int, phoneme_index: int):
        current_consonants = self.get_consonants(group_index)

        phoneme_index += 1

        while phoneme_index == len(current_consonants):
            if group_index == len(self.nonfinals):
                return None
        
            group_index += 1
            phoneme_index = 0
            current_consonants = self.get_consonants(group_index)

        return group_index, phoneme_index
    
    def increment_index(self, group_index: int, phoneme_index: int):
        current_consonants = self.get_consonants(group_index)

        phoneme_index += 1

        if group_index == len(self.nonfinals) and phoneme_index >= len(current_consonants):
            return None

        if group_index < len(self.nonfinals) and phoneme_index > len(current_consonants):
            group_index += 1
            phoneme_index = 0
            current_consonants = self.get_consonants(group_index)

        if group_index == len(self.nonfinals) and phoneme_index >= len(current_consonants):
            return None

        return group_index, phoneme_index
    
    def get_consonant_after(self, group_index: int, phoneme_index: int):
        next_index = self.increment_consonant_index(group_index, phoneme_index)
        if next_index is None:
            return None
        
        return self.get_consonant(*next_index)
    
    def get_consonant_before(self, group_index: int, phoneme_index: int):
        last_index = self.decrement_consonant_index(group_index, phoneme_index)
        if last_index is None:
            return None
        
        return self.get_consonant(*last_index)


def _build_clusters_trie():
    clusters_trie: Trie[Stenophoneme, Stroke] = Trie()
    for phonemes, stroke in CLUSTERS.items():
        current_head = clusters_trie.ROOT
        for key in phonemes:
            current_head = clusters_trie.get_dst_node_else_create(current_head, key)

        clusters_trie.set_translation(current_head, stroke)
    return clusters_trie.frozen()
_clusters_trie = _build_clusters_trie()


def _build_vowel_clusters_trie():
    clusters_trie: "Trie[Stenophoneme | Stroke, Stroke]" = Trie()
    for phonemes, stroke in VOWEL_CONSCIOUS_CLUSTERS.items():
        current_head = clusters_trie.ROOT
        for key in phonemes:
            current_head = clusters_trie.get_dst_node_else_create(current_head, key)

        clusters_trie.set_translation(current_head, stroke)
    return clusters_trie.frozen()
_vowel_clusters_trie = _build_vowel_clusters_trie()


@dataclass(frozen=True)
class Cluster(ABC):
    stroke: Stroke
    initial_state: "EntryBuilderState"

    @abstractmethod
    def apply(self, trie: NondeterministicTrie[str, str], translation: str, current_left: Optional[int], current_right: Optional[int]):
        ...

@dataclass(frozen=True)
class ClusterLeft(Cluster):
    def apply(self, trie: NondeterministicTrie[str, str], translation: str, current_left: Optional[int], current_right: Optional[int]):
        if current_left is None: return

        if self.initial_state.left_consonant_src_node is not None:
            trie.link_chain(self.initial_state.left_consonant_src_node, current_left, self.stroke.keys(), TransitionCostInfo(TransitionCosts.CLUSTER, translation))

        if self.initial_state.can_elide_prev_vowel_left:
            _allow_elide_previous_vowel_using_first_left_consonant(self.initial_state, self.stroke, current_left, TransitionCosts.CLUSTER)

@dataclass(frozen=True)
class ClusterRight(Cluster):
    def apply(self, trie: NondeterministicTrie[str, str], translation: str, current_left: Optional[int], current_right: Optional[int]):
        if current_right is None: return

        if self.initial_state.right_consonant_src_node is not None:
            trie.link_chain(self.initial_state.right_consonant_src_node, current_right, self.stroke.keys(), TransitionCostInfo(TransitionCosts.CLUSTER, translation))

        if self.initial_state.is_first_consonant:
            _allow_elide_previous_vowel_using_first_right_consonant(self.initial_state, self.stroke, current_right, TransitionCosts.CLUSTER)

        # if origin.right_f is not None and right_consonant_f_node is not None:
        #     trie.link_chain(origin.right_f, right_consonant_f_node, cluster_stroke.keys(), TransitionCosts.CLUSTER, translation)

        # if is_first_consonant:
        #     _allow_elide_previous_vowel_using_first_right_consonant(
        #         trie, cluster_stroke, right_consonant_f_node, origin.pre_rtl_stroke_boundary, translation, TransitionCosts.CLUSTER + TransitionCosts.F_CONSONANT,
        #     )

@dataclass
class EntryBuilderState:
    """Convenience struct for making entry state easier to pass into helper functions"""

    trie: NondeterministicTrie[str, str]
    phonemes: OutlinePhonemes
    translation: str

    # The node from which the next left consonant chord will be attached
    left_consonant_src_node: Optional[int] = None
    # The node from which the next right consonant chord will be attached
    right_consonant_src_node: Optional[int] = None
    # The latest node constructed by adding the alternate chord for a left consonant
    last_left_alt_consonant_node: Optional[int] = None
    # The latest node constructed by adding the alternate chord for a right consonant
    last_right_alt_consonant_node: Optional[int] = None

    # The node constructed by adding the previous left consonant; can be None if the previous phoneme was a vowel
    prev_left_consonant_node: Optional[int] = None

    # Two types of elision:
    #  - squish (placing vowel between two consonant chords on the same side)
    #  - boundary (placing vowel on the transition from right to left consonant chords)

    # The latest node which the previous vowel set was attached to
    left_elision_squish_src_node: Optional[int] = None
    # The latest node which the stroke boundary between a right consonant and a left consonant was attached to
    right_elision_squish_src_node: Optional[int] = None
    # The latest node constructed by adding the stroke bunnedry between a right consonant and left consonant
    left_elision_boundary_src_node: Optional[int] = None

    group_index: int = -1
    phoneme_index: int = -1

    @property
    def is_first_consonant_set(self):
        return self.group_index == 0
    
    @property
    def is_first_consonant(self):
        return self.phoneme_index == 0
    
    @property
    def consonant(self):
        return self.phonemes.get_consonant(self.group_index, self.phoneme_index)
    
    @property
    def next_consonant(self):
        return self.phonemes.get_consonant_after(self.group_index, self.phoneme_index)
    
    @property
    def last_consonant(self):
        return self.phonemes.get_consonant_before(self.group_index, self.phoneme_index)

    @property
    def n_previous_syllable_consonants(self):
        return len(self.phonemes.get_consonants(self.group_index - 1)) if self.group_index > 0 else 0

    @property
    def can_elide_prev_vowel_left(self):
        return not self.is_first_consonant_set and self.is_first_consonant and self.n_previous_syllable_consonants > 0


def add_entry(trie: NondeterministicTrie[str, str], phonemes: OutlinePhonemes, translation: str):
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


            left_consonant_node, left_alt_consonant_node = _add_left_consonant(state)


            right_consonant_node = state.right_consonant_src_node
            right_alt_consonant_node = state.last_right_alt_consonant_node
            if not state.is_first_consonant_set:
                right_consonant_node, right_alt_consonant_node, rtl_stroke_boundary_adjacent_nodes = _add_right_consonant(state, left_consonant_node)
                if rtl_stroke_boundary_adjacent_nodes is not None:
                    state.right_elision_squish_src_node, state.left_elision_boundary_src_node = rtl_stroke_boundary_adjacent_nodes

            _handle_clusters(upcoming_clusters, left_consonant_node, right_consonant_node, state, False)

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
        postvowels_node = trie.get_first_dst_node_else_create(vowels_src_node, PHONEMES_TO_CHORDS_VOWELS[vowel].rtfcre, TransitionCostInfo(0, translation))

        _handle_clusters(upcoming_clusters, state.left_consonant_src_node, state.right_consonant_src_node, state, True)


        state.right_consonant_src_node = postvowels_node
        state.left_consonant_src_node = trie.get_first_dst_node_else_create(postvowels_node, TRIE_STROKE_BOUNDARY_KEY, TransitionCostInfo(0, translation))

        if INITIAL_VOWEL_CHORD is not None and state.is_first_consonant_set and len(consonants) == 0:
            trie.link_chain(trie.ROOT, state.left_consonant_src_node, INITIAL_VOWEL_CHORD.keys(), TransitionCostInfo(0, translation))

        state.prev_left_consonant_node = None


    state.group_index = len(phonemes.nonfinals)
    for phoneme_index, consonant in enumerate(phonemes.final_consonants):
        state.phoneme_index = phoneme_index

        right_consonant_node, right_alt_consonant_node, _ = _add_right_consonant(state, None)

        _handle_clusters(upcoming_clusters, None, right_consonant_node, state, False)

        state.right_consonant_src_node = right_consonant_node
        state.last_right_alt_consonant_node = right_alt_consonant_node

        state.left_consonant_src_node = None

    if state.right_consonant_src_node is None:
        # The outline contains no vowels and is likely a brief
        return

    trie.set_translation(state.right_consonant_src_node, translation)


def _handle_clusters(
    upcoming_clusters: dict[tuple[int, int], list[Cluster]],
    left_consonant_node: Optional[int],
    right_consonant_node: Optional[int],
    
    state: EntryBuilderState,

    consider_vowels: bool,
):
    for index, cluster in (_find_vowel_clusters if consider_vowels else _find_clusters)(state.phonemes, state.group_index, state.phoneme_index, state):
        if index not in upcoming_clusters:
            upcoming_clusters[index] = [cluster]
        else:
            upcoming_clusters[index].append(cluster)

    if (state.group_index, state.phoneme_index) in upcoming_clusters:
        for cluster in upcoming_clusters[state.group_index, state.phoneme_index]:
            cluster.apply(state.trie, state.translation, left_consonant_node, right_consonant_node)

def _find_clusters(
    phonemes: OutlinePhonemes,
    start_group_index: int,
    start_phoneme_index: int,

    state: EntryBuilderState,
):
    current_head = _clusters_trie.ROOT
    current_index = (start_group_index, start_phoneme_index)
    while current_head is not None and current_index is not None:
        current_head = _clusters_trie.get_dst_node(current_head, phonemes.get_consonant(*current_index))

        if current_head is None: return

        if (result := _get_clusters_from_node(current_head, current_index, _clusters_trie, state)) is not None:
            yield result

        current_index = phonemes.increment_consonant_index(*current_index)

def _find_vowel_clusters(
    phonemes: OutlinePhonemes,
    start_group_index: int,
    start_phoneme_index: int,

    state: EntryBuilderState,
):
    current_nodes = {_vowel_clusters_trie.ROOT}
    current_index = (start_group_index, start_phoneme_index)
    while current_nodes is not None and current_index is not None:
        phoneme = phonemes[current_index]
        current_nodes = {
            node
            for current_node in current_nodes
            for node in (_vowel_clusters_trie.get_dst_node(current_node, phoneme),)
                    + ((_vowel_clusters_trie.get_dst_node(current_node, Stenophoneme.ANY_VOWEL),) if phoneme in vowel_phonemes else ())
            if node is not None
        }

        if len(current_nodes) == 0: return

        for current_node in current_nodes:
            if (result := _get_clusters_from_node(current_node, current_index, _vowel_clusters_trie, state)) is None:
                continue

            yield result

        current_index = phonemes.increment_index(*current_index)

def _get_clusters_from_node(
    node: int,
    current_index: tuple[int, int],
    clusters_trie: ReadonlyTrie[Any, Stroke],

    state: EntryBuilderState,
):
    stroke = clusters_trie.get_translation(node)
    if stroke is None: return None

    if len(stroke & LEFT_BANK_CONSONANTS_SUBSTROKE) > 0:
        return current_index, ClusterLeft(stroke, dataclasses.replace(state))
    else:
        return current_index, ClusterRight(stroke, dataclasses.replace(state))

def _add_left_consonant(state: EntryBuilderState):
    if state.left_consonant_src_node is None:
        raise Exception


    left_stroke = PHONEMES_TO_CHORDS_LEFT[state.consonant]
    left_stroke_keys = left_stroke.keys()

    left_consonant_node = state.trie.get_first_dst_node_else_create_chain(state.left_consonant_src_node, left_stroke_keys, TransitionCostInfo(0, state.translation))
    if state.left_elision_boundary_src_node is not None:
        state.trie.link_chain(state.left_elision_boundary_src_node, left_consonant_node, left_stroke_keys, TransitionCostInfo(0, state.translation))

    if state.last_left_alt_consonant_node is not None:
        state.trie.link_chain(
            state.last_left_alt_consonant_node, left_consonant_node, left_stroke_keys,
            TransitionCostInfo(TransitionCosts.ALT_CONSONANT + (TransitionCosts.VOWEL_ELISION if state.is_first_consonant else 0), state.translation)
        )

    if state.can_elide_prev_vowel_left:
        _allow_elide_previous_vowel_using_first_left_consonant(state, left_stroke, left_consonant_node)
        
    left_alt_consonant_node = _add_left_alt_consonant(state, left_consonant_node)

    return left_consonant_node, left_alt_consonant_node

def _add_left_alt_consonant(state: EntryBuilderState, left_consonant_node: int):
    if state.left_consonant_src_node is None or state.consonant not in PHONEMES_TO_CHORDS_LEFT_ALT:
        return None
    
    left_alt_stroke = PHONEMES_TO_CHORDS_LEFT_ALT[state.consonant]
    left_stroke = PHONEMES_TO_CHORDS_LEFT[state.consonant]

    should_use_alt_from_prev = (
        state.last_consonant is None
        or state.last_consonant in PHONEMES_TO_CHORDS_RIGHT and (
            can_add_stroke_on(PHONEMES_TO_CHORDS_RIGHT[state.last_consonant], left_stroke)
            or not can_add_stroke_on(PHONEMES_TO_CHORDS_RIGHT[state.last_consonant], left_alt_stroke)
        )
    )
    should_use_alt_from_next = (
        state.next_consonant is None
        or state.next_consonant in PHONEMES_TO_CHORDS_RIGHT and (
            can_add_stroke_on(left_stroke, PHONEMES_TO_CHORDS_RIGHT[state.next_consonant])
            or not can_add_stroke_on(left_alt_stroke, PHONEMES_TO_CHORDS_RIGHT[state.next_consonant])
        )
    )
    if should_use_alt_from_prev and should_use_alt_from_next:
        return None


    left_alt_stroke_keys = left_alt_stroke.keys()

    left_alt_consonant_node = state.trie.get_first_dst_node_else_create_chain(state.left_consonant_src_node, left_alt_stroke_keys, TransitionCostInfo(TransitionCosts.ALT_CONSONANT, state.translation))
    if state.left_elision_boundary_src_node is not None:
        state.trie.link_chain(state.left_elision_boundary_src_node, left_alt_consonant_node, left_alt_stroke_keys, TransitionCostInfo(0, state.translation))

    if state.last_left_alt_consonant_node is not None:
        state.trie.link_chain(
            state.last_left_alt_consonant_node, left_alt_consonant_node, left_alt_stroke_keys,
            TransitionCostInfo(TransitionCosts.ALT_CONSONANT + (TransitionCosts.VOWEL_ELISION if state.is_first_consonant else 0), state.translation)
        )

    if state.can_elide_prev_vowel_left:
        # uses original left consonant node because it is ok to continue onto the vowel if the previous consonant is present
        _allow_elide_previous_vowel_using_first_left_consonant(state, left_alt_stroke, left_consonant_node, TransitionCosts.ALT_CONSONANT, False)
        _allow_elide_previous_vowel_using_first_left_consonant(state, left_alt_stroke, left_alt_consonant_node, TransitionCosts.ALT_CONSONANT)

    return left_alt_consonant_node

def _add_right_consonant(state: EntryBuilderState, left_consonant_node: Optional[int]):
    if state.right_consonant_src_node is None or state.consonant not in PHONEMES_TO_CHORDS_RIGHT:
        return None, None, None
    

    right_stroke = PHONEMES_TO_CHORDS_RIGHT[state.consonant]
    right_stroke_keys = right_stroke.keys()
    
    right_consonant_node = state.trie.get_first_dst_node_else_create_chain(state.right_consonant_src_node, right_stroke_keys, TransitionCostInfo(0, state.translation))


    if state.last_right_alt_consonant_node is not None:
        state.trie.link_chain(state.last_right_alt_consonant_node, right_consonant_node, right_stroke_keys, TransitionCostInfo(TransitionCosts.VOWEL_ELISION if state.is_first_consonant else 0, state.translation))

    # Skeletals and right-bank consonant addons
    can_use_main_prev = (
        state.last_consonant is None
        or state.last_consonant in PHONEMES_TO_CHORDS_RIGHT and can_add_stroke_on(PHONEMES_TO_CHORDS_RIGHT[state.last_consonant], right_stroke)
    )
    if state.prev_left_consonant_node is not None and not can_use_main_prev:
        state.trie.link_chain(state.prev_left_consonant_node, right_consonant_node, right_stroke_keys, TransitionCostInfo(0, state.translation))


    pre_rtl_stroke_boundary_node = state.right_elision_squish_src_node
    rtl_stroke_boundary_node = None

    if left_consonant_node is not None and state.consonant is not Stenophoneme.DUMMY:
        pre_rtl_stroke_boundary_node = right_consonant_node
        rtl_stroke_boundary_node = state.trie.get_first_dst_node_else_create(right_consonant_node, TRIE_STROKE_BOUNDARY_KEY, TransitionCostInfo(0, state.translation))
        state.trie.link(rtl_stroke_boundary_node, left_consonant_node, TRIE_LINKER_KEY, TransitionCostInfo(0, state.translation))
        

    if state.is_first_consonant:
        _allow_elide_previous_vowel_using_first_right_consonant(state, right_stroke, right_consonant_node)


    right_consonant_f_node = _add_right_alt_consonant(state, right_consonant_node)

    rtl_stroke_boundary_adjacent_nodes = (pre_rtl_stroke_boundary_node, rtl_stroke_boundary_node)
    return right_consonant_node, right_consonant_f_node, rtl_stroke_boundary_adjacent_nodes if rtl_stroke_boundary_node is not None else None

def _add_right_alt_consonant(state: EntryBuilderState, right_consonant_node: int):
    if state.right_consonant_src_node is None or state.consonant not in PHONEMES_TO_CHORDS_RIGHT_ALT:
        return None
    
    right_alt_stroke = PHONEMES_TO_CHORDS_RIGHT_ALT[state.consonant]
    right_stroke = PHONEMES_TO_CHORDS_RIGHT[state.consonant]

    should_use_alt_from_prev = (
        state.last_consonant is None
        or state.last_consonant in PHONEMES_TO_CHORDS_RIGHT and (
            can_add_stroke_on(PHONEMES_TO_CHORDS_RIGHT[state.last_consonant], right_stroke)
            or not can_add_stroke_on(PHONEMES_TO_CHORDS_RIGHT[state.last_consonant], right_alt_stroke)
        )
    )
    should_use_alt_from_next = (
        state.next_consonant is None
        or state.next_consonant in PHONEMES_TO_CHORDS_RIGHT and (
            can_add_stroke_on(right_stroke, PHONEMES_TO_CHORDS_RIGHT[state.next_consonant])
            or not can_add_stroke_on(right_alt_stroke, PHONEMES_TO_CHORDS_RIGHT[state.next_consonant])
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
        _allow_elide_previous_vowel_using_first_right_consonant(state, right_alt_stroke, right_consonant_node, TransitionCosts.ALT_CONSONANT)

    return right_alt_consonant_node

def _allow_elide_previous_vowel_using_first_left_consonant(state: EntryBuilderState, phoneme_substroke: Stroke, left_consonant_node: int, additional_cost=0, allow_boundary_elision=True):
    # Elide a vowel by attaching a new left consonant to the previous left consonant
    if state.left_elision_squish_src_node is not None:
        state.trie.link_chain(state.left_elision_squish_src_node, left_consonant_node, phoneme_substroke.keys(), TransitionCostInfo(TransitionCosts.VOWEL_ELISION + additional_cost, state.translation))

    # Elide a vowel by placing the left consonant after a right consonant
    if state.left_elision_boundary_src_node is not None and allow_boundary_elision:
        state.trie.link_chain(state.left_elision_boundary_src_node, left_consonant_node, phoneme_substroke.keys(), TransitionCostInfo(TransitionCosts.VOWEL_ELISION + additional_cost, state.translation))

def _allow_elide_previous_vowel_using_first_right_consonant(state: EntryBuilderState, phoneme_substroke: Stroke, right_consonant_node: int, additional_cost=0):
    if state.right_elision_squish_src_node is not None:
        state.trie.link_chain(state.right_elision_squish_src_node, right_consonant_node, phoneme_substroke.keys(), TransitionCostInfo(TransitionCosts.VOWEL_ELISION + additional_cost, state.translation))

