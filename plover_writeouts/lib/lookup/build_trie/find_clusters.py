import dataclasses
from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Any

from plover.steno import Stroke

from .state import EntryBuilderState, OutlineSounds
from .rules.elision import allow_elide_previous_vowel_using_first_left_consonant, allow_elide_previous_vowel_using_first_right_consonant
from ...util.Trie import NondeterministicTrie, TransitionCostInfo, ReadonlyTrie
from ...theory.theory import amphitheory
from ...stenophoneme.Stenophoneme import Stenophoneme, vowel_phonemes

@dataclass(frozen=True)
class Cluster(ABC):
    stroke: Stroke
    initial_state: EntryBuilderState

    @abstractmethod
    def apply(self, trie: NondeterministicTrie[str, str], translation: str, current_left: "int | None", current_right: "int | None"):
        ...

@dataclass(frozen=True)
class _ClusterLeft(Cluster):
    def apply(self, trie: NondeterministicTrie[str, str], translation: str, current_left: "int | None", current_right: "int | None"):
        if current_left is None: return

        if self.initial_state.left_consonant_src_node is not None:
            trie.link_chain(self.initial_state.left_consonant_src_node, current_left, self.stroke.keys(), TransitionCostInfo(amphitheory.spec.TransitionCosts.CLUSTER, translation))

        if self.initial_state.can_elide_prev_vowel_left:
            allow_elide_previous_vowel_using_first_left_consonant(self.initial_state, self.stroke, current_left, amphitheory.spec.TransitionCosts.CLUSTER)

@dataclass(frozen=True)
class _ClusterRight(Cluster):
    def apply(self, trie: NondeterministicTrie[str, str], translation: str, current_left: "int | None", current_right: "int | None"):
        if current_right is None: return

        if self.initial_state.right_consonant_src_node is not None:
            trie.link_chain(self.initial_state.right_consonant_src_node, current_right, self.stroke.keys(), TransitionCostInfo(amphitheory.spec.TransitionCosts.CLUSTER, translation))

        if self.initial_state.is_first_consonant:
            allow_elide_previous_vowel_using_first_right_consonant(self.initial_state, self.stroke, current_right, amphitheory.spec.TransitionCosts.CLUSTER)

        # if origin.right_f is not None and right_consonant_f_node is not None:
        #     trie.link_chain(origin.right_f, right_consonant_f_node, cluster_stroke.keys(), TransitionCosts.CLUSTER, translation)

        # if is_first_consonant:
        #     _allow_elide_previous_vowel_using_first_right_consonant(
        #         trie, cluster_stroke, right_consonant_f_node, origin.pre_rtl_stroke_boundary, translation, TransitionCosts.CLUSTER + TransitionCosts.F_CONSONANT,
        #     )

def _find_clusters(
    sounds: OutlineSounds,
    start_group_index: int,
    start_phoneme_index: int,

    state: EntryBuilderState,
):
    current_head = amphitheory.clusters_trie.ROOT
    current_index = (start_group_index, start_phoneme_index)
    while current_head is not None and current_index is not None:
        current_head = amphitheory.clusters_trie.get_dst_node(current_head, sounds.get_consonant(*current_index).phoneme)

        if current_head is None: return

        if (result := _get_clusters_from_node(current_head, current_index, amphitheory.clusters_trie, state)) is not None:
            yield result

        current_index = sounds.increment_consonant_index(*current_index)

def _find_vowel_clusters(
    sounds: OutlineSounds,
    start_group_index: int,
    start_phoneme_index: int,

    state: EntryBuilderState,
):
    current_nodes = {amphitheory.vowel_clusters_trie.ROOT}
    current_index = (start_group_index, start_phoneme_index)
    while current_nodes is not None and current_index is not None:
        sound = sounds[current_index]
        current_nodes = {
            node
            for current_node in current_nodes
            for node in (amphitheory.vowel_clusters_trie.get_dst_node(current_node, sound.phoneme),)
                    + ((amphitheory.vowel_clusters_trie.get_dst_node(current_node, Stenophoneme.ANY_VOWEL),) if sound.phoneme in vowel_phonemes else ())
            if node is not None
        }

        if len(current_nodes) == 0: return

        for current_node in current_nodes:
            if (result := _get_clusters_from_node(current_node, current_index, amphitheory.vowel_clusters_trie, state)) is None:
                continue

            yield result

        current_index = sounds.increment_index(*current_index)

def _get_clusters_from_node(
    node: int,
    current_index: tuple[int, int],
    clusters_trie: ReadonlyTrie[Any, Stroke],

    state: EntryBuilderState,
):
    stroke = clusters_trie.get_translation(node)
    if stroke is None: return None

    if len(stroke & amphitheory.spec.LEFT_BANK_CONSONANTS_SUBSTROKE) > 0:
        return current_index, _ClusterLeft(stroke, dataclasses.replace(state))
    else:
        return current_index, _ClusterRight(stroke, dataclasses.replace(state))
    

def handle_clusters(
    upcoming_clusters: dict[tuple[int, int], list[Cluster]],
    left_consonant_node: "int | None",
    right_consonant_node: "int | None",
    
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