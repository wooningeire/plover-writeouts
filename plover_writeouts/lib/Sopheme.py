from dataclasses import dataclass
from typing import Iterable, Sequence

from plover.steno import Stroke

from .util import can_add_stroke_on
from .config import ASTERISK_SUBSTROKE

@dataclass(frozen=True)
class Sopheme:
    ortho: str
    steno: tuple[Stroke, ...]
    phono: str

    def __str__(self):
        return f"{self.ortho}.{'/'.join(stroke.rtfcre for stroke in self.steno)}"
    
    __repr__ = __str__

    @staticmethod
    def keys_to_strokes(keys: Iterable[str], asterisk_matches: Iterable[bool]):
        strokes: list[Stroke] = []

        current_stroke = Stroke.from_integer(0)
        for key, asterisk_match in zip(keys, asterisk_matches):
            key_stroke = Stroke.from_keys((key,))
            if asterisk_match:
                key_stroke += ASTERISK_SUBSTROKE

            if can_add_stroke_on(current_stroke, key_stroke):
                current_stroke += key_stroke
            else:
                strokes.append(current_stroke)
                current_stroke = key_stroke

        if len(current_stroke) > 0:
            strokes.append(current_stroke)

        return tuple(strokes)
    
class SophemeSeq:
    sophemes: Sequence[Sopheme]

    def __init__(self, sophemes: Sequence[Sopheme]):
        self.sophemes = sophemes

    @staticmethod
    def of(sophemes: Iterable[Sopheme]):
        return SophemeSeq(tuple(sophemes))
    
    def word(self):
        return "".join(sopheme.ortho for sopheme in self.sophemes)
    
    def __str__(self):
        return str(tuple(self.sophemes))

    __repr__ = __str__