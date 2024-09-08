from dataclasses import dataclass
import re
from typing import Iterable

from plover.steno import Stroke

from ..stenophoneme.Stenophoneme import Stenophoneme


@dataclass(frozen=True)
class Keysymbol:
    symbol: str
    match_symbol: str
    stress: int = 0
    optional: bool = False

    def __str__(self):
        out = self.symbol
        if self.stress > 0:
            out += f"!{self.stress}"
        if self.optional:
            out += "?"

        return out
    
    __repr__ = __str__

    @staticmethod
    def get_match_symbol(symbol: str):
        return re.sub(r"[\[\]\d]", "", symbol.lower())

@dataclass(frozen=True)
class Orthokeysymbol:
    keysymbols: tuple[Keysymbol, ...]
    chars: str

    def __str__(self):
        keysymbols_string = " ".join(str(keysymbol) for keysymbol in self.keysymbols)
        if len(self.keysymbols) > 1:
            keysymbols_string = f"({keysymbols_string})"

        return f"{self.chars}.{keysymbols_string}"
    
    __repr__ = __str__

@dataclass(frozen=True)
class Sopheme:
    orthokeysymbols: tuple[Orthokeysymbol, ...]
    steno: tuple[Stroke, ...]
    phoneme: "Stenophoneme | None"

    def __str__(self):
        out = " ".join(str(orthokeysymbol) for orthokeysymbol in self.orthokeysymbols)
        if len(self.orthokeysymbols) > 1 and (self.phoneme is not None or len(self.steno) > 0):
            out = f"({out})"

        if self.phoneme is not None:
            out += f"[{self.phoneme}]"
        elif len(self.steno) > 0:
            out += f"[[{'/'.join(stroke.rtfcre for stroke in self.steno)}]]"
            
        return out
    
    __repr__ = __str__

    def shortest_form(self):
        key = (
            tuple(
                (
                    tuple(keysymbol.symbol for keysymbol in orthokeysymbol.keysymbols),
                    orthokeysymbol.chars,
                )
                for orthokeysymbol in self.orthokeysymbols
            ),
            self.phoneme,
        )

        return _sopheme_shorthands.get(key, str(self))
    
    def to_dict(self):
        return {
            "orthokeysymbols": [
                {
                    "chars": orthokeysymbol.chars,
                    "keysymbols": [
                        {
                            "symbol": keysymbol.symbol,
                            "stress": keysymbol.stress,
                            "optional": keysymbol.optional,
                        }
                        for keysymbol in orthokeysymbol.keysymbols
                    ],
                }
                for orthokeysymbol in self.orthokeysymbols
            ],
            "steno": "/".join(stroke.rtfcre for stroke in self.steno),
            "phono": self.phoneme.name if isinstance(self.phoneme, Stenophoneme) else self.phoneme,
        }

    @staticmethod
    def parse_sopheme_dict(json: dict):
        return Sopheme(
            tuple(
                Orthokeysymbol(
                    tuple(
                        Keysymbol(
                            keysymbol_json["symbol"],
                            Keysymbol.get_match_symbol(keysymbol_json["symbol"]),
                            keysymbol_json["stress"],
                            keysymbol_json["optional"],
                        )
                        for keysymbol_json in orthokeysymbol_json["keysymbols"]
                    ),
                    orthokeysymbol_json["chars"],
                )
                for orthokeysymbol_json in json["orthokeysymbols"]
            ),
            tuple(Stroke.from_steno(steno) for steno in json["steno"].split("/")) if len(json["steno"]) > 0 else (),
            Stenophoneme.__dict__.get(json["phono"], json["phono"]),  
        )
    
    @staticmethod
    def get_translation(sophemes: "Iterable[Sopheme]"):
        return "".join(
            orthokeysymbol.chars
            for sopheme in sophemes
            for orthokeysymbol in sopheme.orthokeysymbols
        )


_sopheme_shorthands = {
    ((((keysymbols), ortho),), phoneme): ortho
    for (phoneme, keysymbols), orthos in {
        (Stenophoneme.P, ("p",)): ("p", "pp"),
        (Stenophoneme.T, ("t",)): ("t", "tt"),
        (Stenophoneme.K, ("k",)): ("k", "kk", "ck", "q"),
        (Stenophoneme.B, ("b",)): ("b", "bb"),
        (Stenophoneme.D, ("d",)): ("d", "dd"),
        (Stenophoneme.G, ("g",)): ("g", "gg"),
        (Stenophoneme.CH, ("ch",)): ("ch",),
        (Stenophoneme.J, ("jh",)): ("j",),
        (Stenophoneme.S, ("s",)): ("s", "ss"),
        (Stenophoneme.Z, ("z",)): ("z", "zz"),
        (Stenophoneme.SH, ("sh",)): ("sh", "ti", "ci", "si", "ssi"),
        (Stenophoneme.F, ("f",)): ("f", "ff", "ph"),
        (Stenophoneme.V, ("v",)): ("v", "vv"),
        (Stenophoneme.H, ("h",)): ("h",),
        (Stenophoneme.M, ("m",)): ("m", "mm"),
        (Stenophoneme.N, ("n",)): ("n", "nn"),
        (Stenophoneme.L, ("l",)): ("l", "ll"),
        (Stenophoneme.R, ("r",)): ("r", "rr"),
        (Stenophoneme.Y, ("y",)): ("y",),
        (Stenophoneme.W, ("w",)): ("w",),
    }.items()
    for ortho in orthos
}