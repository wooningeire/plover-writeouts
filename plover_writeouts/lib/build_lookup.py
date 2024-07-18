from typing import Callable, Iterable, NamedTuple, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod

from plover.steno import Stroke
import plover.log

from .Trie import Transition, TransitionCostInfo, Trie, NondeterministicTrie
from .phoneme_util import split_consonant_phonemes
from .config import (
    Phoneme,
    LEFT_BANK_CONSONANTS_SUBSTROKE,
    VOWELS_SUBSTROKE,
    RIGHT_BANK_CONSONANTS_SUBSTROKE,
    ASTERISK_SUBSTROKE,
    TRIE_STROKE_BOUNDARY_KEY,
    TRIE_LINKER_KEY,
    LINKER_CHORD,
    INITIAL_VOWEL_CHORD,
    VARIATION_CYCLER_STROKE,
    # VARIATION_CYCLER_STROKE_BACKWARD,
    PROHIBITED_STROKES,
    CLUSTERS,
    PHONEMES_TO_CHORDS_LEFT,
    PHONEMES_TO_CHORDS_RIGHT,
    PHONEMES_TO_CHORDS_RIGHT_F,
    DIPHTHONG_TRANSITIONS_BY_FIRST_VOWEL,
    OPTIMIZE_TRIE_SPACE,
    TransitionCosts,
)


def _split_stroke_parts(stroke: Stroke):
    left_bank_consonants = stroke & LEFT_BANK_CONSONANTS_SUBSTROKE
    vowels = stroke & VOWELS_SUBSTROKE
    right_bank_consonants = stroke & RIGHT_BANK_CONSONANTS_SUBSTROKE
    asterisk = stroke & ASTERISK_SUBSTROKE

    return left_bank_consonants, vowels, right_bank_consonants, asterisk


def _build_clusters_trie():
    clusters_trie: Trie[Phoneme, Stroke] = Trie()
    for phonemes, stroke in CLUSTERS.items():
        current_head = clusters_trie.ROOT
        for key in phonemes:
            current_head = clusters_trie.get_dst_node_else_create(current_head, key)

        clusters_trie.set_translation(current_head, stroke)
    return clusters_trie.frozen()
_clusters_trie = _build_clusters_trie()


@dataclass(frozen=True)
class Cluster(ABC):
    stroke: Stroke
    can_elide_previous_vowel: bool

    @abstractmethod
    def apply(self, trie: NondeterministicTrie[str, str], translation: str, current_left: Optional[int], current_right: Optional[int]):
        ...

@dataclass(frozen=True)
class ClusterLeft(Cluster):
    left: Optional[int]
    prevowel: Optional[int]
    rtl_stroke_boundary: Optional[int]

    def apply(self, trie: NondeterministicTrie[str, str], translation: str, current_left: Optional[int], current_right: Optional[int]):
        if current_left is None: return

        if self.left is not None:
            trie.link_chain(self.left, current_left, self.stroke.keys(), TransitionCostInfo(TransitionCosts.CLUSTER, translation))

        if self.can_elide_previous_vowel:
            _allow_elide_previous_vowel_using_first_left_consonant(
                trie, self.stroke, current_left, self.prevowel, self.rtl_stroke_boundary, translation, TransitionCosts.CLUSTER,
            )

@dataclass(frozen=True)
class ClusterRight(Cluster):
    right: Optional[int]
    right_f: Optional[int]
    pre_rtl_stroke_boundary: Optional[int]

    def apply(self, trie: NondeterministicTrie[str, str], translation: str, current_left: Optional[int], current_right: Optional[int]):
        if current_right is None: return

        if self.right is not None:
            trie.link_chain(self.right, current_right, self.stroke.keys(), TransitionCostInfo(TransitionCosts.CLUSTER, translation))

        if self.can_elide_previous_vowel:
            _allow_elide_previous_vowel_using_first_right_consonant(
                trie, self.stroke, current_right, self.pre_rtl_stroke_boundary, translation, TransitionCosts.CLUSTER,
            )

        # if origin.right_f is not None and right_consonant_f_node is not None:
        #     trie.link_chain(origin.right_f, right_consonant_f_node, cluster_stroke.keys(), TransitionCosts.CLUSTER, translation)

        # if is_first_consonant:
        #     _allow_elide_previous_vowel_using_first_right_consonant(
        #         trie, cluster_stroke, right_consonant_f_node, origin.pre_rtl_stroke_boundary, translation, TransitionCosts.CLUSTER + TransitionCosts.F_CONSONANT,
        #     )


