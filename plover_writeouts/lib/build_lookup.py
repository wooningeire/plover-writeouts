from typing import Callable, Optional

from plover.steno import Stroke
import plover.log

from .Trie import Trie, NondeterministicTrie
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
    OPTIMIZE_TRIE_SPACE,
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


def build_lookup(mappings: dict[str, str]):
    trie: NondeterministicTrie[str, str] = NondeterministicTrie()

    for outline_steno, translation in mappings.items():
        _add_entry(trie, outline_steno, translation)

    # plover.log.debug(str(trie.optimized()))

    return _create_lookup_for(trie.optimized() if OPTIMIZE_TRIE_SPACE else trie)

def _add_entry(trie: NondeterministicTrie[str, str], outline_steno: str, translation: str):
    current_syllable_consonants: list[Phoneme] = []
    n_previous_syllable_consonants = 0

    next_left_consonant_src_node: Optional[int] = trie.ROOT
    next_right_consonant_src_node: Optional[int] = None
    last_right_consonant_f_node: Optional[int] = None

    prev_left_consonant_node: Optional[int] = None

    last_prevowel_node: Optional[int] = None
    last_pre_rtl_stroke_boundary_node: Optional[int] = None
    last_rtl_stroke_boundary_node: Optional[int] = None

    is_starting_consonants = True

    # Identifying clusters
    cluster_consonants: list[tuple[Phoneme, Optional[int], Optional[int], Optional[int]]] = []
    cluster_consonant_nodes: list[int] = []

    strokes_steno = outline_steno.split("/")
    for j, stroke_steno in enumerate(strokes_steno):
        stroke = Stroke.from_steno(stroke_steno)


        left_bank_consonants, vowels, right_bank_consonants, asterisk = _split_stroke_parts(stroke)
        if len(asterisk) > 0:
            return


        current_syllable_consonants.extend(split_consonant_phonemes(left_bank_consonants))


        if len(vowels) > 0:
            # plover.log.debug(current_syllable_consonants)
            for i, consonant in enumerate(current_syllable_consonants):
                cluster_consonants, cluster_consonant_nodes = _update_cluster_tracking(
                    cluster_consonants, cluster_consonant_nodes, consonant, next_left_consonant_src_node, next_right_consonant_src_node, last_right_consonant_f_node,
                )


                left_stroke = PHONEMES_TO_CHORDS_LEFT[consonant]
                left_stroke_keys = left_stroke.keys()

                left_consonant_node = trie.get_first_dst_node_else_create_chain(next_left_consonant_src_node, left_stroke_keys)
                if last_rtl_stroke_boundary_node is not None:
                    trie.link_chain(last_rtl_stroke_boundary_node, left_consonant_node, left_stroke_keys)


                @_if_cluster_found(cluster_consonants, cluster_consonant_nodes)
                def add_cluster(consonant_and_positions: tuple[Phoneme, Optional[int], Optional[int], Optional[int]], found_cluster: Stroke):
                    cluster_left = found_cluster & LEFT_BANK_CONSONANTS_SUBSTROKE
                    if len(cluster_left) > 0 and consonant_and_positions[1] is not None:
                        trie.link_chain(consonant_and_positions[1], left_consonant_node, found_cluster.keys())


                if not is_starting_consonants:
                    if i == 0 and n_previous_syllable_consonants > 0:
                        _allow_elide_previous_vowel_using_first_left_consonant(
                            trie, left_stroke, left_consonant_node, last_prevowel_node, last_rtl_stroke_boundary_node,
                        )

                    next_right_consonant_src_node, last_right_consonant_f_node, rtl_stroke_boundary_adjacent_nodes = _add_right_consonant(
                        trie, consonant, next_right_consonant_src_node, last_right_consonant_f_node, left_consonant_node, prev_left_consonant_node,
                        last_pre_rtl_stroke_boundary_node, i == 0, i == len(current_syllable_consonants) - 1, cluster_consonants, cluster_consonant_nodes,
                    )
                    if rtl_stroke_boundary_adjacent_nodes is not None:
                        last_pre_rtl_stroke_boundary_node, last_rtl_stroke_boundary_node = rtl_stroke_boundary_adjacent_nodes

                next_left_consonant_src_node = prev_left_consonant_node = left_consonant_node

            n_previous_syllable_consonants = len(current_syllable_consonants)
            current_syllable_consonants = []

            last_prevowel_node = next_left_consonant_src_node
            # can't really do anything all that special with vowels, so only proceed through a vowel transition
            # if it matches verbatim
            if n_previous_syllable_consonants == 0 and not is_starting_consonants:
                postlinker_node = trie.get_first_dst_node_else_create(next_left_consonant_src_node, TRIE_LINKER_KEY)
                postvowels_node = trie.get_first_dst_node_else_create(postlinker_node, vowels.rtfcre)
            else:
                postvowels_node = trie.get_first_dst_node_else_create(next_left_consonant_src_node, vowels.rtfcre)


            next_right_consonant_src_node = postvowels_node
            next_left_consonant_src_node = trie.get_first_dst_node_else_create(postvowels_node, TRIE_STROKE_BOUNDARY_KEY)

            # if INITIAL_VOWEL_CHORD is not None and n_previous_syllable_consonants == 0 and is_starting_consonants:
            #     trie.link_chain(trie.ROOT, next_left_consonant_src_node, INITIAL_VOWEL_CHORD.keys())

            prev_left_consonant_node = None

            is_starting_consonants = False


        current_syllable_consonants.extend(split_consonant_phonemes(right_bank_consonants))


    for i, consonant in enumerate(current_syllable_consonants):
        next_right_consonant_src_node, last_right_consonant_f_node, _ = _add_right_consonant(
            trie, consonant, next_right_consonant_src_node, last_right_consonant_f_node, None, prev_left_consonant_node, last_pre_rtl_stroke_boundary_node,
            i == 0, i == len(current_syllable_consonants) - 1, cluster_consonants, cluster_consonant_nodes,
        )

        next_left_consonant_src_node = None

    # assert last_right_consonant_node is not None
    if next_right_consonant_src_node is None:
        return

    trie.set_translation(next_right_consonant_src_node, translation)


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

