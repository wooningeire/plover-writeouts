from dataclasses import dataclass
from typing import Iterable

from .steno_annotations import AnnotatedChord

@dataclass(frozen=True)
class Sopheme:
    ortho: str
    stenophonemes: tuple[AnnotatedChord[tuple[str, ...]], ...]

    def __str__(self):
        return f"{self.ortho}.{self.stenophonemes}"
    
    __repr__ = __str__

    @staticmethod
    def join_word(sophemes: "Iterable[Sopheme]"):
        return "".join(sopheme.ortho for sopheme in sophemes)