class ConsonantVowelGroup(NamedTuple):
    consonants: tuple[Phoneme, ...]
    vowel: Stroke

@dataclass(frozen=True)
class OutlinePhonemes:
    nonfinals: tuple[ConsonantVowelGroup, ...]
    final_consonants: tuple[Phoneme, ...]

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
        if phoneme_index == len(self.nonfinals):
            return self.nonfinals[group_index].vowel
        return self.nonfinals[group_index].consonants[phoneme_index]
    
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


@dataclass(frozen=True)
class AnnotatedPhoneme:
    phoneme: Phoneme



def build_lookup(mappings: dict[str, str]):
    trie: NondeterministicTrie[str, str] = NondeterministicTrie()

    for outline_steno, translation in mappings.items():
        phonemes = _get_outline_phonemes(Stroke.from_steno(steno) for steno in outline_steno.split("/"))
        if phonemes is None:
            continue
        _add_entry(trie, phonemes, translation)

    # plover.log.debug(str(trie))
    return _create_lookup_for(trie)

def _get_outline_phonemes(outline: Iterable[Stroke]):
    consonant_vowel_groups: list[ConsonantVowelGroup] = []

    current_group_consonants: list[Phoneme] = []
    
    for stroke in outline:
        left_bank_consonants, vowels, right_bank_consonants, asterisk = _split_stroke_parts(stroke)
        if len(asterisk) > 0:
            return None

        current_group_consonants.extend(split_consonant_phonemes(left_bank_consonants))

        if len(vowels) > 0:
            is_diphthong_transition = len(consonant_vowel_groups) > 0 and len(current_group_consonants) == 0
            if is_diphthong_transition and (prev_vowel := consonant_vowel_groups[-1].vowel) in DIPHTHONG_TRANSITIONS_BY_FIRST_VOWEL:
                current_group_consonants.append(DIPHTHONG_TRANSITIONS_BY_FIRST_VOWEL[prev_vowel])

            consonant_vowel_groups.append(ConsonantVowelGroup(tuple(current_group_consonants), vowels))

            current_group_consonants = []

        current_group_consonants.extend(split_consonant_phonemes(right_bank_consonants))

    return OutlinePhonemes(tuple(consonant_vowel_groups), tuple(current_group_consonants))

