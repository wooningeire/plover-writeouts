from typing import Generic, TypeVar, Callable

from plover.steno import Stroke

S = TypeVar("S")
T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")

class DagTrie(Generic[K, V]):
    """A dag used similarly to a trie."""

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
    
    def link(self, src_node: int, dst_node: int, key: K):
        self.__nodes[src_node][key] = dst_node
    
    def link_chain(self, src_node: int, dst_node: int, keys: tuple[K, ...]):
        current_node = src_node
        for key in keys[:-1]:
            current_node = self.get_dst_node_else_create(current_node, key)
        self.__nodes[current_node][keys[-1]] = dst_node
    
    def set_translation(self, node: int, translation: V):
        self.__translations[node] = translation
    
    def get_translation(self, node: int):
        return self.__translations.get(node, None)
