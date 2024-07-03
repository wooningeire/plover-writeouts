from typing import Optional
import json

from plover.steno import Stroke
from plover.steno_dictionary import StenoDictionary
import plover.log

from plover_writeouts.lib.DagTrie import DagTrie

def get_stroke_phonemes(stroke: Stroke):
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

        self.__dag_trie: Optional[DagTrie] = None

    def _load(self, filepath: str):
        with open(filepath, "r") as file:
            map: dict[str, str] = json.load(file)

        self.__dag_trie = dag_trie = DagTrie()

        _CHORD_ALTERNATIVES: dict[Stroke, Stroke] = {
            Stroke.from_steno(steno_main): Stroke.from_steno(steno_alt)
            for steno_main, steno_alt in {
                "-F": "TP",
                "-FB": "SR",
                "-FL": "TPHR",
                "-R": "R",
                "-P": "P",
                "-PB": "TPH",
                "-PL": "PH",
                "-B": "PW",
                "-BG": "K",
                "-L": "HR",
                "-G": "TKPW",
                "-T": "T",
                "-S": "S",
                "-D": "TK",
                "-Z": "STKPW",
                
                "TP": "-F",
                "SR": "-FB",
                "TPHR": "-FL",
                "R": "-R",
                "P": "-P",
                "TPH": "-PB",
                "PH": "-PL",
                "PW": "-B",
                "K": "-BG",
                "HR": "-L",
                "TKPW": "-G",
                "T": "-T",
                "S": "-S",
                "TK": "-D",
                "STKPW": "-Z",
            }.items()
        }

        for outline_steno, translation in map.items():
            current_head = DagTrie.ROOT

            last_prevowels_node = None
            consonants_since_last_vowel = []

            for stroke_steno in outline_steno.split("/"):
                stroke = Stroke.from_steno(stroke_steno)

                left_bank_consonants, vowels, right_bank_consonants = get_stroke_phonemes(stroke)

                preleft_node = current_head
                if len(left_bank_consonants) > 0:
                    left_bank_consonants_keys = tuple(Stroke.from_keys((key,)) for key in left_bank_consonants.keys())

                    current_head = dag_trie.get_dst_node_else_create_chain(current_head, left_bank_consonants_keys)
                    if left_bank_consonants in _CHORD_ALTERNATIVES:
                        alternative_keys = tuple(Stroke.from_keys((key,)) for key in _CHORD_ALTERNATIVES[left_bank_consonants].keys())
                        dag_trie.link_chain(preleft_node, current_head, alternative_keys)

                    if last_prevowels_node is not None:
                        dag_trie.link_chain(last_prevowels_node, current_head, left_bank_consonants_keys)

                    if left_bank_consonants in _CHORD_ALTERNATIVES and last_prevowels_node is not None:
                        dag_trie.link_chain(last_prevowels_node, current_head, alternative_keys)

                    last_prevowels_node = current_head

                if len(vowels) > 0:
                    current_head = dag_trie.get_dst_node_else_create(current_head, vowels)

                if len(right_bank_consonants) > 0:
                    right_bank_consonants_keys = tuple(Stroke.from_keys((key,)) for key in right_bank_consonants.keys())

                    current_head = dag_trie.get_dst_node_else_create_chain(current_head, right_bank_consonants_keys)
                    if right_bank_consonants_keys in _CHORD_ALTERNATIVES:
                        alternative_keys = tuple(Stroke.from_keys((key,)) for key in _CHORD_ALTERNATIVES[right_bank_consonants].keys())
                        dag_trie.link_chain(preleft_node, current_head, alternative_keys)

                    if last_prevowels_node is not None:
                        dag_trie.link_chain(last_prevowels_node, current_head, right_bank_consonants_keys)

                    if left_bank_consonants in _CHORD_ALTERNATIVES and last_prevowels_node is not None:
                        dag_trie.link_chain(last_prevowels_node, current_head, alternative_keys)

                    last_prevowels_node = current_head



            dag_trie.set_translation(current_head, translation)


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
        if self.__dag_trie is None:
            raise Exception("lookup occurred before load")

        current_head = DagTrie.ROOT

        dag_trie = self.__dag_trie

        for stroke_steno in enumerate(stroke_stenos):
            stroke = Stroke.from_steno(stroke_steno)
            if len(stroke) == 0:
                return None

            left_bank_consonants, vowels, right_bank_consonants = get_stroke_phonemes(stroke)

            if len(left_bank_consonants) > 0:
                left_bank_consonants_keys = tuple(Stroke.from_keys((key,)) for key in left_bank_consonants.keys())
                current_head = dag_trie.get_dst_node_chain(current_head, left_bank_consonants_keys)
                plover.log.info(left_bank_consonants_keys)
                if current_head is None:
                    return None

            if len(vowels) == 0:
                return None
            current_head = dag_trie.get_dst_node(current_head, vowels)
            plover.log.info(vowels)
            if current_head is None:
                return None

            if len(right_bank_consonants) > 0:
                right_bank_consonants_keys = tuple(Stroke.from_keys((key,)) for key in right_bank_consonants.keys())
                current_head = dag_trie.get_dst_node_chain(current_head, right_bank_consonants_keys)
                plover.log.info(right_bank_consonants_keys)
                if current_head is None:
                    return None

        return dag_trie.get_translation(current_head)

