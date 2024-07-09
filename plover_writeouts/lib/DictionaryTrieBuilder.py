from typing import Callable, Optional

from plover.steno import Stroke
import plover.log

from .DagTrie import DagTrie
from .Phoneme import Phoneme, split_consonant_phonemes, PHONEMES_TO_CHORDS_LEFT, PHONEMES_TO_CHORDS_RIGHT, PHONEMES_TO_CHORDS_RIGHT_F

_LEFT_BANK_CONSONANTS_SUBSTROKE = Stroke.from_steno("STKPWHR")
_VOWELS_SUBSTROKE = Stroke.from_steno("AOEU")
_RIGHT_BANK_CONSONANTS_SUBSTROKE = Stroke.from_steno("-FRPBLGTSDZ")

def _split_stroke_parts(stroke: Stroke):
    left_bank_consonants = stroke & _LEFT_BANK_CONSONANTS_SUBSTROKE
    vowels = stroke & _VOWELS_SUBSTROKE
    right_bank_consonants = stroke & _RIGHT_BANK_CONSONANTS_SUBSTROKE

    return left_bank_consonants, vowels, right_bank_consonants


_CLUSTERS: dict[tuple[Phoneme, ...], Stroke] = {
    phonemes: Stroke.from_steno(steno)
    for phonemes, steno in {
        (Phoneme.D, Phoneme.S): "STK",
        (Phoneme.G, Phoneme.L): "-LG",
    }.items()
}
_clusters_trie: DagTrie[Phoneme, Stroke] = DagTrie()
for _phonemes, _stroke in _CLUSTERS.items():
    _current_head = _clusters_trie.ROOT
    for key in _phonemes:
        _current_head = _clusters_trie.get_dst_node_else_create(_current_head, key)
    
    _clusters_trie.set_translation(_current_head, _stroke)


_STROKE_BOUNDARY = "/"
_LINKER_CHORD = Stroke.from_steno("SWH")


def build_lookup(mappings: dict[str, str]):
    dag_trie: DagTrie[str, str] = DagTrie()

    for outline_steno, translation in mappings.items():
        _add_entry(dag_trie, outline_steno, translation)

    return _create_lookup_for(dag_trie)

def _add_entry(dag_trie: DagTrie[str, str], outline_steno: str, translation: str):
    current_syllable_consonants: list[Phoneme] = []

    last_left_consonant_node: Optional[int] = dag_trie.ROOT
    last_right_consonant_node: Optional[int] = None
    last_right_consonant_f_node: Optional[int] = None

    last_prevowel_node: Optional[int] = None
    last_pre_rtl_stroke_boundary_node: Optional[int] = None
    last_rtl_stroke_boundary_node: Optional[int] = None

    is_starting_consonants = True

    # Identifying clusters
    cluster_consonants: list[tuple[Phoneme, Optional[int], Optional[int], Optional[int]]] = []
    cluster_consonant_nodes: list[int] = []

    for stroke_steno in outline_steno.split("/"):
        stroke = Stroke.from_steno(stroke_steno)

        left_bank_consonants, vowels, right_bank_consonants = _split_stroke_parts(stroke)


        current_syllable_consonants.extend(split_consonant_phonemes(left_bank_consonants))


        if len(vowels) > 0:
            for i, consonant in enumerate(current_syllable_consonants):
                cluster_consonants, cluster_consonant_nodes = _update_cluster_tracking(
                    cluster_consonants, cluster_consonant_nodes, consonant, last_left_consonant_node, last_right_consonant_node, last_right_consonant_f_node,
                )


                left_consonant_node = dag_trie.get_dst_node_else_create_chain(last_left_consonant_node, PHONEMES_TO_CHORDS_LEFT[consonant].keys())


                @_if_cluster_found(cluster_consonants, cluster_consonant_nodes)
                def add_cluster(consonant_and_positions: tuple[Phoneme, Optional[int], Optional[int], Optional[int]], found_cluster: Stroke):
                    cluster_left, cluster_vowels, cluster_right = _split_stroke_parts(found_cluster)
                    if len(cluster_left) > 0 and consonant_and_positions[1] is not None:
                        dag_trie.link_chain(consonant_and_positions[1], left_consonant_node, found_cluster.keys())


                if not is_starting_consonants:
                    if i == 0:
                        _allow_elide_previous_vowel_using_first_left_consonant(
                            dag_trie, PHONEMES_TO_CHORDS_LEFT[consonant], left_consonant_node, last_prevowel_node, last_rtl_stroke_boundary_node,
                        )

                    last_right_consonant_node, last_right_consonant_f_node, rtl_stroke_boundary_adjacent_nodes = _add_right_consonant(
                        dag_trie, consonant, last_right_consonant_node, last_right_consonant_f_node, left_consonant_node, last_pre_rtl_stroke_boundary_node,
                        i == 0, i == len(current_syllable_consonants) - 1, cluster_consonants, cluster_consonant_nodes,
                    )
                    if rtl_stroke_boundary_adjacent_nodes is not None:
                        last_pre_rtl_stroke_boundary_node, last_rtl_stroke_boundary_node = rtl_stroke_boundary_adjacent_nodes

                last_left_consonant_node = left_consonant_node

            current_syllable_consonants = []

            last_prevowel_node = last_left_consonant_node
            # can't really do anything all that special with vowels, so only proceed through a vowel transition
            # if it matches verbatim
            postvowel_node = dag_trie.get_dst_node_else_create(last_left_consonant_node, vowels.rtfcre)

            last_left_consonant_node = dag_trie.get_dst_node_else_create(postvowel_node, _STROKE_BOUNDARY)
            last_right_consonant_node = postvowel_node

            is_starting_consonants = False

            

        # for cluster in delayed_clusters:
        #     dag_trie.link_chain(cluster[0], current_head, cluster[1].keys())


        current_syllable_consonants.extend(split_consonant_phonemes(right_bank_consonants))


    last_left_consonant_node = None
    for i, consonant in enumerate(current_syllable_consonants):
        last_right_consonant_node, last_right_consonant_f_node, _ = _add_right_consonant(
            dag_trie, consonant, last_right_consonant_node, last_right_consonant_f_node, None, last_pre_rtl_stroke_boundary_node,
            i == 0, i == len(current_syllable_consonants) - 1, cluster_consonants, cluster_consonant_nodes,
        )

    assert last_right_consonant_node is not None

    dag_trie.set_translation(last_right_consonant_node, translation)


