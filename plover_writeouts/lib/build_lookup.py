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
from .util import can_add_stroke_on


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


def build_lookup(mappings: dict[str, str]):
    trie: NondeterministicTrie[Stroke, str] = NondeterministicTrie()

    for outline_steno, translation in mappings.items():
        _add_entry(trie, outline_steno, translation)

    # plover.log.debug(str(trie))
    frozen_trie = (trie.optimized() if OPTIMIZE_TRIE_SPACE else trie).frozen()
    plover.log.debug(frozen_trie.profile())
    return _create_lookup_for(frozen_trie)

def _add_entry(trie: NondeterministicTrie[Stroke, str], outline_steno: str, translation: str):
    current_syllable_consonants: list[Phoneme] = []

    left_stroke_paths: set[tuple[Stroke, int]] = {(Stroke.from_integer(0), trie.ROOT)}
    right_stroke_paths: set[tuple[Stroke, int]] = set()
    right_alt_stroke_paths: set[tuple[Stroke, int]] = set()

    is_first_consonant_set = True

    # Identifying clusters
    cluster_consonants: list[Phoneme] = []
    cluster_consonant_nodes: list[int] = []
    cluster_paths: list[tuple[tuple[tuple[Stroke, int], ...], ...]] = []

    postvowels_node = None


    for stroke_steno in outline_steno.split("/"):
        stroke = Stroke.from_steno(stroke_steno)


        left_bank_consonants, vowels, right_bank_consonants, asterisk = _split_stroke_parts(stroke)
        # if len(asterisk) > 0:
        #     return


        current_syllable_consonants.extend(split_consonant_phonemes(left_bank_consonants))


        if len(vowels) > 0:
            new_postleft_node = None

            for consonant in current_syllable_consonants:
                cluster_consonants, cluster_consonant_nodes, cluster_paths = _update_cluster_tracking(
                    cluster_consonants, cluster_consonant_nodes, cluster_paths, consonant, (left_stroke_paths, right_stroke_paths, right_alt_stroke_paths)
                )

                found_left_clusters: list[tuple[Stroke, tuple[tuple[tuple[Stroke, int], ...], ...]]] = []
                found_right_clusters: list[tuple[Stroke, tuple[tuple[tuple[Stroke, int], ...], ...]]] = []

                @_if_cluster_found(cluster_consonants, cluster_consonant_nodes, cluster_paths)
                def add_cluster(consonant: Phoneme, cluster_stroke: Stroke, paths: tuple[tuple[tuple[Stroke, int], ...], ...]):
                    cluster_left = cluster_stroke & LEFT_BANK_CONSONANTS_SUBSTROKE
                    cluster_right = cluster_stroke & RIGHT_BANK_CONSONANTS_SUBSTROKE
                    if len(cluster_left) > 0:
                        found_left_clusters.append((cluster_stroke, paths))
                    if len(cluster_right) > 0:
                        found_right_clusters.append((cluster_stroke, paths))


                left_stroke = PHONEMES_TO_CHORDS_LEFT[consonant]
                right_stroke = PHONEMES_TO_CHORDS_RIGHT.get(consonant)
                right_alt_stroke = PHONEMES_TO_CHORDS_RIGHT_F.get(consonant)

                left_path_found = False

                for item in tuple(left_stroke_paths):
                    left_stroke_paths.remove(item)
                    existing_stroke, src_node = item


                    for cluster_stroke, paths in found_left_clusters:
                        for existing_stroke_1, src_node_1 in paths[0]:
                            if not can_add_stroke_on(existing_stroke_1, cluster_stroke): continue

                            key = existing_stroke_1 + cluster_stroke
                            left_stroke_paths.add((key, src_node_1))


                    if not can_add_stroke_on(existing_stroke, left_stroke): continue

                    key = existing_stroke + left_stroke
                    left_stroke_paths.add((key, src_node))

                    left_path_found = True
                

                for src_set, item in (
                    *((right_stroke_paths, item) for item in right_stroke_paths),
                    *((right_alt_stroke_paths, item) for item in right_alt_stroke_paths),
                ):
                    src_set.remove(item)
                    existing_stroke, src_node = item


                    for cluster_stroke, paths in found_right_clusters:
                        for existing_stroke_1, src_node_1 in (*paths[1], *paths[2]):
                            if not can_add_stroke_on(existing_stroke_1, cluster_stroke): continue

                            key = existing_stroke_1 + cluster_stroke
                            right_stroke_paths.add((key, src_node_1))


                    if right_stroke is not None:
                        if not can_add_stroke_on(existing_stroke, right_stroke):
                            if not left_path_found:
                                new_src_node = trie.get_first_dst_node_else_create(src_node, existing_stroke)
                                right_stroke_paths.add((right_stroke, new_src_node))

                                new_postright_node = trie.get_first_dst_node_else_create(new_src_node, right_stroke)
                                
                                left_stroke_paths.add((Stroke.from_integer(0), new_postright_node))
                        else:
                            key = existing_stroke + right_stroke
                            right_stroke_paths.add((key, src_node))

                            new_postright_node = trie.get_first_dst_node_else_create(src_node, key)

                            left_stroke_paths.add((Stroke.from_integer(0), new_postright_node))
                    

                    if right_alt_stroke is not None:
                        if not can_add_stroke_on(existing_stroke, right_alt_stroke): continue
                        key = existing_stroke + right_alt_stroke
                        right_alt_stroke_paths.add((key, src_node))


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
        cluster_consonants, cluster_consonant_nodes, cluster_paths = _update_cluster_tracking(
            cluster_consonants, cluster_consonant_nodes, cluster_paths, consonant, (left_stroke_paths, right_stroke_paths, right_alt_stroke_paths)
        )

        found_right_clusters: list[tuple[Stroke, tuple[tuple[tuple[Stroke, int], ...], ...]]] = []

        @_if_cluster_found(cluster_consonants, cluster_consonant_nodes, cluster_paths)
        def add_cluster(consonant: Phoneme, cluster_stroke: Stroke, paths: tuple[tuple[tuple[Stroke, int], ...], ...]):
            cluster_right = cluster_stroke & RIGHT_BANK_CONSONANTS_SUBSTROKE
            if len(cluster_right) > 0:
                found_right_clusters.append((cluster_stroke, paths))


        right_stroke = PHONEMES_TO_CHORDS_RIGHT.get(consonant)
        right_alt_stroke = PHONEMES_TO_CHORDS_RIGHT_F.get(consonant)
        
        for src_set, item in (
            *((right_stroke_paths, item) for item in right_stroke_paths),
            *((right_alt_stroke_paths, item) for item in right_alt_stroke_paths),
        ):
            src_set.remove(item)
            existing_stroke, src_node = item


            for cluster_stroke, paths in found_right_clusters:
                for existing_stroke_1, src_node_1 in (*paths[1], *paths[2]):
                    if not can_add_stroke_on(existing_stroke_1, cluster_stroke): continue

                    key = existing_stroke_1 + cluster_stroke
                    right_stroke_paths.add((key, src_node_1))


            if right_stroke is not None:
                if not can_add_stroke_on(existing_stroke, right_stroke):
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
                if not can_add_stroke_on(existing_stroke, right_alt_stroke): continue
                key = existing_stroke + right_alt_stroke
                right_alt_stroke_paths.add((key, src_node))


    if final_node is None:
        return

    trie.set_translation(final_node, translation)


