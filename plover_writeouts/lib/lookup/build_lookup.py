from plover.steno import Stroke
import plover.log

from ..util.Trie import Transition, NondeterministicTrie
from ..util.util import split_stroke_parts
from ..theory.theory import (
    ALL_KEYS,
    ASTERISK_SUBSTROKE,
    TRIE_STROKE_BOUNDARY_KEY,
    TRIE_LINKER_KEY,
    LINKER_CHORD,
    VARIATION_CYCLER_STROKE,
    # VARIATION_CYCLER_STROKE_BACKWARD,
    PROHIBITED_STROKES,
)

def create_lookup_for(trie:  NondeterministicTrie[str, str]):
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
            
            if stroke == VARIATION_CYCLER_STROKE:
                n_variation += 1
                continue
            # if stroke == VARIATION_CYCLER_STROKE_BACKWARD:
            #     n_variation -= 1
            #     continue
            
            if stroke not in ALL_KEYS:
                return None
            
            if stroke in PROHIBITED_STROKES:
                return None

            if n_variation > 0:
                return None
            
            if i > 0:
                # plover.log.debug(current_nodes)
                # plover.log.debug(TRIE_STROKE_BOUNDARY_KEY)
                current_nodes = trie.get_dst_nodes(current_nodes, TRIE_STROKE_BOUNDARY_KEY)
                if len(current_nodes) == 0:
                    return None

            left_bank_consonants, vowels, right_bank_consonants, asterisk = split_stroke_parts(stroke)

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