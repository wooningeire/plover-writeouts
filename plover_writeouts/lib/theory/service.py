
from plover.steno import Stroke

from ..stenophoneme.Stenophoneme import Stenophoneme
from ..sopheme.Sound import Sound
from .spec import TheorySpec
from ..util.Trie import Trie, ReadonlyTrie

class TheoryService:
    def __init__(self, spec: type[TheorySpec]):
        self.spec = spec

        self.clusters_trie = self.__build_clusters_trie()
        self.vowel_clusters_trie = self.__build_vowel_clusters_trie()
        self.__split_consonant_phonemes = self.__build_consonants_splitter()

    @staticmethod
    def theory(spec: type[TheorySpec]) -> "TheoryService":
        assert not (spec.LINKER_CHORD & ~spec.LEFT_BANK_CONSONANTS_SUBSTROKE), "Linker chord must only consist of starter keys"

        return TheoryService(spec)

    def __build_clusters_trie(self) -> ReadonlyTrie[Stenophoneme, Stroke]:
        clusters_trie: Trie[Stenophoneme, Stroke] = Trie()
        for phonemes, stroke in self.spec.CLUSTERS.items():
            current_head = clusters_trie.ROOT
            for key in phonemes:
                current_head = clusters_trie.get_dst_node_else_create(current_head, key)

            clusters_trie.set_translation(current_head, stroke)
        return clusters_trie.frozen()
    
    def __build_vowel_clusters_trie(self) -> ReadonlyTrie["Stenophoneme | Stroke", Stroke]:
        clusters_trie: "Trie[Stenophoneme | Stroke, Stroke]" = Trie()
        for phonemes, stroke in self.spec.VOWEL_CONSCIOUS_CLUSTERS.items():
            current_head = clusters_trie.ROOT
            for key in phonemes:
                current_head = clusters_trie.get_dst_node_else_create(current_head, key)

            clusters_trie.set_translation(current_head, stroke)
        return clusters_trie.frozen()
    
    def __build_consonants_splitter(self):
        _CONSONANT_CHORDS: dict[Stroke, tuple[Stenophoneme, ...]] = {
            **{
                stroke: (phoneme,)
                for phoneme, stroke in self.spec.PHONEMES_TO_CHORDS_LEFT.items()
            },
            **{
                stroke: (phoneme,)
                for phoneme, stroke in self.spec.PHONEMES_TO_CHORDS_RIGHT.items()
            },

            **{
                Stroke.from_steno(steno): phonemes
                for steno, phonemes in {
                    "PHR": (Stenophoneme.P, Stenophoneme.L),
                    "TPHR": (Stenophoneme.F, Stenophoneme.L),
                }.items()
            },
        }

        def _build_consonants_trie():
            consonants_trie: Trie[str, tuple[Stenophoneme, ...]] = Trie()
            for stroke, _phoneme in _CONSONANT_CHORDS.items():
                current_head = consonants_trie.get_dst_node_else_create_chain(consonants_trie.ROOT, stroke.keys())
                consonants_trie.set_translation(current_head, _phoneme)
            return consonants_trie.frozen()
        _consonants_trie = _build_consonants_trie()


        def split_consonant_phonemes(consonants_stroke: Stroke):
            keys = consonants_stroke.keys()
            
            chord_start_index = 0
            while chord_start_index < len(keys):
                current_node = _consonants_trie.ROOT

                longest_chord_end_index = chord_start_index

                entry: tuple[Stenophoneme, ...] = ()

                for seek_index in range(chord_start_index, len(keys)):
                    key = keys[seek_index]
                    
                    current_node = _consonants_trie.get_dst_node(current_node, key)
                    if current_node is None:
                        break

                    new_entry = _consonants_trie.get_translation(current_node)
                    if new_entry is None:
                        continue
                
                    entry = new_entry
                    longest_chord_end_index = seek_index

                yield from entry

                chord_start_index = longest_chord_end_index + 1
        
        return split_consonant_phonemes

    
    def left_consonant_chord(self, sound: Sound) -> Stroke:
        return self.spec.PHONEMES_TO_CHORDS_LEFT[sound.phoneme]
    
    def right_consonant_chord(self, sound: Sound) -> Stroke:
        return self.spec.PHONEMES_TO_CHORDS_RIGHT[sound.phoneme]
    
    def split_consonant_phonemes(self, stroke: Stroke):
        return self.__split_consonant_phonemes(stroke)