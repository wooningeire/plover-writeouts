from typing import Iterable

from plover.steno import Stroke

from ..stenophoneme.Stenophoneme import vowel_phonemes
from ..stenophoneme.stenophoneme_util import split_consonant_phonemes
from ..sopheme.Sopheme import Sopheme
from ..util.util import split_stroke_parts
from ..theory.theory import (
    Stenophoneme,
    DIPHTHONG_TRANSITIONS_BY_FIRST_VOWEL,
    CHORDS_TO_PHONEMES_VOWELS,
)
from .build_trie import ConsonantVowelGroup, OutlinePhonemes

def get_outline_phonemes(outline: Iterable[Stroke]):
    consonant_vowel_groups: list[ConsonantVowelGroup] = []

    current_group_consonants: list[Stenophoneme] = []
    
    for stroke in outline:
        left_bank_consonants, vowels, right_bank_consonants, asterisk = split_stroke_parts(stroke)
        if len(asterisk) > 0:
            return None

        current_group_consonants.extend(split_consonant_phonemes(left_bank_consonants))

        if len(vowels) > 0:
            is_diphthong_transition = len(consonant_vowel_groups) > 0 and len(current_group_consonants) == 0
            if is_diphthong_transition and (prev_vowel := consonant_vowel_groups[-1].vowel) in DIPHTHONG_TRANSITIONS_BY_FIRST_VOWEL:
                current_group_consonants.append(DIPHTHONG_TRANSITIONS_BY_FIRST_VOWEL[prev_vowel])

            consonant_vowel_groups.append(ConsonantVowelGroup(tuple(current_group_consonants), CHORDS_TO_PHONEMES_VOWELS[vowels]))

            current_group_consonants = []

        current_group_consonants.extend(split_consonant_phonemes(right_bank_consonants))

    return OutlinePhonemes(tuple(consonant_vowel_groups), tuple(current_group_consonants))

def get_sopheme_phonemes(sophemes: Iterable[Sopheme]):
    consonant_vowel_groups: list[ConsonantVowelGroup] = []

    current_group_consonants: list[Stenophoneme] = []
    
    for sopheme in sophemes:
        if sopheme.phoneme is None and len(sopheme.steno) == 0:
            continue

        elif sopheme.phoneme in vowel_phonemes:
            is_diphthong_transition = len(consonant_vowel_groups) > 0 and len(current_group_consonants) == 0
            if is_diphthong_transition and (prev_vowel := consonant_vowel_groups[-1].vowel) in DIPHTHONG_TRANSITIONS_BY_FIRST_VOWEL:
                current_group_consonants.append(DIPHTHONG_TRANSITIONS_BY_FIRST_VOWEL[prev_vowel])

            consonant_vowel_groups.append(ConsonantVowelGroup(tuple(current_group_consonants), sopheme.phoneme))
            
            current_group_consonants = []
            
        elif any(any(key in stroke.rtfcre for key in "AOEU") for stroke in sopheme.steno):
            is_diphthong_transition = len(consonant_vowel_groups) > 0 and len(current_group_consonants) == 0
            if is_diphthong_transition and (prev_vowel := consonant_vowel_groups[-1].vowel) in DIPHTHONG_TRANSITIONS_BY_FIRST_VOWEL:
                current_group_consonants.append(DIPHTHONG_TRANSITIONS_BY_FIRST_VOWEL[prev_vowel])

            for stroke in sopheme.steno:
                vowel_substroke = stroke & Stroke.from_steno("AOEU")
                if len(vowel_substroke) > 0:
                    break
                
            vowel_phoneme = CHORDS_TO_PHONEMES_VOWELS[vowel_substroke]

            consonant_vowel_groups.append(ConsonantVowelGroup(tuple(current_group_consonants), vowel_phoneme))

            current_group_consonants = []
        
        else:
            if sopheme.phoneme is not None:
                current_group_consonants.append(sopheme.phoneme)
            else:
                for stroke in sopheme.steno:
                    current_group_consonants.extend(split_consonant_phonemes(stroke))


    return OutlinePhonemes(tuple(consonant_vowel_groups), tuple(current_group_consonants))
