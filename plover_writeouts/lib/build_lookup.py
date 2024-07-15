from typing import Callable, Optional
from dataclasses import dataclass

from plover.steno import Stroke
import plover.log

from .Trie import Trie, NondeterministicTrie, ReadonlyNondeterministicTrie
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
    # INITIAL_VOWEL_CHORD,
    CLUSTERS,
    PHONEMES_TO_CHORDS_LEFT,
    PHONEMES_TO_CHORDS_RIGHT,
    PHONEMES_TO_CHORDS_RIGHT_F,
    DIPHTHONG_TRANSITIONS_BY_FIRST_VOWEL,
    OPTIMIZE_TRIE_SPACE,
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


@dataclass
class ClusterOrigin:
    left: Optional[int]
    prevowel: Optional[int]
    rtl_stroke_boundary: Optional[int]
    pre_rtl_stroke_boundary: Optional[int]
    right: Optional[int]
    right_f: Optional[int]


def build_lookup(mappings: dict[str, str]):
    trie: NondeterministicTrie[str, str] = NondeterministicTrie()

    for outline_steno, translation in mappings.items():
        _add_entry(trie, outline_steno, translation)

    # plover.log.debug(str(trie.optimized()))
    return _create_lookup_for(trie.optimized().frozen() if OPTIMIZE_TRIE_SPACE else trie)

def _add_entry(trie: NondeterministicTrie[str, str], outline_steno: str, translation: str):
    current_syllable_consonants: list[Phoneme] = []
    n_previous_syllable_consonants = 0

    # The node from which the next left consonant chord will be attached
    next_left_consonant_src_node: Optional[int] = trie.ROOT
    # The node from which the next right consonant chord will be attached
    next_right_consonant_src_node: Optional[int] = None
    # The latest node constructed by adding the alternate chord for a right consonant
    last_right_consonant_f_node: Optional[int] = None

    # The node constructed by adding the previous left consonant; None also if the previous phoneme was a vowel
    prev_left_consonant_node: Optional[int] = None
    prev_vowel: Optional[Stroke] = None

    # The latest node which the previous vowel set was attached to
    last_prevowel_node: Optional[int] = None
    # The latest node which the stroke boundary between a right consonant and a left consonant was attached to
    last_pre_rtl_stroke_boundary_node: Optional[int] = None
    # The latest node constructed by adding the stroke bunnedry between a right consonant and left consonant
    last_rtl_stroke_boundary_node: Optional[int] = None

    cluster_consonants: list[tuple[Phoneme, ClusterOrigin, int]] = []

    for stroke_steno in outline_steno.split("/"):
        stroke = Stroke.from_steno(stroke_steno)


        left_bank_consonants, vowels, right_bank_consonants, asterisk = _split_stroke_parts(stroke)
        if len(asterisk) > 0:
            return


        current_syllable_consonants.extend(split_consonant_phonemes(left_bank_consonants))


        if len(vowels) > 0:
            vowels_src_node: Optional[int] = None
            if len(current_syllable_consonants) == 0 and prev_vowel is not None:
                if prev_vowel in DIPHTHONG_TRANSITIONS_BY_FIRST_VOWEL:
                    current_syllable_consonants.append(DIPHTHONG_TRANSITIONS_BY_FIRST_VOWEL[prev_vowel])
                else:
                    vowels_src_node = trie.get_first_dst_node_else_create(next_left_consonant_src_node, TRIE_LINKER_KEY)

            # plover.log.debug(current_syllable_consonants)
            for i, consonant in enumerate(current_syllable_consonants):
                cluster_consonants = _update_cluster_tracking(
                    cluster_consonants,
                    consonant,
                    ClusterOrigin(
                        next_left_consonant_src_node,
                        last_prevowel_node,
                        last_rtl_stroke_boundary_node,
                        last_pre_rtl_stroke_boundary_node,
                        next_right_consonant_src_node,
                        last_right_consonant_f_node,
                    ),
                )


                is_first_consonant = i == 0


                left_consonant_node = _add_left_consonant(
                    trie, consonant, next_left_consonant_src_node, last_rtl_stroke_boundary_node, last_prevowel_node, is_first_consonant,
                    prev_vowel is None, n_previous_syllable_consonants, cluster_consonants,
                )


                if prev_vowel is not None:
                    next_right_consonant_src_node, last_right_consonant_f_node, rtl_stroke_boundary_adjacent_nodes = _add_right_consonant(
                        trie, consonant, next_right_consonant_src_node, last_right_consonant_f_node, left_consonant_node, prev_left_consonant_node,
                        last_pre_rtl_stroke_boundary_node, i == 0, cluster_consonants,
                    )
                    if rtl_stroke_boundary_adjacent_nodes is not None:
                        last_pre_rtl_stroke_boundary_node, last_rtl_stroke_boundary_node = rtl_stroke_boundary_adjacent_nodes

                next_left_consonant_src_node = prev_left_consonant_node = left_consonant_node

            n_previous_syllable_consonants = len(current_syllable_consonants)
            current_syllable_consonants = []

            last_prevowel_node = next_left_consonant_src_node
            # can't really do anything all that special with vowels, so only proceed through a vowel transition
            # if it matches verbatim
            if vowels_src_node is None:
                vowels_src_node = next_left_consonant_src_node
            postvowels_node = trie.get_first_dst_node_else_create(vowels_src_node, vowels.rtfcre)
            prev_vowel = vowels


            next_right_consonant_src_node = postvowels_node
            next_left_consonant_src_node = trie.get_first_dst_node_else_create(postvowels_node, TRIE_STROKE_BOUNDARY_KEY)

            # if INITIAL_VOWEL_CHORD is not None and n_previous_syllable_consonants == 0 and is_starting_consonants:
            #     trie.link_chain(trie.ROOT, next_left_consonant_src_node, INITIAL_VOWEL_CHORD.keys())

            prev_left_consonant_node = None


        current_syllable_consonants.extend(split_consonant_phonemes(right_bank_consonants))


    for i, consonant in enumerate(current_syllable_consonants):
        next_right_consonant_src_node, last_right_consonant_f_node, _ = _add_right_consonant(
            trie, consonant, next_right_consonant_src_node, last_right_consonant_f_node, None, prev_left_consonant_node, last_pre_rtl_stroke_boundary_node,
            i == 0, cluster_consonants,
        )

        next_left_consonant_src_node = None

    if next_right_consonant_src_node is None:
        return

    trie.set_translation(next_right_consonant_src_node, translation)


