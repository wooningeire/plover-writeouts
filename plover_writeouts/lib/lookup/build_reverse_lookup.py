from plover.steno import Stroke
import plover.log

from ..theory.theory import amphitheory
from ..util.Trie import NondeterministicTrie
from ..util.config import TRIE_STROKE_BOUNDARY_KEY, TRIE_LINKER_KEY


def create_reverse_lookup_for(trie: NondeterministicTrie[str, str]):
    reverse_lookup = trie.build_reverse_lookup()
    
    def search(translation: str):
        valid_outlines: list[tuple[str, ...]] = []
        
        for seq in reverse_lookup(translation):
            outline: list[str] = []
            latest_stroke: Stroke = Stroke.from_integer(0)
            invalid = False
            for key in seq:
                if key == TRIE_STROKE_BOUNDARY_KEY:
                    outline.append(latest_stroke.rtfcre)
                    latest_stroke = Stroke.from_integer(0)
                    continue

                if key == TRIE_LINKER_KEY:
                    key_stroke = amphitheory.spec.LINKER_CHORD
                else: 
                    key_stroke = Stroke.from_steno(key)

                if amphitheory.can_add_stroke_on(latest_stroke, key_stroke):
                    latest_stroke += key_stroke
                else:
                    invalid = True
                    break

            if not invalid:
                outline.append(latest_stroke.rtfcre)
                valid_outlines.append(tuple(outline))

        return valid_outlines
    
    return search