import subprocess
import datetime
import json
from typing import Any, Dict, Optional, Sequence, List, Union
from pathlib import Path

from .data_structs import IndexGraph, Node
from llama_index.schema import BaseDocument


class LoomIndex:
    """Multiverse Index.

    The multiverse index is a tree-structured index, which starts with a single
    root node and branches into multiple nodes. During construction, the tree
    is built one node at a time similar to a list index.

    There are a few different query types (see :ref:`Ref-Query`).
    The main option is to traverse down the tree, summarizing the different branches.
    This can be used to summarize discourse in forums, twitter and other
    online media that are structured as a tree.
    """

    index_struct_cls = IndexGraph
    tags: Dict[str, Node] = {}
    summary: Optional[str] = None
    name: Optional[str] = None
    cache_size: int = 4
    latest_summary: str = "None."

    def __init__(self, name=None, _index_struct=None):
        self._index_struct = _index_struct or self.index_struct_cls()
        self.name = name

    @property
    def index_struct(self):
        """Get the index struct."""
        return self._index_struct

    def _create_node(
        self,
        text: str,
    ) -> Node:
        return Node(
            text=text,
            index=len(self._index_struct.all_nodes),
            node_info={},
        )

    def _build_index_from_nodes(
        self, nodes: Sequence[Node]
    ) -> IndexGraph:
        """Build the index from documents.

        Args:
            documents (List[BaseDocument]): A list of documents.

        Returns:
            IndexGraph: The created graph index.
        """
        index_struct = IndexGraph()
        start_index = 0
        for i, d in enumerate(nodes):
            node = self._get_nodes_from_document(d, start_index + i)
            index_struct.add_root_node(node)
        return index_struct

    def _update_index_registry_and_docstore(self) -> None:
        """Update index registry and docstore."""
        super()._update_index_registry_and_docstore()
        if len(self._index_struct.root_nodes) == 1 and len(self._index_struct.all_nodes) == 1:
            self.checkout_path(self._index_struct.root_nodes[0])
        self.tags = {}

    def checkout_path(self, node: Node) -> None:
        """Checkout a path in the index.
        The tree is traversed from the chosen node to the root node,
        and every node is labelled as "checked_out".

        Args:
            node (Node): The node to checkout.

        Returns:
            None
        """
        self.clear_checkout()
        node.node_info["checked_out"] = True
        while node.index not in self.index_struct.root_nodes.keys():
            node = self.index_struct.get_parent(node)
            if node is None:
                raise ValueError("Node has no parent and is not a root node. Graph is corrupt.")
            node.node_info["checked_out"] = True

    def checkout(self, identifier: Union[int, str]) -> None:
        """Checkout a node in the index."""
        if identifier in self.tags.keys():
            node = self.index_struct.all_nodes[self.tags[identifier]]
        else:
            node = self.index_struct.get_node(identifier)
        # TODO: do an vector search if node is None

        if node is None:
            return
        self.checkout_path(node)

    def cherry_pick(self, identifiers: List[Union[int, str]]) -> None:
        """Cherry pick a list of nodes in the index."""
        nodes = []
        for identifier in identifiers:
            if identifier in self.tags.keys():
                node = self.index_struct.all_nodes[self.tags[identifier]]
            else:
                node = self.index_struct.get_node(identifier)
            nodes.append(node)
        for node in nodes:
            self.extend(node)

    def delete(self, identifiers: List[Union[int, str]]) -> None:
        """Delete a list of nodes in the index."""
        if not isinstance(identifiers, list):
            identifiers = [identifiers]
        nodes = []
        for identifier in identifiers:
            if identifier in self.tags.keys():
                node = self.index_struct.all_nodes[self.tags[identifier]]
            else:
                node = self.index_struct.get_node(identifier)
            nodes.append(node)
        for node in nodes:
            del self.index_struct.all_nodes[node.index]
            if node.index in self.index_struct._root_nodes:
                self.index_struct._root_nodes.remove(node.index)

    def clear_checkout(self) -> None:
        """Clear checkout."""
        for node in self.index_struct.all_nodes.values():
            node.node_info.pop("checked_out", None)
        for node in self.index_struct.root_nodes.values():
            node.node_info.pop("checked_out", None)

    def repr(self, node):
        if isinstance(node, int):
            node = self.index_struct.all_nodes[node]
        return self.index_struct._get_repr(node)

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        self.path_formatted

    @property
    def path_formatted(self) -> List[Node]:
        return self.index_struct.path_formatted

    @property
    def path_str(self) -> List[Node]:
        return self.index_struct.path_str

    @property
    def path(self) -> List[Node]:
        return self.index_struct.path

    def step(self, direction: str) -> None:
        """
        Move up or down the tree.

        When moving down, the first child node is selected.
        """
        if direction in ["w", "up", "k"]:
            direction = "up"
        elif direction in ["s", "down", "j"]:
            direction = "down"
        elif direction in ["a", "left", "h"]:
            direction = "smaller_sibling"
        elif direction in ["d", "right", "l"]:
            direction = "larger_sibling"

        if direction == "up":
            parent = self.index_struct.get_parent(self.path[-1])
            if not parent:
                return
            self.checkout_path(parent)
        elif direction == "down":
            children = self.index_struct.get_children(self.path[-1])
            if not children:
                return
            self.checkout_path(children[min(children.keys())])
        elif direction in ["smaller_sibling", "larger_sibling"]:
            siblings = self.index_struct.get_siblings(self.path[-1], include_self=True)
            self._step_sibling(direction, siblings)

    def _step_sibling(self, direction: str, siblings: Dict[int, Node]) -> None:
        """
        Step to directional sibling, but loop around if at end.
        """
        sib_indexes = sorted(siblings.keys())
        if direction == "smaller_sibling":
            sib_indexes = list(reversed(sib_indexes))

        # If the current node is the lowest or highest index, then we need to
        # loop around to the other end of the list.
        current_index = self.path[-1].index
        position_in_siblings = sib_indexes.index(current_index)
        if position_in_siblings == len(sib_indexes) - 1:
            self.checkout_path(siblings[sib_indexes[0]])
        else:
            self.checkout_path(siblings[sib_indexes[position_in_siblings + 1]])

    def tag(self, tag: str) -> None:
        """Tag the current path."""
        self.tags[tag] = self.path[-1].index

    def _insert(self, node: Union[Node, str], **_: Any) -> None:
        """Insert a document."""
        if isinstance(node, str):
            node = self._create_node(text=node)
        if len(self.path):
            current_node = self.path[-1]
            self.index_struct.insert_under_parent(node, current_node)
        else:
            self.index_struct.add_root_node(node)

    def extend(self, document: Union[str, Node]) -> None:
        self._insert(document)
        self.checkout_path(self.index_struct.last_node)

    def new(self, document: BaseDocument) -> None:
        """Create a new branch."""
        self.clear_checkout()
        self._insert(document)
        self.checkout_path(self.index_struct.last_node)

    @classmethod
    def load_from_disk(cls, save_path: str, **kwargs: Any) -> "LoomIndex":
        with open(save_path, "r") as f:
            file_contents = f.read()
            return cls.load_from_string(file_contents, **kwargs)

    @classmethod
    def load_from_string(cls, index_string: str, **kwargs: Any) -> "LoomIndex":
        result_dict = json.loads(index_string)
        return cls.load_from_dict(result_dict, **kwargs)

    @classmethod
    def load_from_dict(
        cls, result_dict: Dict[str, Any], **kwargs: Any
    ) -> "LoomIndex":
        """Load index from dictionary."""
        index_struct = cls.index_struct_cls.from_json(result_dict["index_struct"])
        index = cls(_index_struct=index_struct, **kwargs)
        if "tags" in result_dict:
            index.tags = result_dict["tags"]
        if "name" in result_dict:
            index.name = result_dict["name"]
        return index

    def save_to_disk(
        self, save_path: str, encoding: str = "ascii", **save_kwargs: Any
    ) -> None:
        index_string = self.save_to_string(**save_kwargs)
        with open(save_path, "wt", encoding=encoding) as f:
            f.write(index_string)

    def save_to_string(self, **save_kwargs: Any) -> str:
        out_dict = self.save_to_dict(**save_kwargs)
        return json.dumps(out_dict, **save_kwargs)

    def save_to_dict(self, **save_kwargs: Any) -> dict:
        """Save index to dictionary."""
        result_dict: Dict[str, Any] = {
            "index_struct": self.index_struct.to_json()
        }
        result_dict["tags"] = self.tags
        result_dict["name"] = self.name
        return result_dict
