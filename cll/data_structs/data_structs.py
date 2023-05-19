"""File for core data structures."""

import shutil

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Tuple

import networkx as nx
from rich.tree import Tree as RichTree
from rich.panel import Panel
from rich import print

from .node import Node, IndexStruct


@dataclass
class IndexGraph(IndexStruct):
    """A graph representing the tree-structured index."""

    all_nodes: Dict[int, Node] = field(default_factory=dict)
    _root_nodes: List[int] = field(default_factory=list)
    path_neighborhood: int = 3
    head_neighborhood: int = 10

    @property
    def root_nodes(self) -> Dict[int, Node]:
        return {key: self.all_nodes[key] for key in self._root_nodes}

    @property
    def active_root(self) -> Dict[int, Node]:
        return [key for key, value in self.root_nodes.items() if value.checked_out][0]

    @property
    def active_tree(self) -> Dict[int, Node]:
        root = self.all_nodes[self.active_root]
        active_nodes = self.get_all_children(root)
        active_nodes.update({self.active_root: root})
        return active_nodes

    @property
    def size(self) -> int:
        """Get the size of the graph."""
        return len(self.all_nodes)

    @property
    def branches(self) -> int:
        """Get the number of branches. This will equal the number of leaves."""
        total = 0
        for node in self.root_nodes.values():
            total += len(self.get_leaves(node))
        return total

    @classmethod
    def get_type(cls) -> str:
        """Get type."""
        return "tree"

    @property
    def last_node(self) -> int:
        """Get the last node index."""
        return self.all_nodes[max(self.all_nodes.keys())]

    @property
    def path(self) -> List[Node]:
        return self.path_nodes

    @property
    def path_nodes(self) -> List[Node]:
        for node in self.root_nodes.values():
            if node.checked_out:
                return self._get_checked_out_path({node.index: node}, [])
        return []

    @property
    def path_formatted(self) -> List[Node]:
        """Path with prompts."""
        return "".join([str(node) for node in self.path])

    @property
    def path_str(self) -> List[Node]:
        """Path purely as str."""
        return "".join([node.text for node in self.path])

    @property
    def path_indices(self) -> List[int]:
        return [node.index for node in self.path]

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
        self._root_nodes.append(node.index)

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

    def _get_checked_out_path(self, nodes: List[Node], path: List[Node]) -> List[Node]:
        """Get path from root to leaf via checked out nodes."""
        for node in nodes.values():
            if node.node_info.get('checked_out', False):
                path.append(node)
                return self._get_checked_out_path(self.get_children(node), path)
        return path

    def insert_under_parent(self, node: Node, parent_node: Optional[Node]) -> None:
        """Insert under parent node."""
        if node.index in self.all_nodes:
            node.index = len(self.all_nodes)
        if parent_node is None:
            self.root_nodes.append(node.index)
        else:
            parent_node.child_indices.add(node.index)

        self.all_nodes[node.index] = node

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
        """Get path to root of the tree."""
        path = path.append(node) if path is not None else [node]
        parent_node = self.get_parent(node)
        if parent_node is None:
            return path
        return self.get_path_to_root(parent_node, path)

    def _get_graph(self) -> None:
        g = nx.Graph()

        # add nodes
        for node in self.active_tree.values():
            g.add_node(node.index)

        # add edges
        for node in self.active_tree.values():
            children = self.get_children(node)
            for _, child in children.items():
                g.add_edge(child.index, node.index)

        self.graph = g
        return self.graph

    def _get_distances(self) -> None:
        self._get_graph()
        self.distances = {}
        for u in self.graph.nodes:
            for v in self.graph.nodes:
                self.distances[tuple({u, v})] = nx.shortest_path_length(self.graph, u, v)

    def get_distance_from_path(self, query_index) -> int:
        distance = float('inf')
        for index in self.path_indices:
            distance = min(distance, self.distances[tuple({index, query_index})])
        return distance

    def close_node(self, query_index, head_index) -> Tuple[int, bool]:
        # Close to path?
        distance = self.get_distance_from_path(query_index)
        if distance < self.path_neighborhood:
            return distance, True

        # Close to head?
        distance = self.distances[tuple({query_index, head_index})]
        if distance < self.head_neighborhood:
            return distance, True

        return distance, False

    def _get_viz(self) -> None:
        from pyvis.network import Network

        net = Network(cdn_resources="in_line", directed=True)
        net.from_nx(self._get_graph())
        net.show_buttons(filter_=['physics'])
        net.save_graph("test.html")

    # Print Representation
    def _root_info(self) -> str:
        _str = "\n# Root Node Index (branches:total_nodes)) #\n"
        for root in self.root_nodes.values():
            leaves = self.get_leaves(root)
            children = self.get_all_children(root)
            _str += f"{root.index}; ({len(leaves)}:{len(children)}):\t\t{root.text.splitlines()[0]}"
            if self.all_nodes[root.index].node_info.get("checked_out", False):
                _str += "\t\t<-- CURRENT_ROOT"
        print(Panel(_str, title="Root Nodes"))

    def legend(self) -> str:
        txt = (
            "checked out nodes are in [bold red]bold red[/bold red]\n"
            "other nodes are in [dim blue]dim blue[/dim blue]\n"
            "navigate with [magenta]hjkl[/magenta]\n"
            "show the current prompt with [magenta]p[/magenta]\n"
            "show the tree with [magenta]t[/magenta]\n"
            "(this will be the checked out path plus template)"
        )
        print(Panel.fit(txt, title="Legend", border_style="bold magenta"))

    def get_full_repr(self, summaries=False) -> str:
        uber_root = Node(
            index=-1,
            text="(displaying all nodes)",
            child_indices=self._root_nodes,
            node_info={"checked_out": True},
        )
        self.legend()
        self._root_info()
        return self._get_repr(uber_root)

    def _get_repr(self, node: Optional[Node] = None) -> str:
        if node is None:
            if self.path_indices:
                node = self.all_nodes[self.path_indices[0]]
            elif len(self.all_nodes):
                node = self.all_nodes[min(self.all_nodes.keys())]
            else:
                return
        tree = RichTree(self._text(node), style="bold red", guide_style="bold magenta")
        self._get_distances()
        return self._get_repr_recursive(node, tree)

    def _get_repr_recursive(self, node: Optional[Node] = None, tree: Optional[RichTree] = None) -> str:
        nodes = self.get_children(node)
        for child_node in nodes.values():
            distance, close = self.close_node(child_node.index, self.path_indices[-1])
            style = "dim blue" if distance else "bold red"
            if not close:
                subtree = tree.add("...", style=style)
                continue
            subtree = tree.add(self._text(child_node), style=style)
            self._get_repr_recursive(child_node, subtree)
        return tree

    def _text(self, node: Node) -> str:
        text_width = shutil.get_terminal_size().columns - 30
        text = node.text.replace("\n", " ")
        text = f"{node.index}: {text}"
        if len(text) > text_width:
            text = text[:text_width] + " ..."
        return text