def _add_entry(trie: NondeterministicTrie[str, str], phonemes: OutlinePhonemes, translation: str):
    # The node from which the next left consonant chord will be attached
    next_left_consonant_src_node: Optional[int] = trie.ROOT
    # The node from which the next right consonant chord will be attached
    next_right_consonant_src_node: Optional[int] = None
    # The latest node constructed by adding the alternate chord for a right consonant
    last_right_consonant_f_node: Optional[int] = None

    # The node constructed by adding the previous left consonant; None also if the previous phoneme was a vowel
    prev_left_consonant_node: Optional[int] = None

    # The latest node which the previous vowel set was attached to
    last_prevowel_node: Optional[int] = None
    # The latest node which the stroke boundary between a right consonant and a left consonant was attached to
    last_pre_rtl_stroke_boundary_node: Optional[int] = None
    # The latest node constructed by adding the stroke bunnedry between a right consonant and left consonant
    last_rtl_stroke_boundary_node: Optional[int] = None

    upcoming_clusters: dict[tuple[int, int], list[Cluster]] = {}

    for group_index, (consonants, vowel) in enumerate(phonemes.nonfinals):
        is_first_consonant_set = group_index == 0

        vowels_src_node: Optional[int] = None
        if len(consonants) == 0 and not is_first_consonant_set:
            vowels_src_node = trie.get_first_dst_node_else_create(next_left_consonant_src_node, TRIE_LINKER_KEY)

        for phoneme_index, consonant in enumerate(consonants):
            is_first_consonant = phoneme_index == 0


            left_consonant_node = _add_left_consonant(
                trie, consonant, next_left_consonant_src_node, last_rtl_stroke_boundary_node, last_prevowel_node, is_first_consonant,
                is_first_consonant_set, len(phonemes.get_consonants(group_index - 1)) if group_index > 0 else 0, translation,
            )
            right_consonant_node = next_right_consonant_src_node
            right_consonant_f_node = last_right_consonant_f_node


            if not is_first_consonant_set:
                right_consonant_node, right_consonant_f_node, rtl_stroke_boundary_adjacent_nodes = _add_right_consonant(
                    trie, consonant, next_right_consonant_src_node, last_right_consonant_f_node, left_consonant_node, prev_left_consonant_node,
                    last_pre_rtl_stroke_boundary_node, phoneme_index == 0, translation,
                )
                if rtl_stroke_boundary_adjacent_nodes is not None:
                    last_pre_rtl_stroke_boundary_node, last_rtl_stroke_boundary_node = rtl_stroke_boundary_adjacent_nodes

            _handle_clusters(
                trie, phonemes, group_index, phoneme_index, upcoming_clusters, translation, left_consonant_node, right_consonant_node,

                next_left_consonant_src_node,
                last_prevowel_node,
                last_rtl_stroke_boundary_node,
                next_right_consonant_src_node,
                last_right_consonant_f_node,
                last_pre_rtl_stroke_boundary_node,
            )

            next_left_consonant_src_node = prev_left_consonant_node = left_consonant_node
            next_right_consonant_src_node = right_consonant_node
            last_right_consonant_f_node = right_consonant_f_node

        last_prevowel_node = next_left_consonant_src_node
        # can't really do anything all that special with vowels, so only proceed through a vowel transition
        # if it matches verbatim
        if vowels_src_node is None:
            vowels_src_node = next_left_consonant_src_node
        postvowels_node = trie.get_first_dst_node_else_create(vowels_src_node, vowel.rtfcre)


        next_right_consonant_src_node = postvowels_node
        next_left_consonant_src_node = trie.get_first_dst_node_else_create(postvowels_node, TRIE_STROKE_BOUNDARY_KEY)

        if INITIAL_VOWEL_CHORD is not None and is_first_consonant_set and len(consonants) == 0:
            trie.link_chain(trie.ROOT, next_left_consonant_src_node, INITIAL_VOWEL_CHORD.keys())

        prev_left_consonant_node = None


    group_index = len(phonemes.nonfinals)
    for phoneme_index, consonant in enumerate(phonemes.final_consonants):
        right_consonant_node, right_consonant_f_node, _ = _add_right_consonant(
            trie, consonant, next_right_consonant_src_node, last_right_consonant_f_node, None, prev_left_consonant_node,
            last_pre_rtl_stroke_boundary_node, phoneme_index == 0, translation,
        )

        _handle_clusters(
            trie, phonemes, group_index, phoneme_index, upcoming_clusters, translation, None, right_consonant_node,

            next_left_consonant_src_node,
            last_prevowel_node,
            last_rtl_stroke_boundary_node,
            next_right_consonant_src_node,
            last_right_consonant_f_node,
            last_pre_rtl_stroke_boundary_node,
        )

        next_right_consonant_src_node = right_consonant_node
        last_right_consonant_f_node = right_consonant_f_node

        next_left_consonant_src_node = None

    if next_right_consonant_src_node is None:
        return

    trie.set_translation(next_right_consonant_src_node, translation)


def _handle_clusters(
    trie: NondeterministicTrie[str, str],
    phonemes: OutlinePhonemes,
    group_index: int,
    phoneme_index: int,
    upcoming_clusters: dict[tuple[int, int], list[Cluster]],
    translation: str,
    left_consonant_node: Optional[int],
    right_consonant_node: Optional[int],
    
    left: Optional[int],
    prevowel: Optional[int],
    rtl_stroke_boundary: Optional[int],
    right: Optional[int],
    right_f: Optional[int],
    pre_rtl_stroke_boundary: Optional[int],
):
    for index, cluster in _find_clusters(
        phonemes, group_index, phoneme_index,

        left,
        prevowel,
        rtl_stroke_boundary,
        right,
        right_f,
        pre_rtl_stroke_boundary,
    ):
        if index not in upcoming_clusters:
            upcoming_clusters[index] = [cluster]
        else:
            upcoming_clusters[index].append(cluster)

    if (group_index, phoneme_index) in upcoming_clusters:
        for cluster in upcoming_clusters[group_index, phoneme_index]:
            cluster.apply(trie, translation, left_consonant_node, right_consonant_node)