def _update_cluster_tracking(
    cluster_consonants: list[Phoneme],
    cluster_consonant_nodes: list[int],
    cluster_paths: list[tuple[tuple[tuple[Stroke, int], ...], ...]],
    new_consonant: Phoneme,
    new_paths: tuple[set[tuple[Stroke, int]], ...]
):
    # update cluster identification
    new_cluster_consonants: list[Phoneme] = []
    new_cluster_consonant_nodes: list[int] = []
    new_cluster_paths: list[tuple[tuple[tuple[Stroke, int], ...], ...]] = []
    for consonant, cluster_node, paths in zip(
        cluster_consonants + [new_consonant],
        cluster_consonant_nodes + [_clusters_trie.ROOT],
        cluster_paths + [tuple(tuple(paths_set) for paths_set in new_paths)]
    ):
        new_cluster_node = _clusters_trie.get_dst_node(cluster_node, new_consonant)
        if new_cluster_node is None: continue

        new_cluster_consonants.append(consonant)
        new_cluster_consonant_nodes.append(new_cluster_node)
        new_cluster_paths.append(paths)

    return new_cluster_consonants, new_cluster_consonant_nodes, new_cluster_paths

def _if_cluster_found(
    cluster_consonants: list[Phoneme],
    cluster_consonant_nodes: list[int],
    cluster_paths: list[tuple[tuple[tuple[Stroke, int], ...], ...]],
):
    def handler(fn: Callable[[Phoneme, Stroke, tuple[tuple[tuple[Stroke, int], ...], ...]], None]):
        for consonant, cluster_node, paths in zip(cluster_consonants, cluster_consonant_nodes, cluster_paths):
            cluster_stroke = _clusters_trie.get_translation(cluster_node)
            if cluster_stroke is None: continue

            fn(consonant, cluster_stroke, paths)

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