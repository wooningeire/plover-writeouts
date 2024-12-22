from dataclasses import dataclass

from .Sopheme import Sopheme
from ..stenophoneme.Stenophoneme import Stenophoneme

@dataclass
class Sound:
    phoneme: Stenophoneme
    sopheme: "Sopheme | None"

    @staticmethod
    def from_sopheme(sopheme: Sopheme):
        assert sopheme.phoneme is not None
        return Sound(sopheme.phoneme, sopheme)