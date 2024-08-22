from dataclasses import dataclass

from plover.steno import Stroke

from .config import ASTERISK_SUBSTROKE

@dataclass(frozen=True)
class AnnotatedKey:
    """A steno key, along with whether its stroke included a modifier key (asterisk)."""

    key: str
    asterisk: bool

    @staticmethod
    def annotations_from_outline(outline_steno: str):
        return tuple(
            AnnotatedKey(key, has_asterisk)
            for stroke, has_asterisk in (
                (stroke - ASTERISK_SUBSTROKE, ASTERISK_SUBSTROKE in stroke)
                for stroke in (
                    Stroke.from_steno(steno)
                    for steno in outline_steno.split("/")
                )
            )
            for key in stroke.keys() 
        )
    
    def __str__(self):
        return f"{self.key}{'(*)' if self.asterisk else ''}"