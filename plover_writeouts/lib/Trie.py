from typing import Generic, TypeVar
import traceback

import plover.log

S = TypeVar("S")
T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")

class Trie(Generic[K, V]):
    ROOT = 0
    
    def __init__(self):
        self.__nodes: list[dict[K, int]] = [{}]
        self.__translations: dict[int, V] = {}

    def get_dst_node_else_create(self, src_node: int, key: K):
        transitions = self.__nodes[src_node]
        if key in transitions:
            return transitions[key]
        
        new_node_id = len(self.__nodes)
        transitions[key] = new_node_id
        self.__nodes.append({})

        return new_node_id

    def get_dst_node_else_create_chain(self, src_node: int, keys: tuple[K, ...]):
        current_node = src_node
        for key in keys:
            current_node = self.get_dst_node_else_create(current_node, key)
        return current_node
    
    def get_dst_node(self, src_node: int, key: K):
        return self.__nodes[src_node].get(key, None)
    
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
        return self.__translations.get(node, None)

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
    
    def __init__(self):
        self.__nodes: list[dict[K, list[int]]] = [{}]
        self.__translations: dict[int, V] = {}

    def get_first_dst_node_else_create(self, src_node: int, key: K) -> int:
        transitions = self.__nodes[src_node]
        if key in transitions:
            return transitions[key][0]
        
        new_node_id = len(self.__nodes)
        transitions[key] = [new_node_id]
        self.__nodes.append({})

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
            for node in self.__nodes[src_node].get(key, [])
        )
    
    def get_dst_nodes_chain(self, src_nodes: set[int], keys: tuple[K, ...]):
        current_nodes = src_nodes
        for key in keys:
            current_nodes = self.get_dst_nodes(current_nodes, key)
            if len(current_nodes) == 0:
                return current_nodes
        return current_nodes
    
    def link(self, src_node: int, dst_node: int, key: K):
        if key in self.__nodes[src_node]:
            self.__nodes[src_node][key].append(dst_node)
        else:
            self.__nodes[src_node][key] = [dst_node]
    
    def link_chain(self, src_node: int, dst_node: int, keys: tuple[K, ...]):
        current_node = src_node
        for key in keys[:-1]:
            current_node = self.get_first_dst_node_else_create(current_node, key)

        self.link(current_node, dst_node, keys[-1])
    
    def set_translation(self, node: int, translation: V):
        self.__translations[node] = translation
    
    def get_translation(self, nodes: set[int]):
        for node in nodes:
            translation = self.__translations.get(node, None)
            if translation is not None:
                return translation
        return None

    def __str__(self):
        lines: list[str] = []

        for i, transitions in enumerate(self.__nodes):
            translation = self.__translations.get(i, None)
            lines.append(f"""{i}{f" : {translation}" if translation is not None else ""}""")
            for key, targets in transitions.items():
                lines.append(f"""\t{key}\t ->\t {",".join(str(node) for node in targets)}""")

        return "\n".join(lines)