from dataclasses import dataclass
from typing import Iterable, Sequence

from .Stenophoneme import Stenophoneme
from .steno_annotations import Phono

@dataclass(frozen=True)
class Sopheme:
    ortho: str
    phono: tuple[Phono, ...]

    def __str__(self):
        out = " ".join(str(phono) for phono in self.phono)
        if len(self.phono) > 1:
            out = f"({out})"

        return f"{self.ortho}.{out}"
    
    __repr__ = __str__

    @staticmethod
    def join_word(sophemes: "Iterable[Sopheme]"):
        return "".join(sopheme.ortho for sopheme in sophemes)
    
# def match_sophemes(stenographemes: tuple[AnnotatedChord[str], ...], stenophonemes: tuple[AnnotatedChord[Sequence[str]], ...]):
#     from plover_writeouts.lib.Sopheme import Sopheme

#     sophemes: list[Sopheme] = []

#     last_added_stenophoneme_index = -1
    
#     last_added_key_index = -1


#     for stenographeme in stenographemes:
#         target_end_index = last_added_key_index + stenographeme.n_keys()
#         current_stenophonemes = []

#         if last_added_stenophoneme_index < len(stenophonemes) - 1:
#             stenophoneme_index = last_added_stenophoneme_index + 1
#             stenophonemes_key_end_index = last_added_key_index + stenophonemes[stenophoneme_index].n_keys()

#             while stenophonemes_key_end_index <= target_end_index:
#                 last_added_key_index = stenophonemes_key_end_index
#                 if stenophoneme_index >= 0:
#                     current_stenophonemes.append(stenophonemes[stenophoneme_index])
#                 last_added_stenophoneme_index = stenophoneme_index


#                 if stenophoneme_index == len(stenophonemes) - 1: break

#                 stenophoneme_index += 1
#                 stenophonemes_key_end_index += stenophonemes[stenophoneme_index].n_keys()
        
#         sophemes.append(Sopheme(stenographeme.data, tuple(current_stenophonemes)))

#     return sophemes