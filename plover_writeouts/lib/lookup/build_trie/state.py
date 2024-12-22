from typing import NamedTuple
from dataclasses import dataclass

from ...util.Trie import NondeterministicTrie
from ...sopheme.Sound import Sound

class ConsonantVowelGroup(NamedTuple):
    consonants: tuple[Sound, ...]
    vowel: Sound

@dataclass(frozen=True)
class OutlineSounds:
    nonfinals: tuple[ConsonantVowelGroup, ...]
    final_consonants: tuple[Sound, ...]

    def get_consonants(self, group_index: int):
        if group_index == len(self.nonfinals):
            return self.final_consonants
        return self.nonfinals[group_index].consonants

    def get_consonant(self, group_index: int, phoneme_index: int):
        return self.get_consonants(group_index)[phoneme_index]

    def __getitem__(self, key: tuple[int, int]):
        group_index, phoneme_index = key

        if group_index == len(self.nonfinals):
            return self.final_consonants[phoneme_index]
        if phoneme_index == len(self.nonfinals[group_index].consonants):
            return self.nonfinals[group_index].vowel
        return self.nonfinals[group_index].consonants[phoneme_index]
    
    def decrement_consonant_index(self, group_index: int, phoneme_index: int):
        current_consonants = self.get_consonants(group_index)

        phoneme_index -= 1

        while phoneme_index == -1:
            if group_index == 0:
                return None
        
            group_index -= 1
            current_consonants = self.get_consonants(group_index)
            phoneme_index = len(current_consonants) - 1

        return group_index, phoneme_index
    
    def increment_consonant_index(self, group_index: int, phoneme_index: int):
        current_consonants = self.get_consonants(group_index)

        phoneme_index += 1

        while phoneme_index == len(current_consonants):
            if group_index == len(self.nonfinals):
                return None
        
            group_index += 1
            phoneme_index = 0
            current_consonants = self.get_consonants(group_index)

        return group_index, phoneme_index
    
    def increment_index(self, group_index: int, phoneme_index: int):
        current_consonants = self.get_consonants(group_index)

        phoneme_index += 1

        if group_index == len(self.nonfinals) and phoneme_index >= len(current_consonants):
            return None

        if group_index < len(self.nonfinals) and phoneme_index > len(current_consonants):
            group_index += 1
            phoneme_index = 0
            current_consonants = self.get_consonants(group_index)

        if group_index == len(self.nonfinals) and phoneme_index >= len(current_consonants):
            return None

        return group_index, phoneme_index
    
    def get_consonant_after(self, group_index: int, phoneme_index: int):
        next_index = self.increment_consonant_index(group_index, phoneme_index)
        if next_index is None:
            return None
        
        return self.get_consonant(*next_index)
    
    def get_consonant_before(self, group_index: int, phoneme_index: int):
        last_index = self.decrement_consonant_index(group_index, phoneme_index)
        if last_index is None:
            return None
        
        return self.get_consonant(*last_index)
    
@dataclass
class EntryBuilderState:
    """Convenience struct for making entry state easier to pass into helper functions"""

    trie: NondeterministicTrie[str, str]
    phonemes: OutlineSounds
    translation: str

    # The node from which the next left consonant chord will be attached
    left_consonant_src_node: "int | None" = None
    # The node from which the next right consonant chord will be attached
    right_consonant_src_node: "int | None" = None
    # The latest node constructed by adding the alternate chord for a left consonant
    last_left_alt_consonant_node: "int | None" = None
    # The latest node constructed by adding the alternate chord for a right consonant
    last_right_alt_consonant_node: "int | None" = None

    # The node constructed by adding the previous left consonant; can be None if the previous phoneme was a vowel
    prev_left_consonant_node: "int | None" = None

    # Two types of elision:
    #  - squish (placing vowel between two consonant chords on the same side)
    #  - boundary (placing vowel on the transition from right to left consonant chords)

    # The latest node which the previous vowel set was attached to
    left_elision_squish_src_node: "int | None" = None
    # The latest node which the stroke boundary between a right consonant and a left consonant was attached to
    right_elision_squish_src_node: "int | None" = None
    # The latest node constructed by adding the stroke bunnedry between a right consonant and left consonant
    left_elision_boundary_src_node: "int | None" = None

    group_index: int = -1
    phoneme_index: int = -1

    @property
    def is_first_consonant_set(self):
        return self.group_index == 0
    
    @property
    def is_first_consonant(self):
        return self.phoneme_index == 0
    
    @property
    def consonant(self):
        return self.phonemes.get_consonant(self.group_index, self.phoneme_index)
    
    @property
    def next_consonant(self):
        return self.phonemes.get_consonant_after(self.group_index, self.phoneme_index)
    
    @property
    def last_consonant(self):
        return self.phonemes.get_consonant_before(self.group_index, self.phoneme_index)

    @property
    def n_previous_syllable_consonants(self):
        return len(self.phonemes.get_consonants(self.group_index - 1)) if self.group_index > 0 else 0

    @property
    def can_elide_prev_vowel_left(self):
        return not self.is_first_consonant_set and self.is_first_consonant and self.n_previous_syllable_consonants > 0