"""File for core data structures."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Union

from dataclasses_json import DataClassJsonMixin

from llama_index.schema import BaseDocument


@dataclass
class IndexStruct(BaseDocument, DataClassJsonMixin):
    """A base data struct for a LlamaIndex."""

    # NOTE: the text field, inherited from BaseDocument,
    # represents a summary of the content of the index struct.
    # primarily used for composing indices with other indices

    # NOTE: the doc_id field, inherited from BaseDocument,
    # represents a unique identifier for the index struct
    # that will be put in the docstore.
    # Not all index_structs need to have a doc_id. Only index_structs that
    # represent a complete data structure (e.g. IndexGraph, IndexList),
    # and are used to compose a higher level index, will have a doc_id.


@dataclass
class Node(IndexStruct):
    """A generic node of data.

    Base struct used in most indices.

    """

    def __post_init__(self) -> None:
        """Post init."""
        super().__post_init__()
        # NOTE: for Node objects, the text field is required
        if self.text is None:
            raise ValueError("text field not set.")

    # used for GPTTreeIndex
    index: int = 0
    child_indices: Set[int] = field(default_factory=set)

    # embeddings
    embedding: Optional[List[float]] = None

    # reference document id
    ref_doc_id: Optional[str] = None

    # extra node info
    node_info: Optional[Dict[str, Any]] = None

    # TODO: store reference instead of actual image
    # base64 encoded image str
    image: Optional[str] = None

    def get_text(self) -> str:
        """Get text."""
        text = super().get_text()
        result_text = (
            text if self.extra_info_str is None else f"{self.extra_info_str}\n\n{text}"
        )
        return result_text

    @classmethod
    def get_type(cls) -> str:
        """Get type."""
        # TODO: consolidate with IndexStructType
        return "node"


@dataclass
class IndexGraph(IndexStruct):
    """A graph representing the tree-structured index."""

    all_nodes: Dict[int, Node] = field(default_factory=dict)
    root_nodes: Dict[int, Node] = field(default_factory=dict)

    @property
    def size(self) -> int:
        """Get the size of the graph."""
        return len(self.all_nodes)

    def add_node(self, node: Node) -> None:
        """Add a node."""
        if node.index in self.all_nodes:
            raise ValueError(
                "Cannot add a new node with the same index as an existing node."
            )
        self.all_nodes[node.index] = node

    def add_root_node(self, node: Node) -> None:
        """Add a root node."""
        if node.index not in self.all_nodes:
            self.add_node(node)
        if node.index in self.root_nodes:
            raise ValueError(
                "Cannot add a new root node with the same index as an existing root node."
            )
        self.root_nodes[node.index] = node

    def get_children(self, parent_node: Optional[Node]) -> Dict[int, Node]:
        """Get nodes given indices."""
        if parent_node is None:
            return self.root_nodes
        else:
            return {i: self.all_nodes[i] for i in parent_node.child_indices}

    def get_all_children(self, parent_node: Optional[Node], all_children=None) -> Dict[int, Node]:
        """Get all children."""
        all_children = all_children or {}
        children = self.get_children(parent_node)
        for child_node in children.values():
            all_children[child_node.index] = child_node
            self.get_all_children(child_node, all_children)
        return all_children

    def get_parent(self, node: Node) -> Optional[Node]:
        """Get parent node."""
        for parent_node in self.all_nodes.values():
            if node.index in parent_node.child_indices:
                return parent_node
        return None

    def get_siblings(self, node: Node, include_self=False) -> Dict[int, Node]:
        """Get siblings."""
        parent_node = self.get_parent(node)
        if parent_node is None:
            children = self.root_nodes
        else:
            children = self.get_children(parent_node)
        if include_self:
            return children
        return {i: children[i] for i in children if i != node.index}

    def is_last_child(self, node: Node) -> Dict[int, Node]:
        """Get siblings."""
        siblings = self.get_siblings(node, include_self=True)
        if len(siblings) == 1:
            return True
        if node.index == max(siblings.keys()):
            return True
        return False

    def get_leaves(self, node: Node, leaves: Optional[Dict[int, Node]] = None) -> Dict[int, Node]:
        """Get leaves."""
        if leaves is None:
            leaves = {}
        if len(node.child_indices) == 0:
            leaves[node.index] = node
        else:
            for child_node in self.get_children(node).values():
                self.get_leaves(child_node, leaves)
        return leaves

    @property
    def branches(self) -> int:
        """Get the number of branches. This will equal the number of leaves."""
        total = 0
        for node in self.root_nodes.values():
            total += len(self.get_leaves(node))
        return total

    def insert_under_parent(self, node: Node, parent_node: Optional[Node]) -> None:
        """Insert under parent node."""
        if node.index in self.all_nodes:
            raise ValueError(
                "Cannot insert a new node with the same index as an existing node."
            )
        if parent_node is None:
            self.root_nodes[node.index] = node
        else:
            parent_node.child_indices.add(node.index)

        self.all_nodes[node.index] = node

    @classmethod
    def get_type(cls) -> str:
        """Get type."""
        return "tree"

    @property
    def last_node(self) -> int:
        """Get the last node index."""
        return self.all_nodes[max(self.all_nodes.keys())]

    def get_node(self, identifier: Union[int, str]) -> Optional[Node]:
        """Get node."""
        if isinstance(identifier, int):
            return self.all_nodes.get(identifier, None)
        if identifier.isdigit():
            return self.all_nodes.get(int(identifier), None)
        if isinstance(identifier, str):
            for node in self.all_nodes.values():
                if node.text == identifier:
                    return node
        return None

    def get_path_to_root(self, node: Node, path: Optional[List[Node]] = None) -> List[Node]:
        """Get path to root."""
        path = path.append(node) if path is not None else [node]
        parent_node = self.get_parent(node)
        if parent_node is None:
            return path
        return self.get_path_to_root(parent_node, path)

    def _get_graph(self) -> None:
        import networkx as nx

        g = nx.Graph()

        # add nodes
        for _, node in self.all_nodes.items():
            g.add_node(node.text)

        # add edges
        for _, node in self.all_nodes.items():
            children = self.get_children(node)
            for _, child in children.items():
                g.add_edge(child.text, node.text)

        return g

    def _get_viz(self) -> None:
        from pyvis.network import Network

        net = Network(cdn_resources="in_line", directed=True)
        net.from_nx(self._get_graph())
        net.show_buttons(filter_=['physics'])
        net.save_graph("test.html")

    def __repr__(self) -> str:
        """Get string representation, in the manner of a git log."""
        return self._get_repr(_str=self._legend())

    def get_full_repr(self, summaries=False) -> str:
        uber_root = Node(
            index=-1,
            text='(displaying all nodes)',
            child_indices=[i for i in self.root_nodes.keys()],
            node_info={}
        )
        _str = self._legend()
        _str += self._root_info()
        return self._get_repr(uber_root, _str, summaries=summaries)
