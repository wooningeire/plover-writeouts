from typing import Generic, Iterable, Optional, TypeVar, NamedTuple
from dataclasses import dataclass

from plover.steno import Stroke
import plover.log

from .config import LINKER_CHORD, TRIE_LINKER_KEY, TRIE_STROKE_BOUNDARY_KEY
from .util import can_add_stroke_on

S = TypeVar("S")
T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")

class Transition(NamedTuple):
    node_index: int
    key_id: int
    transition_index: int

class TransitionCostKey(NamedTuple):
    transition: Transition
    value_id: int

@dataclass(frozen=True)
class TransitionCostInfo(Generic[V]):
    cost: float
    value: V

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
        key_id = self.__keys.get(key)
        if key_id is None:
            return None
        
        return self.__nodes[src_node].get(key_id)
    
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
    
    def frozen(self):
        return ReadonlyTrie(self.__nodes, self.__translations, self.__keys)
    
    def __get_key_id(self, key: K):
        if key in self.__keys:
            return self.__keys[key]
        
        new_key_id = len(self.__keys)
        self.__keys[key] = new_key_id
        return new_key_id

    def __str__(self):
        lines: list[str] = []

        key_ids_to_keys = self.__key_ids_to_keys()

        for i, transitions in enumerate(self.__nodes):
            translation = self.__translations.get(i, None)
            lines.append(f"""{i}{f" : {translation}" if translation is not None else ""}""")
            for key_id, dst_node in transitions.items():
                lines.append(f"""\t{key_ids_to_keys[key_id]}\t ->\t {dst_node}""")

        return "\n".join(lines)
    
    def __key_ids_to_keys(self):
        return {
            key_id: key
            for key, key_id in self.__keys.items()
        }
    

class ReadonlyTrie(Generic[K, V]):
    ROOT = 0

    def __init__(self, nodes: list[dict[int, int]], translations: dict[int, V], keys: dict[K, int]):
        self.__nodes: dict[tuple[int, int], int] = {
            (src_node, key): dst_node
            for src_node, transitions in enumerate(nodes)
            for key, dst_node in transitions.items()
        }
        self.__translations: dict[int, V] = translations
        self.__keys: dict[K, int] = keys
    
    def get_dst_node(self, src_node: int, key: K):
        key_id = self.__keys.get(key)
        if key_id is None:
            return None
        
        return self.__nodes.get((src_node, key_id))
    
    def get_dst_node_chain(self, src_node: int, keys: tuple[K, ...]):
        current_node = src_node
        for stroke in keys:
            current_node = self.get_dst_node(current_node, stroke)
            if current_node is None:
                return None
        return current_node
    
    def get_translation(self, node: int):
        return self.__translations.get(node)