def _find_clusters(
    phonemes: OutlinePhonemes,
    start_group_index: int,
    start_phoneme_index: int,

    left: Optional[int],
    prevowel: Optional[int],
    rtl_stroke_boundary: Optional[int],
    right: Optional[int],
    right_f: Optional[int],
    pre_rtl_stroke_boundary: Optional[int],
):
    current_head = _clusters_trie.ROOT
    current_index = (start_group_index, start_phoneme_index)
    while current_head is not None and current_index is not None:
        current_head = _clusters_trie.get_dst_node(current_head, phonemes.get_consonant(current_index[0], current_index[1]))
        if current_head is None: return

        if (stroke := _clusters_trie.get_translation(current_head)) is not None:
            if len(stroke & LEFT_BANK_CONSONANTS_SUBSTROKE) > 0:
                yield current_index, ClusterLeft(
                    stroke,
                    start_group_index > 0 and start_phoneme_index == 0 and len(phonemes.get_consonants(start_group_index - 1)) == 0,
                    left, prevowel, rtl_stroke_boundary
                )
            else:
                yield current_index, ClusterRight(
                    stroke,
                    start_phoneme_index == 0,
                    right, right_f, pre_rtl_stroke_boundary
                )

        current_index = phonemes.increment_consonant_index(current_index[0], current_index[1])

def _add_left_consonant(
    trie: NondeterministicTrie[str, str],
    consonant: Phoneme,
    next_left_consonant_src_node: int,
    last_rtl_stroke_boundary_node: Optional[int],
    last_prevowel_node: Optional[int],
    is_first_consonant: bool,
    is_first_consonant_set: bool,
    n_previous_syllable_consonants: int,
    translation: str,
):
    left_stroke = PHONEMES_TO_CHORDS_LEFT[consonant]
    left_stroke_keys = left_stroke.keys()

    left_consonant_node = trie.get_first_dst_node_else_create_chain(next_left_consonant_src_node, left_stroke_keys)
    if last_rtl_stroke_boundary_node is not None:
        trie.link_chain(last_rtl_stroke_boundary_node, left_consonant_node, left_stroke_keys)

    if not is_first_consonant_set and is_first_consonant and n_previous_syllable_consonants > 0:
        _allow_elide_previous_vowel_using_first_left_consonant(
            trie, left_stroke, left_consonant_node, last_prevowel_node, last_rtl_stroke_boundary_node, translation,
        )

    return left_consonant_node

def _add_right_consonant(
    trie: NondeterministicTrie[str, str],
    consonant: Phoneme,
    next_right_consonant_src_node: Optional[int],
    last_right_consonant_f_node: Optional[int],
    left_consonant_node: Optional[int],
    prev_left_consonant_node: Optional[int],
    last_pre_rtl_stroke_boundary_node: Optional[int],
    is_first_consonant: bool,
    translation: str,
):
    if next_right_consonant_src_node is None or consonant not in PHONEMES_TO_CHORDS_RIGHT:
        return None, None, None
    

    right_stroke = PHONEMES_TO_CHORDS_RIGHT[consonant]
    right_stroke_keys = right_stroke.keys()
    
    right_consonant_node = trie.get_first_dst_node_else_create_chain(next_right_consonant_src_node, right_stroke_keys)
    if last_right_consonant_f_node is not None:
        trie.link_chain(last_right_consonant_f_node, right_consonant_node, right_stroke_keys, TransitionCostInfo(TransitionCosts.VOWEL_ELISION if is_first_consonant else 0, translation))

    # Skeletals and right-bank consonant addons
    if prev_left_consonant_node is not None:
        trie.link_chain(prev_left_consonant_node, right_consonant_node, right_stroke_keys)


    pre_rtl_stroke_boundary_node = last_pre_rtl_stroke_boundary_node
    rtl_stroke_boundary_node = None

    if left_consonant_node is not None and consonant is not Phoneme.DUMMY:
        pre_rtl_stroke_boundary_node = right_consonant_node
        rtl_stroke_boundary_node = trie.get_first_dst_node_else_create(right_consonant_node, TRIE_STROKE_BOUNDARY_KEY)
        trie.link(rtl_stroke_boundary_node, left_consonant_node, TRIE_LINKER_KEY)
        

    if is_first_consonant:
        _allow_elide_previous_vowel_using_first_right_consonant(trie, right_stroke, right_consonant_node, last_pre_rtl_stroke_boundary_node, translation)


    right_consonant_f_node = _add_right_f_consonant(
        trie, consonant, next_right_consonant_src_node, last_right_consonant_f_node, prev_left_consonant_node,
        last_pre_rtl_stroke_boundary_node, is_first_consonant, translation
    )

    rtl_stroke_boundary_adjacent_nodes = (pre_rtl_stroke_boundary_node, rtl_stroke_boundary_node)
    return right_consonant_node, right_consonant_f_node, rtl_stroke_boundary_adjacent_nodes if rtl_stroke_boundary_node is not None else None

