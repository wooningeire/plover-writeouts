from typing import Optional
import json
from collections import defaultdict

from plover.steno import Stroke
from plover.steno_dictionary import StenoDictionary
import plover.log

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

        self.__entries = {}

    def _load(self, filepath: str):
        with open(filepath, "r") as file:
            map: dict[str, str] = json.load(file)


        for outline_steno, translation in map.items():
            phonemes, consonant_phonemes = get_outline_phonemes(tuple(Stroke.from_steno(stroke_steno) for stroke_steno in outline_steno.split("/")))

            if consonant_phonemes in self.__entries:
                self.__entries[consonant_phonemes].add(translation)
            else:
                self.__entries[consonant_phonemes] = {translation}

            plover.log.info(str(phonemes))


    def __getitem__(self, key: tuple[str, ...]) -> str:
        result = self.__lookup(key)
        if result is None:
            raise KeyError
        
        return result

    def get(self, key: tuple[str, ...], fallback=None) -> Optional[str]:
        result = self.__lookup(key)
        if result is None:
            return fallback
        
        return result
    
    def __lookup(self, key: tuple[str, ...]) -> Optional[str]:
        phonemes, consonant_phonemes = get_outline_phonemes(tuple(Stroke.from_steno(stroke_steno) for stroke_steno in key))

        consonant_lookup_result = self.__entries.get(consonant_phonemes)
        if consonant_lookup_result is None:
            return None
        
        return tuple(consonant_lookup_result)[0]

