"""File for core data structures."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

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

    @property
    def prefix(self):
        return self.node_info.get("prefix", "")

    @prefix.setter
    def prefix(self, value):
        self.node_info["prefix"] = value

    def __str__(self):
        return self.prefix + self.text

    @property
    def checked_out(self):
        return self.node_info.get("checked_out", False)

    @checked_out.setter
    def checked_out(self, value):
        self.node_info["checked_out"] = value
