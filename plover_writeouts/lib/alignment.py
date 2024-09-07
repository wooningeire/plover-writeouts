from dataclasses import dataclass
from typing import Generator, Generic, TypeVar, Sequence, Mapping, Protocol, Iterable
from abc import ABC, abstractmethod

from .Trie import Trie

_Item = TypeVar("_Item")

class Sliceable(Protocol[_Item]):
    def __getitem__(self: "Sliceable[_Item]", slice: slice) -> "Sliceable[_Item]":
        ...

    def __len__(self) -> int:
        ...

    def __iter__(self: "Sliceable[_Item]") -> Iterable[_Item]:
        ...

Cost = TypeVar("Cost")
MatchData = TypeVar("MatchData")
InputX = TypeVar("InputX")
InputY = TypeVar("InputY")
MappingX = TypeVar("MappingX", bound=Sliceable)
MappingY = TypeVar("MappingY", bound=Sliceable)
ItemX = TypeVar("ItemX", bound=Sliceable)
ItemY = TypeVar("ItemY", bound=Sliceable)
Match = TypeVar("Match")

@dataclass(frozen=True)
class Cell(Generic[Cost, MatchData]):
    """A cell in the Needleman–Wunsch alignment matrix; represents an optimal alignment of the first x characters in a translation to the first y keys in an outline."""

    cost: Cost

    unmatched_x_start_index: int
    """The index where the sequence of trailing unmatched characters for this alignment beigins. Used during traceback when a match is not found by this cell."""
    unmatched_y_start_index: int
    """The index where the sequence of trailing unmatched keys for this alignment beigins. Used during traceback when a match is not found by this cell."""
    
    parent: "Cell[Cost, MatchData] | None"
    """The optimal sub-alignment which this alignment extends upon."""

    x: int
    y: int

    has_match: bool
    match_data: "MatchData | None" = None
    # asterisk_matches: tuple[bool, ...] = ()

    def __lt__(self, cell: "Cell"):
        return self.cost < cell.cost
    
    def __gt__(self, cell: "Cell"):
        return self.cost > cell.cost

class AlignmentService[Cost, MatchData, InputX, InputY, MappingX, MappingY, ItemX, ItemY, Match](ABC):
    MAPPINGS: Mapping[MappingX, MappingY]

    @staticmethod
    def process_input(x_input: InputX, y_input: InputY) -> tuple[Sliceable[ItemX], Sliceable[ItemY]]:
        return (x_input, y_input)

    @staticmethod
    def initial_cost() -> Cost:
        ...

    @staticmethod
    def mismatch_cost(mismatch_parent: Cell[Cost, MatchData], increment_x: bool, increment_y: bool) -> Cost:
        ...

    @staticmethod
    def generate_candidate_x_key(candidate_subseq_x: MappingX) -> Sliceable[ItemX]:
        return candidate_subseq_x
    
    @staticmethod
    def generate_candidate_y_key(candidate_subseq_y: MappingY) -> Sliceable[ItemY]:
        return candidate_subseq_y
    
    @staticmethod
    def y_seq_len(candidate_subseq_y: Sliceable[ItemY]) -> int:
        return len(candidate_subseq_y)

    @staticmethod
    def is_match(actual_subseq_y: Sliceable[ItemY], candidate_subseq_y: Sliceable[ItemY]) -> bool:
        ...

    @staticmethod
    def match_cost(parent: Cell[Cost, MatchData]) -> Cost:
        ...

    @staticmethod
    def match_data(subseq_x: Sliceable[ItemX], subseq_y: Sliceable[ItemY], pre_subseq_x: Sliceable[ItemX], pre_subseq_y: Sliceable[ItemY]) -> MatchData:
        ...

    @staticmethod
    def construct_match(seq_x: Sliceable[ItemX], seq_y: Sliceable[ItemY], start_cell: Cell[Cost, MatchData], end_cell: Cell[Cost, MatchData], match_data: "MatchData | None") -> Match:
        ...


