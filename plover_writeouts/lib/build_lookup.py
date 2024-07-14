from typing import Callable, Optional

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

def _can_add_stroke_on(src_stroke: Stroke, addon_stroke: Stroke):
    return len(src_stroke) == 0 or len(addon_stroke) == 0 or Stroke.from_keys((src_stroke.keys()[-1],)) < Stroke.from_keys((addon_stroke.keys()[0],))


def _build_clusters_trie():
    clusters_trie: Trie[Phoneme, Stroke] = Trie()
    for phonemes, stroke in CLUSTERS.items():
        current_head = clusters_trie.ROOT
        for key in phonemes:
            current_head = clusters_trie.get_dst_node_else_create(current_head, key)

        clusters_trie.set_translation(current_head, stroke)
    return clusters_trie.frozen()
_clusters_trie = _build_clusters_trie()


def build_lookup(mappings: dict[str, str]):
    trie: NondeterministicTrie[Stroke, str] = NondeterministicTrie()

    for outline_steno, translation in mappings.items():
        _add_entry(trie, outline_steno, translation)

    plover.log.debug(str(trie))
    plover.log.debug(trie.profile())
    return _create_lookup_for((trie.optimized() if OPTIMIZE_TRIE_SPACE else trie).frozen())

def _add_entry(trie: NondeterministicTrie[Stroke, str], outline_steno: str, translation: str):
    current_syllable_consonants: list[Phoneme] = []

    left_stroke_paths: set[tuple[Stroke, int]] = {(Stroke.from_integer(0), trie.ROOT)}
    right_stroke_paths: set[tuple[Stroke, int]] = set()
    right_alt_stroke_paths: set[tuple[Stroke, int]] = set()

    is_first_consonant_set = True

    # Identifying clusters
    cluster_consonants: list[tuple[Phoneme, Optional[int], Optional[int], Optional[int]]] = []
    cluster_consonant_nodes: list[int] = []

    postvowels_node = None


    for stroke_steno in outline_steno.split("/"):
        stroke = Stroke.from_steno(stroke_steno)


        left_bank_consonants, vowels, right_bank_consonants, asterisk = _split_stroke_parts(stroke)
        if len(asterisk) > 0:
            return


        current_syllable_consonants.extend(split_consonant_phonemes(left_bank_consonants))


        if len(vowels) > 0:
            new_postleft_node = None

            # plover.log.debug(current_syllable_consonants)
            for consonant in current_syllable_consonants:
                # cluster_consonants, cluster_consonant_nodes = _update_cluster_tracking(
                #     cluster_consonants, cluster_consonant_nodes, consonant, next_left_consonant_src_node, next_right_consonant_src_node, last_right_consonant_f_node,
                # )


                left_stroke = PHONEMES_TO_CHORDS_LEFT[consonant]
                right_stroke = PHONEMES_TO_CHORDS_RIGHT.get(consonant)
                right_alt_stroke = PHONEMES_TO_CHORDS_RIGHT_F.get(consonant)

                for item in tuple(left_stroke_paths):
                    left_stroke_paths.remove(item)
                    existing_stroke, src_node = item

                    if not _can_add_stroke_on(existing_stroke, left_stroke): continue

                    key = existing_stroke + left_stroke

                    left_stroke_paths.add((key, src_node))
                
                for src_set, item in (
                    *((right_stroke_paths, item) for item in right_stroke_paths),
                    *((right_alt_stroke_paths, item) for item in right_alt_stroke_paths),
                ):
                    src_set.remove(item)
                    existing_stroke, src_node = item

                    if right_stroke is not None:
                        if not _can_add_stroke_on(existing_stroke, right_stroke):
                            new_src_node = trie.get_first_dst_node_else_create(src_node, existing_stroke)
                            new_postright_node = trie.get_first_dst_node_else_create(new_src_node, right_stroke)
                            right_stroke_paths.add((right_stroke, new_src_node))
                        else:
                            key = existing_stroke + right_stroke
                            new_postright_node = trie.get_first_dst_node_else_create(src_node, key)

                            right_stroke_paths.add((key, src_node))

                        left_stroke_paths.add((Stroke.from_integer(0), new_postright_node))
                    
                    if right_alt_stroke is not None:
                        if not _can_add_stroke_on(existing_stroke, right_alt_stroke): continue
                        key = existing_stroke + right_alt_stroke
                        right_alt_stroke_paths.add((key, src_node))


                # @_if_cluster_found(cluster_consonants, cluster_consonant_nodes)
                # def add_cluster(consonant_and_positions: tuple[Phoneme, Optional[int], Optional[int], Optional[int]], found_cluster: Stroke):
                #     pass
                #     # cluster_left = found_cluster & LEFT_BANK_CONSONANTS_SUBSTROKE
                #     # if len(cluster_left) > 0 and consonant_and_positions[1] is not None:
                #     #     trie.link_chain(consonant_and_positions[1], left_consonant_node, found_cluster.keys())

            for key, src_node in tuple(left_stroke_paths):
                if len(key) == 0 and is_first_consonant_set:
                    continue
                if len(key) == 0:
                    key = LINKER_CHORD

                if new_postleft_node is None:
                    new_postleft_node = trie.get_first_dst_node_else_create(src_node, key)
                else:
                    trie.link(src_node, new_postleft_node, key)


            if new_postleft_node is None:
                postvowels_node = trie.get_first_dst_node_else_create(trie.ROOT, vowels)
            else:
                postvowels_node = trie.get_first_dst_node_else_create(new_postleft_node, vowels)
                

            for key, src_node in tuple(right_stroke_paths):
                trie.link(src_node, postvowels_node, key)


            left_stroke_paths.add((Stroke.from_integer(0), postvowels_node))
            right_stroke_paths.add((Stroke.from_integer(0), postvowels_node))
            right_alt_stroke_paths.add((Stroke.from_integer(0), postvowels_node))

            n_previous_syllable_consonants = len(current_syllable_consonants)
            current_syllable_consonants = []

            is_first_consonant_set = False

        current_syllable_consonants.extend(split_consonant_phonemes(right_bank_consonants))


    final_node = postvowels_node if len(current_syllable_consonants) == 0 else None

    for i, consonant in enumerate(current_syllable_consonants):
        right_stroke = PHONEMES_TO_CHORDS_RIGHT.get(consonant)
        right_alt_stroke = PHONEMES_TO_CHORDS_RIGHT_F.get(consonant)
        
        for src_set, item in (
            *((right_stroke_paths, item) for item in right_stroke_paths),
            *((right_alt_stroke_paths, item) for item in right_alt_stroke_paths),
        ):
            src_set.remove(item)
            existing_stroke, src_node = item

            if right_stroke is not None:
                if not _can_add_stroke_on(existing_stroke, right_stroke):
                    new_postright_node = trie.get_first_dst_node_else_create(src_node, right_stroke)
                    right_stroke_paths.add((right_stroke, src_node))
                else:
                    key = existing_stroke + right_stroke
                    if i == len(current_syllable_consonants) - 1:
                        if final_node is None:
                            final_node = trie.get_first_dst_node_else_create(src_node, key)
                        else:
                            trie.link(src_node, final_node, key)

                    right_stroke_paths.add((key, src_node))

            
            if right_alt_stroke is not None:
                if not _can_add_stroke_on(existing_stroke, right_alt_stroke): continue
                key = existing_stroke + right_alt_stroke
                right_alt_stroke_paths.add((key, src_node))


    if final_node is None:
        return

    trie.set_translation(final_node, translation)


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


