from typing import Generic, Optional, TypeVar

from plover.steno import Stroke
import plover.log

from .config import TRIE_STROKE_BOUNDARY_KEY

S = TypeVar("S")
T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")

class Trie(Generic[K, V]):
    ROOT = 0
    
    def __init__(self):
        self.__nodes: list[dict[int, int]] = [{}]
        self.__translations: dict[int, V] = {}
        self.__keys: dict[K, int] = {}

    def get_dst_node_else_create(self, src_node: int, key: K):
        key_id = self.__get_key_id(key)

        transitions = self.__nodes[src_node]
        if key_id in transitions:
            return transitions[key_id]
        
        new_node_id = len(self.__nodes)
        transitions[key_id] = new_node_id
        self.__nodes.append({})

        return new_node_id

    def get_dst_node_else_create_chain(self, src_node: int, keys: tuple[K, ...]):
        current_node = src_node
        for key in keys:
            current_node = self.get_dst_node_else_create(current_node, key)
        return current_node
    
    def get_dst_node(self, src_node: int, key: K):
        return self.__nodes[src_node].get(self.__get_key_id(key))
    
    def get_dst_node_chain(self, src_node: int, keys: tuple[K, ...]):
        current_node = src_node
        for stroke in keys:
            current_node = self.get_dst_node(current_node, stroke)
            if current_node is None:
                return None
        return current_node
    
    def set_translation(self, node: int, translation: V):
        self.__translations[node] = translation
    
    def get_translation(self, node: int):
        return self.__translations.get(node)
    
    def __get_key_id(self, key: K):
        if key in self.__keys:
            return self.__keys[key]
        
        new_key_id = len(self.__keys)
        self.__keys[key] = new_key_id
        return new_key_id

#     def to_xstate(self):
#         return (
#             """
# import { createMachine } from "xstate";

# export const machine = createMachine({
#   context: {},
#   id: "trie",
#   initial: "0",
#   states: {
# """ +
#             "".join(f"""    "{i}": {{
#       on: {{
#         {" ".join(f'"{trigger}": {{ target: "{dst_node}" }},' for trigger, dst_node in transitions.items())}
#       }},
#     }},
# """ for i, transitions in enumerate(self.__nodes)) +
# """
#   },
# }).withConfig({});
# """)

class NondeterministicTrie(Generic[K, V]):
    """A trie that can be in multiple states at once."""

    ROOT = 0
    
    def __init__(self, *, with_root=True):
        self.__nodes: list[dict[int, list[int]]] = [{}] if with_root else []
        self.__translations: dict[int, V] = {}
        self.__keys: dict[K, int] = {}

    def get_first_dst_node_else_create(self, src_node: int, key: K) -> int:
        key_id = self.__get_key_id(key)

        transitions = self.__nodes[src_node]
        if key_id in transitions:
            return transitions[key_id][0]
        
        new_node_id = self.__create_new_node()
        transitions[key_id] = [new_node_id]
        return new_node_id

    def get_first_dst_node_else_create_chain(self, src_node: int, keys: tuple[K, ...]) -> int:
        current_node = src_node
        for key in keys:
            current_node = self.get_first_dst_node_else_create(current_node, key)
        return current_node
    
    def get_dst_nodes(self, src_nodes: set[int], key: K):
        return set(
            node
            for src_node in src_nodes
            for node in self.__nodes[src_node].get(self.__get_key_id(key), [])
        )
    
    def get_dst_nodes_chain(self, src_nodes: set[int], keys: tuple[K, ...]):
        current_nodes = src_nodes
        for key in keys:
            current_nodes = self.get_dst_nodes(current_nodes, key)
            # plover.log.debug(f"\t{key}\t {current_nodes}")
            if len(current_nodes) == 0:
                return current_nodes
        return current_nodes
    
    def link(self, src_node: int, dst_node: int, key: K):
        key_id = self.__get_key_id(key)
        
        if key_id in self.__nodes[src_node]: # and dst_node not in self.__nodes[src_node][key]
            self.__nodes[src_node][key_id].append(dst_node)
        else:
            self.__nodes[src_node][key_id] = [dst_node]
    
    def link_chain(self, src_node: int, dst_node: int, keys: tuple[K, ...]):
        current_node = src_node
        for key in keys[:-1]:
            current_node = self.get_first_dst_node_else_create(current_node, key)

        self.link(current_node, dst_node, keys[-1])
    
    def set_translation(self, node: int, translation: V):
        self.__translations[node] = translation
    
    def get_translation_single(self, node: int):
        translation = self.__translations.get(node)
        if translation is not None:
            return translation
    
    def get_translation(self, nodes: set[int]):
        for node in nodes:
            translation = self.__translations.get(node)
            if translation is not None:
                return translation
        return None

    def __str__(self):
        lines: list[str] = []

        key_ids_to_keys = self.__key_ids_to_keys()

        for i, transitions in enumerate(self.__nodes):
            translation = self.__translations.get(i, None)
            lines.append(f"""{i}{f" : {translation}" if translation is not None else ""}""")
            for key_id, dst_nodes in transitions.items():
                lines.append(f"""\t{key_ids_to_keys[key_id]}\t ->\t {",".join(str(node) for node in dst_nodes)}""")

        return "\n".join(lines)
    
    def optimized(self: "NondeterministicTrie[str, str]"):
        # from pympler.asizeof import asizeof

        new_trie: NondeterministicTrie[str, str] = NondeterministicTrie()
        self.__transfer_node_and_descendants_if_necessary(new_trie, self.ROOT, {0: 0}, Stroke.from_keys(()), set(), {0}, self.__key_ids_to_keys())