def _if_cluster_found(
    cluster_consonants: list[tuple[Phoneme, Optional[int], Optional[int], Optional[int]]],
    cluster_consonant_nodes: list[int],
):
    def handler(fn: Callable[[tuple[Phoneme, Optional[int], Optional[int], Optional[int]], Stroke], None]):
        for consonant_and_positions, cluster_node in zip(cluster_consonants, cluster_consonant_nodes):
            found_cluster = _clusters_trie.get_translation(cluster_node)
            if found_cluster is None: continue

            fn(consonant_and_positions, found_cluster)

    return handler

def _add_right_consonant(
    trie: NondeterministicTrie[str, str],
    consonant: Phoneme,
    next_right_consonant_src_node: Optional[int],
    last_right_consonant_f_node: Optional[int],
    left_consonant_node: Optional[int],
    prev_left_consonant_node: Optional[int],
    last_pre_rtl_stroke_boundary_node: Optional[int],
    is_first_consonant: bool,
    is_last_consonant: bool,
    cluster_consonants: list[tuple[Phoneme, Optional[int], Optional[int], Optional[int]]],
    cluster_consonant_nodes: list[int],
):
    if next_right_consonant_src_node is None or consonant not in PHONEMES_TO_CHORDS_RIGHT:
        return None, None, None
    

    right_stroke = PHONEMES_TO_CHORDS_RIGHT[consonant]
    right_stroke_keys = right_stroke.keys()
    
    right_consonant_node = trie.get_first_dst_node_else_create_chain(next_right_consonant_src_node, right_stroke_keys)
    if last_right_consonant_f_node is not None:
        trie.link_chain(last_right_consonant_f_node, right_consonant_node, right_stroke_keys)

    # Skeletals and right-bank consonant addons
    # if prev_left_consonant_node is not None:
    #     trie.link_chain(prev_left_consonant_node, right_consonant_node, right_stroke_keys)


    pre_rtl_stroke_boundary_node = last_pre_rtl_stroke_boundary_node
    rtl_stroke_boundary_node = None

    if left_consonant_node is not None and consonant is not Phoneme.DUMMY:
        pre_rtl_stroke_boundary_node = right_consonant_node
        rtl_stroke_boundary_node = trie.get_first_dst_node_else_create(right_consonant_node, TRIE_STROKE_BOUNDARY_KEY)
        trie.link(rtl_stroke_boundary_node, left_consonant_node, TRIE_LINKER_KEY)
        

    if is_first_consonant:
        _allow_elide_previous_vowel_using_first_right_consonant(trie, right_stroke, right_consonant_node, last_pre_rtl_stroke_boundary_node)


    if consonant not in PHONEMES_TO_CHORDS_RIGHT_F:
        right_consonant_f_node = None
    else:
        right_f_stroke = PHONEMES_TO_CHORDS_RIGHT_F[consonant]
        right_f_stroke_keys = right_f_stroke.keys()


        right_consonant_f_node = trie.get_first_dst_node_else_create_chain(next_right_consonant_src_node, right_f_stroke_keys)
        if last_right_consonant_f_node is not None:
            trie.link_chain(last_right_consonant_f_node, right_consonant_f_node, right_f_stroke_keys)

        # if prev_left_consonant_node is not None:
        #     trie.link_chain(prev_left_consonant_node, right_consonant_f_node, right_f_stroke_keys)
            
        if is_first_consonant:
            _allow_elide_previous_vowel_using_first_right_consonant(trie, right_f_stroke, right_consonant_f_node, last_pre_rtl_stroke_boundary_node)


    @_if_cluster_found(cluster_consonants, cluster_consonant_nodes)
    def add_cluster(consonant_and_positions: tuple[Phoneme, Optional[int], Optional[int], Optional[int]], found_cluster: Stroke):
        cluster_right = found_cluster & RIGHT_BANK_CONSONANTS_SUBSTROKE
        if len(cluster_right) > 0 and consonant_and_positions[2] is not None:
            trie.link_chain(consonant_and_positions[2], right_consonant_node, found_cluster.keys())
        if len(cluster_right) > 0 and consonant_and_positions[3] is not None and right_consonant_f_node is not None:
            trie.link_chain(consonant_and_positions[3], right_consonant_f_node, found_cluster.keys())

    
    rtl_stroke_boundary_adjacent_nodes = (pre_rtl_stroke_boundary_node, rtl_stroke_boundary_node)
    return right_consonant_node, right_consonant_f_node, rtl_stroke_boundary_adjacent_nodes if rtl_stroke_boundary_node is not None else None