def _update_cluster_tracking(
    cluster_consonants: list[tuple[Phoneme, ClusterOrigin, int]],
    new_consonant: Phoneme,
    new_origin: ClusterOrigin,
):
    # update cluster identification
    new_cluster_consonants: list[tuple[Phoneme, ClusterOrigin, int]] = []
    for consonant, origin, node in cluster_consonants + [(new_consonant, new_origin, _clusters_trie.ROOT)]:
        new_cluster_node = _clusters_trie.get_dst_node(node, new_consonant)
        if new_cluster_node is None: continue

        new_cluster_consonants.append((consonant, origin, new_cluster_node))

    return new_cluster_consonants

def _if_cluster_found(
    cluster_consonants: list[tuple[Phoneme, ClusterOrigin, int]],
):
    def handler(fn: Callable[[Phoneme, ClusterOrigin, Stroke], None]):
        for consonant, origin, cluster_node in cluster_consonants:
            found_cluster = _clusters_trie.get_translation(cluster_node)
            if found_cluster is None: continue

            fn(consonant, origin, found_cluster)

    return handler

def _add_left_consonant(
    trie: NondeterministicTrie[str, str],
    consonant: Phoneme,
    next_left_consonant_src_node: int,
    last_rtl_stroke_boundary_node: Optional[int],
    last_prevowel_node: Optional[int],
    is_first_consonant: bool,
    is_first_consonant_set: bool,
    n_previous_syllable_consonants: int,
    cluster_consonants: list[tuple[Phoneme, ClusterOrigin, int]],
):
    left_stroke = PHONEMES_TO_CHORDS_LEFT[consonant]
    left_stroke_keys = left_stroke.keys()

    left_consonant_node = trie.get_first_dst_node_else_create_chain(next_left_consonant_src_node, left_stroke_keys)
    if last_rtl_stroke_boundary_node is not None:
        trie.link_chain(last_rtl_stroke_boundary_node, left_consonant_node, left_stroke_keys)

    can_elide_previous_vowel = not is_first_consonant_set and is_first_consonant and n_previous_syllable_consonants > 0

    @_if_cluster_found(cluster_consonants)
    def add_cluster(consonant: Phoneme, origin: ClusterOrigin, cluster_stroke: Stroke):
        if len(cluster_stroke & LEFT_BANK_CONSONANTS_SUBSTROKE) == 0: return
        
        if origin.left is not None:
            trie.link_chain(origin.left, left_consonant_node, cluster_stroke.keys())

        if can_elide_previous_vowel:
            _allow_elide_previous_vowel_using_first_left_consonant(
                trie, cluster_stroke, left_consonant_node, origin.prevowel, origin.rtl_stroke_boundary,
            )

    if can_elide_previous_vowel:
        _allow_elide_previous_vowel_using_first_left_consonant(
            trie, left_stroke, left_consonant_node, last_prevowel_node, last_rtl_stroke_boundary_node,
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
    cluster_consonants: list[tuple[Phoneme, ClusterOrigin, int]],
):
    if next_right_consonant_src_node is None or consonant not in PHONEMES_TO_CHORDS_RIGHT:
        return None, None, None
    

    right_stroke = PHONEMES_TO_CHORDS_RIGHT[consonant]
    right_stroke_keys = right_stroke.keys()
    
    right_consonant_node = trie.get_first_dst_node_else_create_chain(next_right_consonant_src_node, right_stroke_keys)
    if last_right_consonant_f_node is not None:
        trie.link_chain(last_right_consonant_f_node, right_consonant_node, right_stroke_keys)

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
        _allow_elide_previous_vowel_using_first_right_consonant(trie, right_stroke, right_consonant_node, last_pre_rtl_stroke_boundary_node)


    right_consonant_f_node = _add_right_f_consonant(
        trie, consonant, next_right_consonant_src_node, last_right_consonant_f_node, prev_left_consonant_node,
        last_pre_rtl_stroke_boundary_node, is_first_consonant, cluster_consonants,
    )


    @_if_cluster_found(cluster_consonants)
    def add_cluster(consonant: Phoneme, origin: ClusterOrigin, cluster_stroke: Stroke):
        if len(cluster_stroke & RIGHT_BANK_CONSONANTS_SUBSTROKE) == 0: return

        if origin.right is not None:
            trie.link_chain(origin.right, right_consonant_node, cluster_stroke.keys())

        if is_first_consonant:
            _allow_elide_previous_vowel_using_first_right_consonant(trie, cluster_stroke, right_consonant_node, origin.pre_rtl_stroke_boundary)

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
    cluster_consonants: list[tuple[Phoneme, ClusterOrigin, int]],
):
    if consonant not in PHONEMES_TO_CHORDS_RIGHT_F:
        return None
    
    right_f_stroke = PHONEMES_TO_CHORDS_RIGHT_F[consonant]
    right_f_stroke_keys = right_f_stroke.keys()


    right_consonant_f_node = trie.get_first_dst_node_else_create_chain(next_right_consonant_src_node, right_f_stroke_keys)
    if last_right_consonant_f_node is not None:
        trie.link_chain(last_right_consonant_f_node, right_consonant_f_node, right_f_stroke_keys)

    if prev_left_consonant_node is not None:
        trie.link_chain(prev_left_consonant_node, right_consonant_f_node, right_f_stroke_keys)
        
    if is_first_consonant:
        _allow_elide_previous_vowel_using_first_right_consonant(trie, right_f_stroke, right_consonant_f_node, last_pre_rtl_stroke_boundary_node)
        
    @_if_cluster_found(cluster_consonants)
    def add_cluster(consonant: Phoneme, origin: ClusterOrigin, cluster_stroke: Stroke):
        if len(cluster_stroke & RIGHT_BANK_CONSONANTS_SUBSTROKE) == 0: return

        if origin.right_f is not None and right_consonant_f_node is not None:
            trie.link_chain(origin.right_f, right_consonant_f_node, cluster_stroke.keys())

        if is_first_consonant:
            _allow_elide_previous_vowel_using_first_right_consonant(trie, cluster_stroke, right_consonant_f_node, origin.pre_rtl_stroke_boundary)

    return right_consonant_f_node