class NondeterministicTrie(Generic[K, V]):
    """A trie that can be in multiple states at once."""

    ROOT = 0
    
    def __init__(self):
        self.__nodes: list[dict[int, list[int]]] = [{}]
        self.__translations: dict[int, list[int]] = {}
        self.__keys: dict[K, int] = {}
        self.__values: dict[V, int] = {}
        self.__values_list: list[V] = []
        self.__transition_costs: dict[TransitionCostKey, float] = {}

    def get_first_dst_node_else_create(self, src_node: int, key: K, cost_info: TransitionCostInfo[V]) -> int:
        key_id = self.__get_key_id_else_create(key)

        self.__assign_cost(src_node, key_id, 0, cost_info)

        transitions = self.__nodes[src_node]
        if key_id in transitions:
            return transitions[key_id][0]
        
        new_node_id = self.__create_new_node()
        transitions[key_id] = [new_node_id]
        return new_node_id
    

    def get_first_dst_node_else_create_chain(self, src_node: int, keys: tuple[K, ...], cost_info: TransitionCostInfo[V]) -> int:
        current_node = src_node
        for i, key in enumerate(keys):
            if i == len(keys) - 1:
                current_node = self.get_first_dst_node_else_create(current_node, key, cost_info)
            else:
                current_node = self.get_first_dst_node_else_create(current_node, key, TransitionCostInfo(0, cost_info.value))
        return current_node

    def get_dst_nodes(self, src_nodes: dict[int, tuple[Transition, ...]], key: K):
        key_id = self.__keys.get(key)
        if key_id is None:
            return {}
        
        # TODO if multiple paths are found to a destination node, this does not store all paths and so minimum-cost paths might be overwritten
        return {
            dst_node: node_transitions + (Transition(src_node, key_id, transition_index),)
            for src_node, node_transitions in src_nodes.items()
            for transition_index, dst_node in enumerate(self.__nodes[src_node].get(key_id, []))
        }
    
    def get_dst_nodes_chain(self, src_nodes: dict[int, tuple[Transition, ...]], keys: tuple[K, ...]):
        current_nodes = src_nodes
        for key in keys:
            current_nodes = self.get_dst_nodes(current_nodes, key)
            if len(current_nodes) == 0:
                return current_nodes
        return current_nodes
    
    def link(self, src_node: int, dst_node: int, key: K, cost_info: TransitionCostInfo[V]):
        key_id = self.__get_key_id_else_create(key)
        
        if key_id in self.__nodes[src_node]: # and dst_node not in self.__nodes[src_node][key]
            new_transition_index = len(self.__nodes[src_node][key_id])
            self.__nodes[src_node][key_id].append(dst_node)
        else:
            new_transition_index = 0
            self.__nodes[src_node][key_id] = [dst_node]

        self.__assign_cost(src_node, key_id, new_transition_index, cost_info)

    
    def link_chain(self, src_node: int, dst_node: int, keys: tuple[K, ...], cost_info: TransitionCostInfo[V]):
        current_node = src_node
        for key in keys[:-1]:
            current_node = self.get_first_dst_node_else_create(current_node, key, TransitionCostInfo(0, cost_info.value))

        self.link(current_node, dst_node, keys[-1], cost_info)
    
    def set_translation(self, node: int, translation: V):
        translation_id = self.__get_value_id_else_create(translation)

        if node in self.__translations:
            self.__translations[node].append(translation_id)
        else:
            self.__translations[node] = [translation_id]
        
    
    def get_translations_and_costs_single(self, node: int, transitions: Iterable[Transition]) -> tuple[tuple[V, float], ...]:
        if node not in self.__translations:
            return ()
        
        translation_cost_pairs: list[tuple[V, float]] = []

        for translation_id in self.__translations[node]:
            cumsum_cost = 0
            for transition in transitions:
                key = TransitionCostKey(transition, translation_id)
                if key not in self.__transition_costs:
                    continue
                
                cumsum_cost += self.__transition_costs[key]

            translation_cost_pairs.append((self.__values_list[translation_id], cumsum_cost))

        return tuple(translation_cost_pairs)


    def get_translations_and_costs(self, nodes: dict[int, tuple[Transition, ...]]):
        results: dict[V, tuple[float, tuple[Transition, ...]]] = {}
        for node, transitions in nodes.items():
            for translation, cost in self.get_translations_and_costs_single(node, transitions):
                if cost >= results.get(translation, (float("inf"), -1))[0]: continue
                results[translation] = (cost, transitions)
        return results
    
    def transition_has_key(self, transition: Transition, key: K):
        return self.__keys[key] == transition.key_id
    
    def __str__(self):
        lines: list[str] = []

        key_ids_to_keys = self.__key_ids_to_keys()

        transition_costs: dict[Transition, dict[int, float]] = {}
        for (transition, value_id), cost in self.__transition_costs.items():
            if transition in transition_costs:
                transition_costs[transition][value_id] = cost
                continue

            transition_costs[transition] = {value_id: cost}

        for i, transitions in enumerate(self.__nodes):
            value_ids = self.__translations.get(i)
            lines.append(f"""{i}{f" : {tuple(self.__values_list[value_id] for value_id in value_ids)}" if value_ids is not None else ""}""")
            for key_id, dst_nodes in transitions.items():
                lines.append(f"""\t{key_ids_to_keys[key_id]}\t ->\t {",".join(str(node) for node in dst_nodes)}""")
                for j, dst_node in enumerate(dst_nodes):
                    if Transition(i, key_id, j) not in transition_costs: continue
                    lines.append(f"""\t\t{dst_node}:""")
                    for value_id, cost in transition_costs[Transition(i, key_id, j)].items():
                        lines.append(f"""\t\t\t{self.__values_list[value_id]}:\t {cost}""")

        return "\n".join(lines)
    
#     def optimized(self: "NondeterministicTrie[str, str]"):
#         new_trie: NondeterministicTrie[str, str] = NondeterministicTrie()
#         self.__transfer_node_and_descendants_if_necessary(new_trie, self.ROOT, {0: 0}, Stroke.from_keys(()), set(), {0}, self.__key_ids_to_keys())
# #         plover.log.debug(f"""

