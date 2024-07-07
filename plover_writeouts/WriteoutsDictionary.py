from typing import Optional
import json

from plover.steno import Stroke
from plover.steno_dictionary import StenoDictionary
import plover.log

from .lib.DagTrie import DagTrie

def split_stroke_parts(stroke: Stroke):
    _LEFT_BANK_CONSONANTS_SUBSTROKE = Stroke.from_steno("STKPWHR")
    _VOWELS_SUBSTROKE = Stroke.from_steno("AOEU")
    _RIGHT_BANK_CONSONANTS_SUBSTROKE = Stroke.from_steno("-FRPBLGTSDZ")

    left_bank_consonants = stroke & _LEFT_BANK_CONSONANTS_SUBSTROKE
    vowels = stroke & _VOWELS_SUBSTROKE
    right_bank_consonants = stroke & _RIGHT_BANK_CONSONANTS_SUBSTROKE

    return left_bank_consonants, vowels, right_bank_consonants


class WriteoutsDictionary(StenoDictionary):
    readonly = True


    def __init__(self):
        super().__init__()

        """(override)"""
        self._longest_key = 8

        self.__dag_trie: Optional[DagTrie[str, str]] = None

    def _load(self, filepath: str):
        from .lib.DictionaryTrieBuilder import build_dictionary_trie

        with open(filepath, "r") as file:
            map: dict[str, str] = json.load(file)

        self.__dag_trie = build_dictionary_trie(map)


        # with open(f"{filepath}.trie.js", "w") as file:
        #     file.write(self.dag_trie.to_xstate())


    def __getitem__(self, stroke_stenos: tuple[str, ...]) -> str:
        result = self.__lookup(stroke_stenos)
        if result is None:
            raise KeyError
        
        return result

    def get(self, stroke_stenos: tuple[str, ...], fallback=None) -> Optional[str]:
        result = self.__lookup(stroke_stenos)
        if result is None:
            return fallback
        
        return result
    
    def __lookup(self, stroke_stenos: tuple[str, ...]) -> Optional[str]:
        from .lib.DictionaryTrieBuilder import STROKE_BOUNDARY

        if self.__dag_trie is None:
            raise Exception("lookup occurred before load")

        current_head = DagTrie.ROOT

        dag_trie = self.__dag_trie

        # plover.log.info("new lookup")

        for i, stroke_steno in enumerate(stroke_stenos):
            stroke = Stroke.from_steno(stroke_steno)
            if len(stroke) == 0:
                return None
            
            if i > 0:
                current_head = dag_trie.get_dst_node(current_head, STROKE_BOUNDARY)
                if current_head is None:
                    return None

            left_bank_consonants, vowels, right_bank_consonants = split_stroke_parts(stroke)

            if len(left_bank_consonants) > 0:
                left_bank_consonants_keys = left_bank_consonants.keys()
                current_head = dag_trie.get_dst_node_chain(current_head, left_bank_consonants_keys)
                # plover.log.info(left_bank_consonants_keys)

                if current_head is None:
                    return None

            if len(vowels) == 0:
                return None
            # plover.log.info(vowels)
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

