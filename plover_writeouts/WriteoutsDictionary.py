from typing import Optional
import json

from plover.steno import Stroke
from plover.steno_dictionary import StenoDictionary
import plover.log

from plover_writeouts.lib.DagTrie import DagTrie

def get_outline_phonemes(outline: tuple[Stroke, ...]):
    _CONSONANTS_CHORDS = {
        Stroke.from_steno(steno_right): Stroke.from_steno(steno_left)
        for steno_right, steno_left in {
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
        }.items()
    }
    _LEFT_BANK_CONSONANTS_SUBSTROKE = Stroke.from_steno("STKPWHR")
    _VOWELS_SUBSTROKE = Stroke.from_steno("AOEU")
    _RIGHT_BANK_CONSONANTS_SUBSTROKE = Stroke.from_steno("-FRPBLGTSDZ")


    consonant_phonemes: list[Stroke] = []
    phonemes: list[Stroke] = []
    for stroke in outline:
        left_bank_consonant_keys = (stroke & _LEFT_BANK_CONSONANTS_SUBSTROKE)
        vowel_keys = (stroke & _VOWELS_SUBSTROKE)
        right_bank_consonant_keys = (stroke & _RIGHT_BANK_CONSONANTS_SUBSTROKE)


        phonemes.append(left_bank_consonant_keys)
        consonant_phonemes.append(left_bank_consonant_keys)

        phonemes.append(vowel_keys)

        if right_bank_consonant_keys in _CONSONANTS_CHORDS:
            mapped_keys = _CONSONANTS_CHORDS[right_bank_consonant_keys]

            phonemes.append(mapped_keys)
            consonant_phonemes.append(mapped_keys)

    return tuple(phonemes), tuple(consonant_phonemes)


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

        for outline_steno, translation in map.items():
            current_head = DagTrie.ROOT

            for stroke_steno in outline_steno.split("/"):
                stroke = Stroke.from_steno(stroke_steno)
                for key in stroke.keys():
                    current_head = dag_trie.get_dest_node(current_head, Stroke.from_steno(key))

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

        for stroke_steno in stroke_stenos:
            stroke = Stroke.from_steno(stroke_steno)
            for key in stroke.keys():
                current_head = dag_trie.find_dest_node(current_head, Stroke.from_steno(key))

                if current_head is None:
                    return None

        return dag_trie.get_translation(current_head)