# # Optimized lookup trie.
# # \t{self.profile()}
# # \t\t->
# # \t{new_trie.profile()}
# # """)
#         return new_trie
    

    def profile(self):
        from pympler.asizeof import asizeof
        n_transitions = sum(sum(len(dst_nodes) for dst_nodes in transitions.values()) for transitions in self.__nodes)
        return f"{len(self.__nodes):,} nodes, {n_transitions:,} transitions, {len(self.__translations):,} translations ({asizeof(self):,} bytes)"
    
    # def frozen(self):
    #     return ReadonlyNondeterministicTrie(self.__nodes, self.__translations, self.__keys)
    
    def __get_key_id_else_create(self, key: K):
        if key in self.__keys:
            return self.__keys[key]
        
        new_key_id = len(self.__keys)
        self.__keys[key] = new_key_id
        return new_key_id
    
    def __get_value_id_else_create(self, value: V):
        if value in self.__values:
            return self.__values[value]
        
        new_value_id = len(self.__values)
        self.__values[value] = new_value_id
        self.__values_list.append(value)
        return new_value_id

    def __create_new_node(self):
        new_node_id = len(self.__nodes)
        self.__nodes.append({})
        return new_node_id
    
    def __assign_cost(self, src_node: int, key_id: int, new_transition_index: int, cost_info: Optional[TransitionCostInfo[V]]):
        if cost_info is None: return
        cost_key = TransitionCostKey(Transition(src_node, key_id, new_transition_index), self.__get_value_id_else_create(cost_info.value))
        self.__transition_costs[cost_key] = min(cost_info.cost, self.__transition_costs.get(cost_key, float("inf")))

    # def __transfer_node_and_descendants_if_necessary(
    #     self: "NondeterministicTrie[str, str]",
    #     new_trie: "NondeterministicTrie[str, str]",
    #     orig_node_id: int,
    #     new_node_mapping: dict[int, int],
    #     current_stroke: Stroke,
    #     visited_nodes: set[int],
    #     translated_nodes: set[int],
    #     key_ids_to_keys: dict[int, str],
    # ) -> bool:
    #     if orig_node_id in visited_nodes:
    #         return orig_node_id in new_node_mapping
    #     visited_nodes.add(orig_node_id)


    #     new_node_id: Optional[int] = new_node_mapping.get(orig_node_id)
    #     if orig_node_id not in translated_nodes:
    #         translated_nodes.add(orig_node_id)

    #         translation = self.get_translation_single(orig_node_id)
    #         if translation is not None:
    #             new_node_id = new_trie.__create_new_node()
    #             new_trie.set_translation(new_node_id, translation)
    #             new_node_mapping[orig_node_id] = new_node_id

    #     for key_id, dst_nodes in self.__nodes[orig_node_id].items():
    #         if key_id == self.__keys[TRIE_STROKE_BOUNDARY_KEY]:
    #             new_stroke = Stroke.from_keys(())
    #         elif key_id == self.__keys[TRIE_LINKER_KEY]:
    #             new_stroke = LINKER_CHORD
    #         else:
    #             new_key_stroke = Stroke.from_steno(key_ids_to_keys[key_id])
    #             if not can_add_stroke_on(current_stroke, new_key_stroke):
    #                 # The new stroke would violate steno order if it continued off the current stroke
    #                 continue

    #             new_stroke = current_stroke + new_key_stroke

    #         for dst_node in set(dst_nodes):
    #             if not self.__transfer_node_and_descendants_if_necessary(new_trie, dst_node, new_node_mapping, new_stroke, visited_nodes, translated_nodes, key_ids_to_keys): continue
                
    #             if new_node_id is None:
    #                 new_node_id = new_trie.__create_new_node()
    #                 new_node_mapping[orig_node_id] = new_node_id
    #             new_trie.link(new_node_id, new_node_mapping[dst_node], key_ids_to_keys[key_id])

    #     return new_node_id is not None

    def __key_ids_to_keys(self):
        return {
            key_id: key
            for key, key_id in self.__keys.items()
        }
    

# class ReadonlyNondeterministicTrie(Generic[K, V]):
#     """A readonly variant of `NondeterministicTrie` that reduces memory usage"""

#     ROOT = 0

#     def __init__(self, nodes: list[dict[int, list[int]]], translations: dict[int, V], keys: dict[K, int]):
#         self.__nodes: dict[tuple[int, int], tuple[int, ...]] = {
#             (src_node, key): tuple(dst_nodes)
#             for src_node, transitions in enumerate(nodes)
#             for key, dst_nodes in transitions.items()
#         }
#         self.__translations: dict[int, V] = translations
#         self.__keys: dict[K, int] = keys

#     def get_dst_nodes(self, src_nodes: set[int], key: K):
#         key_id = self.__keys.get(key)
#         if key_id is None:
#             return set()
        
#         return set(
#             node
#             for src_node in src_nodes
#             for node in self.__nodes.get((src_node, key_id), ())
#         )
    
#     def get_dst_nodes_chain(self, src_nodes: set[int], keys: tuple[K, ...]):
#         current_nodes = src_nodes
#         for key in keys:
#             current_nodes = self.get_dst_nodes(current_nodes, key)
#             if len(current_nodes) == 0:
#                 return current_nodes
#         return current_nodes
    
#     def get_translation(self, nodes: set[int]):
#         for node in nodes:
#             translation = self.__translations.get(node)
#             if translation is not None:
#                 return translation
#         return None

#     def profile(self):
#         from pympler.asizeof import asizeof
#         n_nodes = max(transition[0] for transition in self.__nodes.keys())
#         n_transitions = sum(len(dst_nodes) for dst_nodes in self.__nodes.values())
#         return f"{n_nodes:,} nodes, {n_transitions:,} transitions, {len(self.__translations):,} translations ({asizeof(self):,} bytes)"