def _update_cluster_tracking(
    cluster_consonants: list[tuple[Phoneme, Optional[int], Optional[int], Optional[int]]],
    cluster_consonant_nodes: list[int],
    new_consonant: Phoneme,
    last_left_consonant_node: Optional[int],
    last_right_consonant_node: Optional[int],
    last_right_consonant_f_node: Optional[int],
):
    # update cluster identification
    new_cluster_consonants: list[tuple[Phoneme, Optional[int], Optional[int], Optional[int]]] = []
    new_cluster_consonant_nodes: list[int] = []
    for consonant_and_positions, cluster_node in zip(
        cluster_consonants + [(new_consonant, last_left_consonant_node, last_right_consonant_node, last_right_consonant_f_node)],
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
    dag_trie: DagTrie[str, str],
    consonant: Phoneme,
    last_right_consonant_node: Optional[int],
    last_right_consonant_f_node: Optional[int],
    left_consonant_node: Optional[int],
    last_pre_rtl_stroke_boundary_node: Optional[int],
    is_first_consonant: bool,
    is_last_consonant: bool,
    cluster_consonants: list[tuple[Phoneme, Optional[int], Optional[int], Optional[int]]],
    cluster_consonant_nodes: list[int],
):
    if last_right_consonant_node is None or consonant not in PHONEMES_TO_CHORDS_RIGHT:
        return None, None, None
    
    right_consonant_node = dag_trie.get_dst_node_else_create_chain(last_right_consonant_node, PHONEMES_TO_CHORDS_RIGHT[consonant].keys())
    if last_right_consonant_f_node is not None:
        dag_trie.link_chain(last_right_consonant_f_node, right_consonant_node, PHONEMES_TO_CHORDS_RIGHT[consonant].keys())


    last_rtl_stroke_boundary_node = None

    if left_consonant_node is not None:
        if is_last_consonant:
            last_pre_rtl_stroke_boundary_node = right_consonant_node
            last_rtl_stroke_boundary_node = dag_trie.get_dst_node_else_create(right_consonant_node, _STROKE_BOUNDARY)
            dag_trie.link_chain(last_rtl_stroke_boundary_node, left_consonant_node, _LINKER_CHORD.keys())
        else:
            dag_trie.link(right_consonant_node, left_consonant_node, _STROKE_BOUNDARY)
        

    if is_first_consonant:
        _allow_elide_previous_vowel_using_first_right_consonant(dag_trie, PHONEMES_TO_CHORDS_RIGHT[consonant], right_consonant_node, last_pre_rtl_stroke_boundary_node)


    if consonant not in PHONEMES_TO_CHORDS_RIGHT_F:
        right_consonant_f_node = None
    else:
        right_consonant_f_node = dag_trie.get_dst_node_else_create_chain(last_right_consonant_node, PHONEMES_TO_CHORDS_RIGHT_F[consonant].keys())
        if last_right_consonant_f_node is not None:
            dag_trie.link_chain(last_right_consonant_f_node, right_consonant_f_node, PHONEMES_TO_CHORDS_RIGHT_F[consonant].keys())
            
        if is_first_consonant:
            _allow_elide_previous_vowel_using_first_right_consonant(dag_trie, PHONEMES_TO_CHORDS_RIGHT_F[consonant], right_consonant_f_node, last_pre_rtl_stroke_boundary_node)


    @_if_cluster_found(cluster_consonants, cluster_consonant_nodes)
    def add_cluster(consonant_and_positions: tuple[Phoneme, Optional[int], Optional[int], Optional[int]], found_cluster: Stroke):
        cluster_left, cluster_vowels, cluster_right = _split_stroke_parts(found_cluster)
        if len(cluster_right) > 0 and consonant_and_positions[2] is not None:
            dag_trie.link_chain(consonant_and_positions[2], right_consonant_node, found_cluster.keys())
        # if len(cluster_right) > 0 and consonant_and_positions[3] is not None and right_consonant_f_node is not None:
        #     dag_trie.link_chain(consonant_and_positions[3], right_consonant_f_node, found_cluster.keys())

    
    rtl_stroke_boundary_adjacent_nodes = (last_pre_rtl_stroke_boundary_node, last_rtl_stroke_boundary_node)
    return right_consonant_node, right_consonant_f_node, rtl_stroke_boundary_adjacent_nodes if last_rtl_stroke_boundary_node is not None else None