#         plover.log.debug(f"""

# Optimized lookup trie.
# \t{self.__n_nodes():,} nodes, {self.__n_transitions():,} transitions, {self.__n_translations():,} translations ({asizeof(self):,} bytes)
# \t\t->
# \t{new_trie.__n_nodes():,} nodes, {new_trie.__n_transitions():,} transitions, {new_trie.__n_translations():,} translations ({asizeof(new_trie):,} bytes)
# """)
        return new_trie
    
    def __get_key_id(self, key: K):
        if key in self.__keys:
            return self.__keys[key]
        
        new_key_id = len(self.__keys)
        self.__keys[key] = new_key_id
        return new_key_id

    def __create_new_node(self):
        new_node_id = len(self.__nodes)
        self.__nodes.append({})
        return new_node_id


    def __transfer_node_and_descendants_if_necessary(
        self: "NondeterministicTrie[str, str]",
        new_trie: "NondeterministicTrie[str, str]",
        orig_node_id: int,
        new_node_mapping: dict[int, int],
        current_stroke: Stroke,
        visited_nodes: set[int],
        translated_nodes: set[int],
        key_ids_to_keys: dict[int, str],
    ) -> bool:
        if orig_node_id in visited_nodes:
            return orig_node_id in new_node_mapping
        visited_nodes.add(orig_node_id)


        new_node_id: Optional[int] = new_node_mapping.get(orig_node_id)
        if orig_node_id not in translated_nodes:
            translated_nodes.add(orig_node_id)

            translation = self.get_translation_single(orig_node_id)
            if translation is not None:
                new_node_id = new_trie.__create_new_node()
                new_trie.set_translation(new_node_id, translation)
                new_node_mapping[orig_node_id] = new_node_id


        if len(current_stroke) > 0:
            latest_key_stroke = Stroke.from_keys((current_stroke.keys()[-1],))
        else:
            latest_key_stroke = None

        for key_id, dst_nodes in self.__nodes[orig_node_id].items():
            if key_id == self.__keys[TRIE_STROKE_BOUNDARY_KEY]:
                new_stroke = Stroke.from_keys(())
            else:
                new_key_stroke = Stroke.from_steno(key_ids_to_keys[key_id])
                if latest_key_stroke is not None and len(new_key_stroke) > 0 and latest_key_stroke >= Stroke.from_keys((new_key_stroke.keys()[0],)):
                    # The new stroke would violate steno order if it continued off the current stroke
                    continue

                new_stroke = current_stroke + new_key_stroke

            for dst_node in set(dst_nodes):
                if not self.__transfer_node_and_descendants_if_necessary(new_trie, dst_node, new_node_mapping, new_stroke, visited_nodes, translated_nodes, key_ids_to_keys): continue
                
                if new_node_id is None:
                    new_node_id = new_trie.__create_new_node()
                    new_node_mapping[orig_node_id] = new_node_id
                new_trie.link(new_node_id, new_node_mapping[dst_node], key_ids_to_keys[key_id])

        return new_node_id is not None
    

    def __n_nodes(self):
        return len(self.__nodes)
    
    def __n_transitions(self):
        return sum(sum(len(dst_nodes) for dst_nodes in transitions.values()) for transitions in self.__nodes)
    
    def __n_translations(self):
        return len(self.__translations)
    
    def __key_ids_to_keys(self):
        return {
            key_id: key
            for key, key_id in self.__keys.items()
        }