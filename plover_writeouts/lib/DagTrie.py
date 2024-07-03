from plover.steno import Stroke

class DagTrie:
    """A dag used similarly to a trie."""

    ROOT = 0
    
    def __init__(self):
        self.__nodes: list[dict[Stroke, int]] = [{}]
        self.__words: dict[int, str] = {}

    def get_dst_node_else_create(self, src_node: int, key: Stroke):
        transitions = self.__nodes[src_node]
        if key in transitions:
            return transitions[key]
        
        new_node_id = len(self.__nodes)
        transitions[key] = new_node_id
        self.__nodes.append({})

        return new_node_id

    def get_dst_node_else_create_chain(self, src_node: int, strokes: tuple[Stroke, ...]):
        current_node = src_node
        for stroke in strokes:
            current_node = self.get_dst_node_else_create(current_node, stroke)
        return current_node
    
    def get_dst_node(self, src_node: int, key: Stroke):
        return self.__nodes[src_node].get(key, None)
    
    def get_dst_node_chain(self, src_node: int, strokes: tuple[Stroke, ...]):
        current_node = src_node
        for stroke in strokes:
            current_node = self.get_dst_node(current_node, stroke)
            if current_node is None:
                return None
        return current_node
    
    def link(self, src_node: int, dst_node: int, key: Stroke):
        self.__nodes[src_node][key] = dst_node
    
    def link_chain(self, src_node: int, dst_node: int, strokes: tuple[Stroke, ...]):
        current_node = src_node
        for stroke in strokes[:-1]:
            current_node = self.get_dst_node_else_create(current_node, stroke)
        self.__nodes[current_node][strokes[-1]] = dst_node
    
    def set_translation(self, node: int, translation: str):
        self.__words[node] = translation
    
    def get_translation(self, node: int):
        return self.__words.get(node, None)