def _allow_elide_previous_vowel_using_first_left_consonant(dag_trie: DagTrie[str, str], phoneme_substroke: Stroke, left_consonant_node: int, last_prevowels_node: Optional[int], last_rtl_stroke_boundary_node: Optional[int]):
    if last_prevowels_node is not None:
        dag_trie.link_chain(last_prevowels_node, left_consonant_node, phoneme_substroke.keys())

    if last_rtl_stroke_boundary_node is not None:
        dag_trie.link_chain(last_rtl_stroke_boundary_node, left_consonant_node, phoneme_substroke.keys())

def _allow_elide_previous_vowel_using_first_right_consonant(dag_trie: DagTrie[str, str], phoneme_substroke: Stroke, right_consonant_node: int, last_pre_rtl_stroke_boundary_node: Optional[int]):
    if last_pre_rtl_stroke_boundary_node is not None:
        dag_trie.link_chain(last_pre_rtl_stroke_boundary_node, right_consonant_node, phoneme_substroke.keys())


def _create_lookup_for(dag_trie: DagTrie[str, str]):
    def lookup(stroke_stenos: tuple[str, ...]):
        # plover.log.info("new lookup")

        current_head = dag_trie.ROOT

        for i, stroke_steno in enumerate(stroke_stenos):
            stroke = Stroke.from_steno(stroke_steno)
            if len(stroke) == 0:
                return None
            
            if i > 0:
                # plover.log.info(current_head)
                # plover.log.info(_STROKE_BOUNDARY)
                current_head = dag_trie.get_dst_node(current_head, _STROKE_BOUNDARY)
                if current_head is None:
                    return None

            left_bank_consonants, vowels, right_bank_consonants = _split_stroke_parts(stroke)

            if len(left_bank_consonants) > 0:
                left_bank_consonants_keys = left_bank_consonants.keys()
                current_head = dag_trie.get_dst_node_chain(current_head, left_bank_consonants_keys)
                # plover.log.info(left_bank_consonants_keys)

                if current_head is None:
                    return None

            if len(vowels) == 0:
                return None
            # plover.log.info(current_head)
            # plover.log.info(vowels.rtfcre)
            current_head = dag_trie.get_dst_node(current_head, vowels.rtfcre)
            if current_head is None:
                return None

            if len(right_bank_consonants) > 0:
                right_bank_consonants_keys = right_bank_consonants.keys()
                current_head = dag_trie.get_dst_node_chain(current_head, right_bank_consonants_keys)
                # plover.log.info(right_bank_consonants_keys)
                if current_head is None:
                    return None

        return dag_trie.get_translation(current_head)

    return lookup