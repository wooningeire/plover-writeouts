from typing import Callable, Optional

from plover.steno import Stroke
import plover.log

from .Trie import Trie, NondeterministicTrie
from .phoneme_util import split_consonant_phonemes_greedy, possible_consonant_phoneme_splits
from .config import (
    Phoneme,
    LEFT_BANK_CONSONANTS_SUBSTROKE,
    VOWELS_SUBSTROKE,
    RIGHT_BANK_CONSONANTS_SUBSTROKE,
    ASTERISK_SUBSTROKE,
    TRIE_STROKE_BOUNDARY_KEY,
    TRIE_LINKER_KEY,
    LINKER_CHORD,
    # INITIAL_VOWEL_CHORD,
    CLUSTERS,
    PHONEMES_TO_CHORDS_LEFT,
    PHONEMES_TO_CHORDS_RIGHT,
    PHONEMES_TO_CHORDS_RIGHT_F,
    OPTIMIZE_TRIE_SPACE,
    USE_PHONEME_TRANSITIONS,
)


def _split_stroke_parts(stroke: Stroke):
    left_bank_consonants = stroke & LEFT_BANK_CONSONANTS_SUBSTROKE
    vowels = stroke & VOWELS_SUBSTROKE
    right_bank_consonants = stroke & RIGHT_BANK_CONSONANTS_SUBSTROKE
    asterisk = stroke & ASTERISK_SUBSTROKE

    return left_bank_consonants, vowels, right_bank_consonants, asterisk


_clusters_trie: Trie[Phoneme, Stroke] = Trie()
for _phonemes, _stroke in CLUSTERS.items():
    _current_head = _clusters_trie.ROOT
    for key in _phonemes:
        _current_head = _clusters_trie.get_dst_node_else_create(_current_head, key)
    
    _clusters_trie.set_translation(_current_head, _stroke)


def build_phoneme_trie(mappings: dict[str, str]):
    trie: "NondeterministicTrie[Phoneme | Stroke, str]" = NondeterministicTrie()

    for outline_steno, translation in mappings.items():
        _add_entry(trie, outline_steno, translation)

    # plover.log.debug(str(trie))
    plover.log.debug(trie.profile())

    return _create_lookup_for(trie)


def _add_entry(trie: "NondeterministicTrie[Phoneme | Stroke, str]", outline_steno: str, translation: str):
    current_head = trie.ROOT

    next_phonemes: list[Phoneme] = []

    for stroke_steno in outline_steno.split("/"):
        stroke = Stroke.from_steno(stroke_steno)


        left_bank_consonants, vowels, right_bank_consonants, asterisk = _split_stroke_parts(stroke)
        if len(asterisk) > 0:
            return


        next_phonemes.extend(split_consonant_phonemes_greedy(left_bank_consonants))

        if len(vowels) > 0:
            if len(next_phonemes) > 0:
                last_prevowels_node = current_head
                current_head = trie.get_first_dst_node_else_create(current_head, next_phonemes[0])
                trie.link(last_prevowels_node, current_head, next_phonemes[0])

                current_head = trie.get_first_dst_node_else_create_chain(current_head, next_phonemes[1:])
            next_phonemes = []

            trie.get_first_dst_node_else_create(current_head, vowels)

        next_phonemes.extend(split_consonant_phonemes_greedy(right_bank_consonants))

    trie.set_translation(current_head, translation)


def _update_cluster_tracking(
    cluster_consonants: list[tuple[Phoneme, Optional[int], Optional[int], Optional[int]]],
    cluster_consonant_nodes: list[int],
    new_consonant: Phoneme,
    prev_left_consonant_node: Optional[int],
    last_right_consonant_node: Optional[int],
    last_right_consonant_f_node: Optional[int],
):
    # update cluster identification
    new_cluster_consonants: list[tuple[Phoneme, Optional[int], Optional[int], Optional[int]]] = []
    new_cluster_consonant_nodes: list[int] = []
    for consonant_and_positions, cluster_node in zip(
        cluster_consonants + [(new_consonant, prev_left_consonant_node, last_right_consonant_node, last_right_consonant_f_node)],
        cluster_consonant_nodes + [_clusters_trie.ROOT],
    ):
        new_cluster_node = _clusters_trie.get_dst_node(cluster_node, new_consonant)
        if new_cluster_node is None: continue

        new_cluster_consonants.append(consonant_and_positions)
        new_cluster_consonant_nodes.append(new_cluster_node)

    return new_cluster_consonants, new_cluster_consonant_nodes


def _create_lookup_for(trie: "NondeterministicTrie[Phoneme | Stroke, str]") -> Callable[[tuple[str, ...]], Optional[str]]:
    def lookup(outline: tuple[Stroke, ...], current_nodes: set[int]):
        if len(outline) == 0:
            return trie.get_translation(current_nodes)

        stroke = outline[0]
        if len(stroke) == 0:
            return None
            

        left_bank_consonants, vowels, right_bank_consonants, asterisk = _split_stroke_parts(stroke)

        phoneme_seqs_left = possible_consonant_phoneme_splits(left_bank_consonants)
        try:
            while True:
                phonemes_left = next(phoneme_seqs_left)
                new_nodes_left = trie.get_dst_nodes_chain(current_nodes, phonemes_left)
                if len(new_nodes_left) == 0:
                    continue


                new_nodes_vowels = trie.get_dst_nodes(new_nodes_left, vowels)
                if len(new_nodes_vowels) == 0:
                    continue

                phoneme_seqs_right = possible_consonant_phoneme_splits(right_bank_consonants)
                try:
                    while True:
                        phonemes_right = next(phoneme_seqs_right)
                        new_nodes_right = trie.get_dst_nodes_chain(new_nodes_vowels, phonemes_right)
                        if len(new_nodes_right) == 0:
                            continue

                        return lookup(outline[1:], new_nodes_right)

                except StopIteration:
                    pass

        except StopIteration:
            pass


    return lambda stroke_stenos: lookup(tuple(Stroke.from_steno(stroke_steno) for stroke_steno in stroke_stenos), {trie.ROOT})