def aligner(Service: type[AlignmentService[Cost, MatchData, InputX, InputY, MappingX, MappingY, ItemX, ItemY, Match]]):
    def align(input_x: InputX, input_y: InputY):
        """Generates an alignment between characters in a translation and keys in a Lapwing-style outline.
        
        Uses a variation of the Needleman–Wunsch algorithm.
        
        Assumptions:
        - Strict left-to-right parsing; no inversions
        """

        mappings = Service.MAPPINGS

        seq_x, seq_y = Service.process_input(input_x, input_y)

        def create_mismatch_cell(x: int, y: int, increment_x: bool, increment_y: bool):
            mismatch_parent = matrix[x if increment_x else x + 1][y if increment_y else y + 1]

            return Cell(
                Service.mismatch_cost(mismatch_parent, increment_x, increment_y),
                mismatch_parent.unmatched_x_start_index,
                mismatch_parent.unmatched_y_start_index,
                mismatch_parent,
                x + 1,
                y + 1,
                False,
            )
        

        def find_match(x: int, y: int, increment_x: bool, increment_y: bool):
            """Attempt to match any combination of the last m consecutive unmatched characters to the last n consecutive unmatched keys."""

            domain_seq_x = seq_x[:x + 1]
            domain_seq_y = seq_y[:y + 1]

            # print()
            # print(domain_seq_x, domain_seq_y, x, y)

            candidate_cells = [create_mismatch_cell(x, y, increment_x, increment_y)]


            # When not incrementing x, only consider silent chords

            for i in range((len(domain_seq_x) if increment_x else 0) + 1):
                candidate_subseq_x = domain_seq_x[len(domain_seq_x) - i:]
                candidate_subseq_x_key = Service.generate_candidate_x_key(candidate_subseq_x)
                # print("using grapheme", candidate_subseq_x_key)
                if candidate_subseq_x_key not in mappings: continue


                # When not incrementing y, only consider silent letters

                candidate_subseqs_y: Iterable[Sliceable[ItemY]]
                if increment_y:
                    candidate_subseqs_y = mappings[candidate_subseq_x_key]
                else:
                    candidate_subseqs_y = filter(lambda chord: Service.y_seq_len(chord) == 0, mappings[candidate_subseq_x_key])

                for candidate_subseq_y in candidate_subseqs_y:
                    candidate_subseq_y_key = Service.generate_candidate_y_key(candidate_subseq_y)
                    # print("testing chord", candidate_subseq_y_key)
                    actual_subseq_y = domain_seq_y[len(domain_seq_y) - len(candidate_subseq_y_key):]

                    if not Service.is_match(actual_subseq_y, candidate_subseq_y_key): continue

                    parent = matrix[x + 1 - len(candidate_subseq_x)][y + 1 - len(actual_subseq_y)]
                    
                    # print("found", candidate_subseq_x_key, candidate_subseq_y_key)
                    candidate_cells.append(
                        Cell(
                            Service.match_cost(parent),
                            x + 1,
                            y + 1,
                            parent,
                            x + 1,
                            y + 1,
                            True,
                            Service.match_data(candidate_subseq_x_key, candidate_subseq_y_key, candidate_subseq_x, candidate_subseq_y),
                        )
                    )

            return min(candidate_cells)


        # Base row and column

        matrix = [[Cell(Service.initial_cost(), 0, 0, None, 0, 0, False)]]

        for i in range(len(seq_x)):
            matrix.append([find_match(i, -1, True, False)])

        for i in range(len(seq_y)):
            matrix[0].append(find_match(-1, i, False, True))


        # Populating the matrix

        for x in range(len(seq_x)):
            for y in range(len(seq_y)):
                # Increment x: add a character from the translation
                x_candidate = find_match(x, y, True, False)

                # Increment y: add a key from the outline
                y_candidate = find_match(x, y, False, True)

                # Increment xy: both
                xy_candidate = find_match(x, y, True, True)


                matrix[x + 1].append(min(x_candidate, y_candidate, xy_candidate))


        # Display the cost matrix
        # COL_WIDTH = 16
        # print(f"{'.'.ljust(COL_WIDTH) * 2}{''.join(str(key).ljust(COL_WIDTH) for key in annotated_keys)}")
        # for r, ch in zip(matrix, f".{translation}"):
        #     print(f"{ch.ljust(COL_WIDTH)}{''.join(str(cell.cost).ljust(COL_WIDTH) for cell in r)}")


        # Traceback

        def traceback_matchings(cell: Cell[Cost, MatchData]) -> Generator[Match, None, None]:
            if cell.parent is None: return

            if cell.has_match:
                start_cell = cell.parent
                match_data = cell.match_data
            else:
                start_cell = matrix[cell.parent.unmatched_x_start_index][cell.parent.unmatched_y_start_index]
                match_data = None

            yield from traceback_matchings(start_cell)

            yield Service.construct_match(seq_x, seq_y, start_cell, cell, match_data)

        return tuple(traceback_matchings(matrix[-1][-1]))

    return align