def _add_right_f_consonant(
    trie: NondeterministicTrie[str, str],
    consonant: Phoneme,
    next_right_consonant_src_node: int,
    last_right_consonant_f_node: Optional[int],
    prev_left_consonant_node: Optional[int],
    last_pre_rtl_stroke_boundary_node: Optional[int],
    is_first_consonant: bool,
    translation: str,
):
    if consonant not in PHONEMES_TO_CHORDS_RIGHT_F:
        return None
    
    right_f_stroke = PHONEMES_TO_CHORDS_RIGHT_F[consonant]
    right_f_stroke_keys = right_f_stroke.keys()


    right_consonant_f_node = trie.get_first_dst_node_else_create_chain(next_right_consonant_src_node, right_f_stroke_keys, TransitionCostInfo(TransitionCosts.F_CONSONANT, translation))
    if last_right_consonant_f_node is not None:
        trie.link_chain(
            last_right_consonant_f_node, right_consonant_f_node, right_f_stroke_keys,
            TransitionCostInfo(TransitionCosts.F_CONSONANT + (TransitionCosts.VOWEL_ELISION if is_first_consonant else 0), translation)
        )

    if prev_left_consonant_node is not None:
        trie.link_chain(prev_left_consonant_node, right_consonant_f_node, right_f_stroke_keys)
        
    if is_first_consonant:
        _allow_elide_previous_vowel_using_first_right_consonant(
            trie, right_f_stroke, right_consonant_f_node, last_pre_rtl_stroke_boundary_node, translation, TransitionCosts.F_CONSONANT,
        )

    return right_consonant_f_node

def _allow_elide_previous_vowel_using_first_left_consonant(
    trie: NondeterministicTrie[str, str],
    phoneme_substroke: Stroke,
    left_consonant_node: int,
    last_prevowels_node: Optional[int],
    last_rtl_stroke_boundary_node: Optional[int],
    translation: str,
    additional_cost=0,
):
    if last_prevowels_node is not None:
        trie.link_chain(last_prevowels_node, left_consonant_node, phoneme_substroke.keys(), TransitionCostInfo(TransitionCosts.VOWEL_ELISION + additional_cost, translation))

    if last_rtl_stroke_boundary_node is not None:
        trie.link_chain(last_rtl_stroke_boundary_node, left_consonant_node, phoneme_substroke.keys(), TransitionCostInfo(TransitionCosts.VOWEL_ELISION + additional_cost, translation))

def _allow_elide_previous_vowel_using_first_right_consonant(
    trie: NondeterministicTrie[str, str],
    phoneme_substroke: Stroke,
    right_consonant_node: int,
    last_pre_rtl_stroke_boundary_node: Optional[int],
    translation: str,
    additional_cost=0,
):
    if last_pre_rtl_stroke_boundary_node is not None:
        trie.link_chain(last_pre_rtl_stroke_boundary_node, right_consonant_node, phoneme_substroke.keys(), TransitionCostInfo(TransitionCosts.VOWEL_ELISION + additional_cost, translation))


