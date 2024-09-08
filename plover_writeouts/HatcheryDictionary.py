from typing import Optional, Callable
import json

from plover.steno import Stroke
from plover.steno_dictionary import StenoDictionary
import plover.log

class HatcheryDictionary(StenoDictionary):
    readonly = True


    def __init__(self):
        super().__init__()

        """(override)"""
        self._longest_key = 12

        self.__maybe_lookup: Optional[Callable[[tuple[str, ...]], Optional[str]]] = None

    def _load(self, filepath: str):
        from .lib.lookup import build_lookup_hatchery

        with open(filepath, "r", encoding="utf-8") as file:
            self.__maybe_lookup = build_lookup_hatchery(file)
            

    def __getitem__(self, stroke_stenos: tuple[str, ...]) -> str:
        result = self.__lookup(stroke_stenos)
        if result is None:
            raise KeyError
        
        return result

    def get(self, stroke_stenos: tuple[str, ...], fallback=None) -> Optional[str]:
        result = self.__lookup(stroke_stenos)
        if result is None:
            return fallback
        
        return result
    
    def __lookup(self, stroke_stenos: tuple[str, ...]) -> Optional[str]:
        if self.__maybe_lookup is None: raise Exception("lookup occurred before load")

        return self.__maybe_lookup(stroke_stenos)

