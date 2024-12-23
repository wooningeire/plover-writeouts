# Hatchery
Theory engine plugin for Plover!

Hatchery generates all possible writeouts from a word list, according to customizable theory rules.

## Entrypoints
This plugin exposes the following tools and interfaces:

### Dictionaries

#### `.theory`
> [!IMPORTANT]
> This is upcoming!

A collection of rules and settings to use when converting Hatchery entries to strokable outlines.

#### `.hatchery`
A Hatchery word list.

Each entry in a Hatchery word list is a sequence of orthographic–phonetic correspondences, referred to as **<u>sophemes</u>**. Upon loading a dictionary, Hatchery will apply your given theory rules and mappings to each entry, alongside rules such as vowel elision. The end result is that **any valid writeout** for an entry, with any combination of valid chords, elisions, and syllabic splits, will map to that entry (or some conflicting entry).

Sometimes, an outline will map to multiple possible translations, known as **<u>conflicts</u>**. Conflicts are ordered using a cost mechanism, determined by counting the number of abbreviation methods used in the outline, such as elisions (sorted into different types, such as stressed vowel vs unstressed vowel vs consonant) and clusters. The theory can specify specify these cost amounts as well as a variation cycler stroke that allows you to switch between the different conflicts in increasing order of cost.

##### File format
> [!IMPORTANT]
> This is upcoming!



##### Generating a Hatchery dictionary from JSON
`./local-utils/generate_word_list.py` takes a standard JSON dictionary (such as `lapwing-base.json`) and the [Unisyn v1.3](https://www.cstr.ed.ac.uk/projects/unisyn/) Unilex lexicon as input and produces a Hatchery dictionary as an output by automatically matching letters with phonemes/keysymbols.

## Methodology
*See the algorithms being ideated and developed in the [algorithm drafting whiteboard](https://www.figma.com/board/22f2V9ufYxLdvBtGWj6nXv/Hatchery?node-id=0-1&t=rvw11Srj6YIEvjmo-1)*

### Dictionary generation
Hatchery dictionaries are (or will be) intended to be added to directly. However, for testing or as a base, a JSON dictionary along with the Unilex lexicon can be used to generate a large starter dictionary (using `./local-utils/generate_word_list.py`).

Letters, steno chords, and keysymbols are matched and aligned using a modified variant of the [Needleman–Wunsch string alignment algorithm](https://en.wikipedia.org/wiki/Needleman–Wunsch_algorithm). First, letters are matched with keysymbols, and then those "orthokeysymbols" are matched with steno chords.

A key modification is that the mapping is many-to-many, as in, multiple letters can match with multiple keysymbols and multiple keysymbols can match with multiple steno keys, as opposed to stock Needleman–Wunsch which can only match single letters. If we are aligning the sequences $x, y$ and are currently computing the cost in cell $i, j$, then in stock Needleman–Wunsch we take the minimum among 3 costs: an indel of $x_i$, an indel of $y_j$, and a match/mismatch of $x_i, y_j$. Our modified alignment algorithm is supplied a dictionary of substrings of $x$ which map to substrings of $y$ that the aligner will consider a match. For each cell, our modified algorithm still considers the indel and mismatch cases, but for matches it will test every substring of $x$ that ends at position $i$ and look it up in the dictionary to see if it maps to some substring of $y$ that ends at position $j$. If $x, y$ have lengths $m, n$ respectively, then this incurs an additional cost of $O(m)$ for each cell, resulting in an overall time complexity of $O(m^2 n)$.

![String alignment diagram](https://github.com/user-attachments/assets/25295963-cd4f-431c-bbea-439c7e435d26)

Lapwing can be converted into a Hatchery dictionary in about 3 to 4 minutes.

### Lookup
The number of possible outlines for an entry depends on the number of combinations of possible elisions, syllabic splits, and chord choices, which scales roughly exponentially with the length of the entry. To store all these possible options while limiting redundant storage, we use a nondeterministic finite automaton/state machine that functions as a trie. Transitions are associated with one or more steno keys, with some special entries for linkers and stroke boundaries.

![Lookup trie diagram](https://github.com/user-attachments/assets/16bedccd-0ea7-4c10-b514-54b604c968d8)

While constructing paths in the trie, transitions are also associated with a (cost, translation) pair.
* The translation is used to ensure that the paths traversed during the lookup align with the translation that is found when there are no more keys in the outline to read. If a translation is found for an outline, but the path used to reach the node has some transition that is not associated with the translation, then the path is ignored.
* The cost is used to determine which translation to use in the case of conflicts, which occur when the set of nodes an outline ends at is associated with multiple valid translations. The cost is determined by e.g. whether the path is part of a cluster, inversion, elision, etc.

Constructing the trie for the entirety of Lapwing takes about 18 seconds.