def _create_lookup_for(trie:  NondeterministicTrie[str, str]):
    def lookup(stroke_stenos: tuple[str, ...]):
        # plover.log.debug("")
        # plover.log.debug("new lookup")

        current_nodes = {
            trie.ROOT: (),
        }
        n_variation = 0

        asterisk = Stroke.from_integer(0)

        for i, stroke_steno in enumerate(stroke_stenos):
            stroke = Stroke.from_steno(stroke_steno)
            if len(stroke) == 0:
                return None
            
            if stroke in PROHIBITED_STROKES:
                return None
            
            if stroke == VARIATION_CYCLER_STROKE:
                n_variation += 1
                continue
            # if stroke == VARIATION_CYCLER_STROKE_BACKWARD:
            #     n_variation -= 1
            #     continue

            if n_variation > 0:
                return None
            
            if i > 0:
                # plover.log.debug(current_nodes)
                # plover.log.debug(TRIE_STROKE_BOUNDARY_KEY)
                current_nodes = trie.get_dst_nodes(current_nodes, TRIE_STROKE_BOUNDARY_KEY)
                if len(current_nodes) == 0:
                    return None

            left_bank_consonants, vowels, right_bank_consonants, asterisk = _split_stroke_parts(stroke)

            if len(left_bank_consonants) > 0:
                # plover.log.debug(current_nodes)
                # plover.log.debug(left_bank_consonants.keys())
                if len(asterisk) > 0:
                    for key in left_bank_consonants.keys():
                        current_nodes = trie.get_dst_nodes(current_nodes, key)
                        # plover.log.debug(f"\t{key}\t {current_nodes}")
                        current_nodes |= trie.get_dst_nodes_chain(current_nodes, asterisk.keys())
                        # plover.log.debug(f"\t{asterisk.rtfcre}\t {current_nodes}")
                        if len(current_nodes) == 0:
                            return None
                elif left_bank_consonants == LINKER_CHORD:
                    current_nodes = trie.get_dst_nodes_chain(current_nodes, left_bank_consonants.keys()) | trie.get_dst_nodes(current_nodes, TRIE_LINKER_KEY)
                else:
                    current_nodes = trie.get_dst_nodes_chain(current_nodes, left_bank_consonants.keys())

                if len(current_nodes) == 0:
                    return None

            if len(vowels) > 0:
                # plover.log.debug(current_nodes)
                # plover.log.debug(vowels.rtfcre)
                current_nodes = trie.get_dst_nodes(current_nodes, vowels.rtfcre)
                if len(current_nodes) == 0:
                    return None

            if len(right_bank_consonants) > 0:
                # plover.log.debug(current_nodes)
                # plover.log.debug(right_bank_consonants.keys())
                if len(asterisk) > 0:
                    for key in right_bank_consonants.keys():
                        current_nodes |= trie.get_dst_nodes_chain(current_nodes, asterisk.keys())
                        # plover.log.debug(f"\t{asterisk.rtfcre}\t {current_nodes}")
                        current_nodes = trie.get_dst_nodes(current_nodes, key)
                        # plover.log.debug(f"\t{key}\t {current_nodes}")
                        if len(current_nodes) == 0:
                            return None
                else:
                    current_nodes = trie.get_dst_nodes_chain(current_nodes, right_bank_consonants.keys())
                    
                if len(current_nodes) == 0:
                    return None
                
        translation_choices = sorted(trie.get_translations_and_costs(current_nodes).items(), key=lambda cost_info: cost_info[1])
        if len(translation_choices) == 0: return None

        first_choice = translation_choices[0]
        if len(asterisk) == 0:
            return _nth_variation(translation_choices, n_variation)
        else:
            for transition in reversed(first_choice[1][1]):
                if trie.transition_has_key(transition, TRIE_STROKE_BOUNDARY_KEY): break
                if not trie.transition_has_key(transition, ASTERISK_SUBSTROKE.rtfcre): continue

                return _nth_variation(translation_choices, n_variation)

        return _nth_variation(translation_choices, n_variation + 1) if len(translation_choices) > 1 else None

    return lookup

def _nth_variation(choices: list[tuple[str, tuple[float, tuple[Transition, ...]]]], n_variation: int):
    # index = n_variation % (len(choices) + 1)
    # return choices[index][0] if index != len(choices) else None
    return choices[n_variation % len(choices)][0]