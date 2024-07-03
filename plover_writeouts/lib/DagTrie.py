from plover.steno import Stroke

class DagTrie:
    """A dag used similarly to a trie."""

    ROOT = 0
    
    def __init__(self):
        self.__nodes: list[dict[Stroke, int]] = [{}]
        self.__words: dict[int, str] = {}

    def get_dest_node(self, from_node: int, key: Stroke):
        transitions = self.__nodes[from_node]
        if key in transitions:
            return transitions[key]
        
        new_node_id = len(self.__nodes)
        transitions[key] = new_node_id
        self.__nodes.append({})

        return new_node_id
    
    def find_dest_node(self, from_node: int, key: Stroke):
        return self.__nodes[from_node].get(key, None)
    
    def set_translation(self, node: int, translation: str):
        self.__words[node] = translation
    
    def get_translation(self, node: int):
        return self.__words.get(node, None)