def _create_lookup_for(trie: ReadonlyNondeterministicTrie[Stroke, str]):
    def lookup(stroke_stenos: tuple[str, ...]):
        # plover.log.debug("")
        # plover.log.debug("new lookup")

        current_nodes = {trie.ROOT}

        for stroke_steno in stroke_stenos:
            stroke = Stroke.from_steno(stroke_steno)
            if len(stroke) == 0:
                return None

            left_bank_consonants, vowels, right_bank_consonants, asterisk = _split_stroke_parts(stroke)

            if len(left_bank_consonants) > 0:
                # plover.log.debug(current_nodes)
                # plover.log.debug(left_bank_consonants.keys())
                if len(asterisk) > 0:
                    current_nodes = trie.get_dst_nodes(current_nodes, left_bank_consonants) | trie.get_dst_nodes(current_nodes, left_bank_consonants + asterisk)
                else:
                    current_nodes = trie.get_dst_nodes(current_nodes, left_bank_consonants)

                if len(current_nodes) == 0:
                    return None

            if len(vowels) > 0:
                # plover.log.debug(current_nodes)
                # plover.log.debug(vowels.rtfcre)
                current_nodes = trie.get_dst_nodes(current_nodes, vowels)
                if len(current_nodes) == 0:
                    return None

            if len(right_bank_consonants) > 0:
                # plover.log.debug(current_nodes)
                # plover.log.debug(right_bank_consonants.keys())
                if len(asterisk) > 0:
                    current_nodes = trie.get_dst_nodes(current_nodes, right_bank_consonants) | trie.get_dst_nodes(current_nodes, right_bank_consonants + asterisk)
                else:
                    current_nodes = trie.get_dst_nodes(current_nodes, right_bank_consonants)

                if len(current_nodes) == 0:
                    return None
                
            # if len(asterisk) > 0:
            #     current_nodes = trie.get_dst_nodes_chain(current_nodes, asterisk.keys())

        return trie.get_translation(current_nodes)

    return lookup