def _allow_elide_previous_vowel_using_first_left_consonant(trie: NondeterministicTrie[str, str], phoneme_substroke: Stroke, left_consonant_node: int, last_prevowels_node: Optional[int], last_rtl_stroke_boundary_node: Optional[int]):
    if last_prevowels_node is not None:
        trie.link_chain(last_prevowels_node, left_consonant_node, phoneme_substroke.keys())

    if last_rtl_stroke_boundary_node is not None:
        trie.link_chain(last_rtl_stroke_boundary_node, left_consonant_node, phoneme_substroke.keys())

def _allow_elide_previous_vowel_using_first_right_consonant(trie: NondeterministicTrie[str, str], phoneme_substroke: Stroke, right_consonant_node: int, last_pre_rtl_stroke_boundary_node: Optional[int]):
    if last_pre_rtl_stroke_boundary_node is not None:
        trie.link_chain(last_pre_rtl_stroke_boundary_node, right_consonant_node, phoneme_substroke.keys())


def _create_lookup_for(trie: NondeterministicTrie[str, str]):
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
                # plover.log.debug(_STROKE_BOUNDARY)
                current_nodes = trie.get_dst_nodes(current_nodes, TRIE_STROKE_BOUNDARY_KEY)
                if len(current_nodes) == 0:
                    return None

            left_bank_consonants, vowels, right_bank_consonants, asterisk = _split_stroke_parts(stroke)

            if len(left_bank_consonants) > 0:
                # plover.log.debug(current_nodes)
                # plover.log.debug(left_bank_consonants.keys())
                if left_bank_consonants == LINKER_CHORD:
                    current_nodes = {*trie.get_dst_nodes_chain(current_nodes, left_bank_consonants.keys()), *trie.get_dst_nodes(current_nodes, TRIE_LINKER_KEY)}
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
                current_nodes = trie.get_dst_nodes_chain(current_nodes, right_bank_consonants.keys())
                if len(current_nodes) == 0:
                    return None
                
            if len(asterisk) > 0:
                current_nodes = trie.get_dst_nodes_chain(current_nodes, asterisk.keys())

        return trie.get_translation(current_nodes)

    return lookup