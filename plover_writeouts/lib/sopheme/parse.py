from enum import Enum, auto
from dataclasses import dataclass

from .Sopheme import Sopheme, Orthokeysymbol, Keysymbol
from ..stenophoneme import Stenophoneme


class _TokenType(Enum):
    NONE = auto()
    WHITESPACE = auto()
    CHARS = auto()
    PARENTHESIS = auto()
    BRACKET = auto()
    SYMBOL = auto()

@dataclass(frozen=True)
class _Token:
    type: _TokenType
    ch: str

def _lex_seq(seq: str):
    tokens: list[_Token] = []

    state = _TokenType.NONE
    current_token = ""

    def step(target_state: _TokenType):
        nonlocal state
        nonlocal current_token

        if state == target_state:
            current_token += ch
        else:
            tokens.append(_Token(state, current_token))
            current_token = ch

        state = target_state

    for ch in seq:
        if ch == " ":
            step(_TokenType.WHITESPACE)
        elif ch.isalnum() or ch in "-/@":
            step(_TokenType.CHARS)
        elif ch in "()":
            step(_TokenType.PARENTHESIS)
        elif ch in "[]":
            step(_TokenType.BRACKET)
        else:
            step(_TokenType.SYMBOL)
    
    return tuple(tokens)


class _ParserState(Enum):
    NONE = auto()
    ORTHO = auto()
    POST_ORTHO = auto()
    PHONO = auto()
    STRESS = auto()
    STENO = auto()
    PHONEME = auto()
    SYMBOL = auto()
    GROUP = auto()


def parse_sopheme_seq(seq: str):
    tokens = _lex_seq(seq)
    # state = _ParserState.NONE

    # sophemes: list[Sopheme] = []

    # def _parse_sopheme_tokens(sopheme_tokens: tuple[_Token, ...]):
    #     nonlocal state

    #     assert state == _ParserState.NONE

    #     orthokeysymbols: list[Orthokeysymbol] = []
    #     ortho: str
    #     keysymbol: str
    #     steno: str

    #     for token in sopheme_tokens:
    #         match state:
    #             case _ParserState.NONE:
    #                 match token.type:
    #                     case _TokenType.CHARS:
    #                         state = _ParserState.ORTHO
    #                         ortho = token.ch
    #                     case _TokenType.SYMBOL:
    #                         state = _ParserState.POST_ORTHO
    #                     case _:
    #                         raise TypeError

    #             case _ParserState.ORTHO:
    #                 match token.type:
    #                     case _TokenType.SYMBOL:
    #                         state = _ParserState.POST_ORTHO
    #                     case _:
    #                         raise TypeError
                        
    #             case _ParserState.POST_ORTHO:
    #                 match token.type:
    #                     case _TokenType.CHARS:
    #                         state = _ParserState.PHONO
    #                         keysymbol = token.ch
    #                     case _:
    #                         raise TypeError
        



    # sopheme_start_index = 0
    # for i in range(0, len(tokens)):
    #     if tokens[i].type is _TokenType.WHITESPACE:
    #         _parse_sopheme_tokens(tokens[sopheme_start_index:i + 1])
    #         sopheme_start_index += 1
    #         continue
        
