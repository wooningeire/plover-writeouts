from enum import Enum, auto

class Phoneme(Enum):
    S = auto()
    T = auto()
    K = auto()
    P = auto()
    W = auto()
    H = auto()
    R = auto()

    Z = auto()
    J = auto()
    V = auto()
    D = auto()
    G = auto()
    F = auto()
    N = auto()
    Y = auto()
    B = auto()
    M = auto()
    L = auto()

    CH = auto()
    SH = auto()
    TH = auto()

    NG = auto()

    ANY_VOWEL = auto()

    DUMMY = auto()

    def __str__(self):
        return self.name
    
    def __repr__(self):
        return self.__str__()