def _allow_elide_previous_vowel_using_first_left_consonant(trie: NondeterministicTrie[str, str], phoneme_substroke: Stroke, left_consonant_node: int, last_prevowels_node: Optional[int], last_rtl_stroke_boundary_node: Optional[int]):
    if last_prevowels_node is not None:
        trie.link_chain(last_prevowels_node, left_consonant_node, phoneme_substroke.keys())

    if last_rtl_stroke_boundary_node is not None:
        trie.link_chain(last_rtl_stroke_boundary_node, left_consonant_node, phoneme_substroke.keys())

def _allow_elide_previous_vowel_using_first_right_consonant(trie: NondeterministicTrie[str, str], phoneme_substroke: Stroke, right_consonant_node: int, last_pre_rtl_stroke_boundary_node: Optional[int]):
    if last_pre_rtl_stroke_boundary_node is not None:
        trie.link_chain(last_pre_rtl_stroke_boundary_node, right_consonant_node, phoneme_substroke.keys())


def _create_lookup_for(trie: "ReadonlyNondeterministicTrie[str, str] | NondeterministicTrie[str, str]"):
    def lookup(stroke_stenos: tuple[str, ...]):
        # plover.log.debug("")
        # plover.log.debug("new lookup")

        current_nodes = {trie.ROOT}

        for i, stroke_steno in enumerate(stroke_stenos):
            stroke = Stroke.from_steno(stroke_steno)
            if len(stroke) == 0:
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
                

        return trie.get_translation(current_nodes)

    return lookup