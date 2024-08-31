from dataclasses import dataclass
from typing import Generic, TypeVar, Iterable

from plover.steno import Stroke

from .Stenophoneme import Stenophoneme
from .util import can_add_stroke_on
from .config import ASTERISK_SUBSTROKE

@dataclass(frozen=True)
class AsteriskableKey:
    """A steno key, along with whether its stroke included a modifier key (asterisk)."""

    key: str
    asterisk: bool

    @staticmethod
    def annotations_from_outline(outline_steno: str):
        return AsteriskableKey.annotations_from_strokes(Stroke.from_steno(steno) for steno in outline_steno.split("/"))
    
    @staticmethod
    def annotations_from_strokes(strokes: Iterable[Stroke]):
        return tuple(
            AsteriskableKey(key, has_asterisk)
            for stroke, has_asterisk in (
                (stroke - ASTERISK_SUBSTROKE, ASTERISK_SUBSTROKE in stroke)
                for stroke in strokes
            )
            for key in stroke.keys() 
        )
    
    def __str__(self):
        return f"{self.key}{'(*)' if self.asterisk else ''}"
    
    __repr__ = __str__

T = TypeVar("T")

@dataclass(frozen=True)
class AnnotatedChord(Generic[T]):
    data: T
    chord: tuple[Stroke, ...]

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
    
    def n_keys(self):
        return sum(len(stroke) for stroke in self.chord)

    def __str__(self):
        return f"{self.data}.{'/'.join(stroke.rtfcre for stroke in self.chord)}"
    
    __repr__ = __str__

@dataclass(frozen=True)
class Phono:
    keysymbols: tuple[str, ...]
    phoneme: "Stenophoneme | str | None"
    steno: tuple[Stroke, ...]

    def __str__(self):
        out = " ".join(self.keysymbols)
        if len(self.keysymbols) > 1:
            out = f"({out})"


        out += f".{self.phoneme}" if self.phoneme is not None else "."

        if len(self.steno) > 0:
            out += f"[{'/'.join(stroke.rtfcre for stroke in self.steno)}]"

        return out
    
    __repr__ = __str__