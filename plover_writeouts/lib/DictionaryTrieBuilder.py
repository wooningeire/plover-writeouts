from typing import Optional

from plover.steno import Stroke

from .DagTrie import DagTrie
from .Phoneme import Phoneme

LEFT_BANK_CONSONANTS_SUBSTROKE = Stroke.from_steno("STKPWHR")
VOWELS_SUBSTROKE = Stroke.from_steno("AOEU")
RIGHT_BANK_CONSONANTS_SUBSTROKE = Stroke.from_steno("-FRPBLGTSDZ")

def split_stroke_parts(stroke: Stroke):
    left_bank_consonants = stroke & LEFT_BANK_CONSONANTS_SUBSTROKE
    vowels = stroke & VOWELS_SUBSTROKE
    right_bank_consonants = stroke & RIGHT_BANK_CONSONANTS_SUBSTROKE

    return left_bank_consonants, vowels, right_bank_consonants

_RTL_CONSONANTS: dict[Stroke, Stroke] = {
    Stroke.from_steno(steno_right): Stroke.from_steno(steno_left)
    for steno_right, steno_left in {
        "-F": "TP",
        "-FB": "SR",
        "-FL": "TPHR",
        "-R": "R",
        "-P": "P",
        "-PB": "TPH",
        "-PBLG": "SKWR",
        "-PL": "PH",
        "-B": "PW",
        "-BG": "K",
        "-L": "HR",
        "-G": "TKPW",
        "-T": "T",
        "-S": "S",
        "-D": "TK",
        "-Z": "STKPW",
    }.items()
}

_LTR_CONSONANTS: dict[Stroke, Stroke] = {
    left: right
    for right, left in _RTL_CONSONANTS.items()
}

_LTR_F_CONSONANTS: dict[Stroke, Stroke] = {
    Stroke.from_steno(steno_main): Stroke.from_steno(steno_alt)
    for steno_main, steno_alt in {
        "S": "-F",
        "SR": "-F",
        "SKWR": "-F",
        "TH": "-F",
        "PH": "-FR",
    }.items()
}

_CLUSTERS: dict[tuple[Phoneme, ...], Stroke] = {
    phonemes: Stroke.from_steno(steno)
    for phonemes, steno in {
        (Phoneme.D, Phoneme.S): "STK",
        (Phoneme.G, Phoneme.L): "-LG",
    }.items()
}
clusters_trie: DagTrie[Phoneme, Stroke] = DagTrie()
for phonemes, stroke in _CLUSTERS.items():
    current_head = clusters_trie.ROOT
    for key in phonemes:
        current_head = clusters_trie.get_dst_node_else_create(current_head, key)
    
    clusters_trie.set_translation(current_head, stroke)



STROKE_BOUNDARY = "/"
LINKER_CHORD = Stroke.from_steno("KWR")

def allow_elide_previous_vowel_using_first_starting_consonant(dag_trie: DagTrie[str, str], current_head: int, first_phoneme_substroke: Stroke, last_prevowels_node: Optional[int], last_alternate_stroke_start_node: Optional[int]):
    if last_prevowels_node is not None:
        dag_trie.link_chain(last_prevowels_node, current_head, first_phoneme_substroke.keys())

    if last_alternate_stroke_start_node is not None:
        dag_trie.link_chain(last_alternate_stroke_start_node, current_head, first_phoneme_substroke.keys())


# def allow_reattach_starting_consonants_to_previous_stroke_as_ending_consonants_no_previous_right_bank(dag_trie: DagTrie[str, str], phonemes: tuple[], last_preboundary_node: Optional[int], last_alternate_right_base_nodes: list[int]):


def start_ltr_consonant_reattachment_no_previous_right_bank(dag_trie: DagTrie[str, str], phoneme_substroke: Stroke, last_preboundary_node: Optional[int], last_post_right_consonant_nodes: list[int]):
    main_right_consonant_node = None
    f_right_consonant_node = None
    alternate_stroke_start_node = None

    if phoneme_substroke in _LTR_CONSONANTS and last_preboundary_node is not None:
        main_right_consonant_node = dag_trie.get_dst_node_else_create_chain(last_preboundary_node, _LTR_CONSONANTS[phoneme_substroke].keys())

        # chain together ending chords
        for node in last_post_right_consonant_nodes:
            dag_trie.link_chain(node, main_right_consonant_node, _LTR_CONSONANTS[phoneme_substroke].keys())
            
        alternate_stroke_start_node = dag_trie.get_dst_node_else_create(main_right_consonant_node, STROKE_BOUNDARY)

    if phoneme_substroke in _LTR_F_CONSONANTS and last_preboundary_node is not None:
        f_right_consonant_node = dag_trie.get_dst_node_else_create_chain(last_preboundary_node, _LTR_F_CONSONANTS[phoneme_substroke].keys())

        # chain together ending chords
        for node in last_post_right_consonant_nodes:
            dag_trie.link_chain(node, f_right_consonant_node, _LTR_F_CONSONANTS[phoneme_substroke].keys())

    return main_right_consonant_node, f_right_consonant_node, alternate_stroke_start_node

def continue_ltr_consonant_reattachment(dag_trie: DagTrie[str, str], current_head: int, phoneme_substroke: Stroke, last_main_right_consonant_node: int, last_f_right_consonant_node: Optional[int], last_alternate_stroke_start_node: int):
    dag_trie.link_chain(last_alternate_stroke_start_node, current_head, phoneme_substroke.keys())

    main_right_consonant_node = None
    f_right_consonant_node = None
    alternate_stroke_start_node = None

    if phoneme_substroke in _LTR_CONSONANTS:
        main_right_consonant_node = dag_trie.get_dst_node_else_create_chain(last_main_right_consonant_node, _LTR_CONSONANTS[phoneme_substroke].keys())

        # chain together ending chords
        if last_f_right_consonant_node is not None:
            dag_trie.link_chain(last_f_right_consonant_node, main_right_consonant_node, _LTR_CONSONANTS[phoneme_substroke].keys())
            
        alternate_stroke_start_node = dag_trie.get_dst_node_else_create(main_right_consonant_node, STROKE_BOUNDARY)

    if phoneme_substroke in _LTR_F_CONSONANTS:
        f_right_consonant_node = dag_trie.get_dst_node_else_create_chain(last_main_right_consonant_node, _LTR_F_CONSONANTS[phoneme_substroke].keys())

        # chain together ending chords
        if last_f_right_consonant_node is not None:
            dag_trie.link_chain(last_f_right_consonant_node, f_right_consonant_node, _LTR_F_CONSONANTS[phoneme_substroke].keys())

    return main_right_consonant_node, f_right_consonant_node, alternate_stroke_start_node

def finish_ltr_consonant_reattachment(dag_trie: DagTrie[str, str], current_head: int, last_alternate_stroke_start_node: int):
    """Note: may cause some graphs to be nondeterministic"""
    dag_trie.link_chain(last_alternate_stroke_start_node, current_head, LINKER_CHORD.keys())
