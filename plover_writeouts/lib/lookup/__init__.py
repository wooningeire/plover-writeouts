from typing import TextIO

from plover.steno import Stroke
import plover.log

from ..util.Trie import NondeterministicTrie
from ..sopheme.Sopheme import Sopheme
from .build_trie import add_entry
from .build_lookup import create_lookup_for
from .get_sophemes import get_outline_phonemes, get_sopheme_phonemes

def build_lookup_json(mappings: dict[str, str]):
    trie: NondeterministicTrie[str, str] = NondeterministicTrie()

    for outline_steno, translation in mappings.items():
        phonemes = get_outline_phonemes(Stroke.from_steno(steno) for steno in outline_steno.split("/"))
        if phonemes is None:
            continue
        add_entry(trie, phonemes, translation)

    # plover.log.debug(str(trie))
    return create_lookup_for(trie)


def build_lookup_hatchery(file: TextIO):
    import json

    trie: NondeterministicTrie[str, str] = NondeterministicTrie()

    entries_json = json.load(file)
    for entry in entries_json:
        sophemes = tuple(Sopheme.parse_sopheme_dict(sopheme_json) for sopheme_json in entry)
        add_entry(trie, get_sopheme_phonemes(sophemes), Sopheme.get_translation(sophemes))

    # while len(line := file.readline()) > 0:
    #     _add_entry(trie, Sopheme.parse_seq())

    return create_lookup_for(trie)