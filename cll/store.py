import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from rich import print
from typer import Argument, Context
from typing_extensions import Annotated

from cll.tree import DummyTree, Tree

from typer_shell import make_typer_shell


@dataclass
class Store:
    """
    Indexs are stored in a vector db, which is a collection of documents

    This handles the vector db, plus exporting/importing to disk.
    """

    config: Optional["Config"] = None
    chat_path: Path = Path("~/.config/cll/chats/").expanduser()

    def __post_init__(self):
        if self.config and self.config._dict.get("chat_path", None):
            self.chat_path = Path(self.config._dict["chat_path"]).expanduser()
            self.chat_file = self.chat_path / f"{Path(self.config._dict['chat_name'])}.json"

    def dump(self):
        if self.chat_file.exists():
            return json.dumps(json.loads(self.chat_file.read_text()), indent=4)
        return json.dumps({})

    def list_files(self):
        if self.chat_path.exists():
            self._list_dir()

    def _list_dir(self):
        files = [x for x in self.chat_path.glob("*.json")]
        print(f"Found {len(files)} chats.")
        summaries = [json.loads(x.read_text()).get("summary", None) for x in files]
        for file, summary in zip(files, summaries):
            summary = summary or "No summary"
            print(f"{file.stem}: {summary:100}")

    def list_db_docs(self):
        if not self.db:
            return

        print(f"Found {len(self.db.documents)} documents.")
        for doc in self.db.documents:
            print(f"{doc['name']}: {doc['summary']}")

    def load_file(self):
        if self.config._dict["file"]:
            return Tree(self.chat_file)
        return DummyTree()


cli = make_typer_shell(prompt="💾: ", intro="Welcome to the Store! Type help or ? to list commands.")


@cli.command()
def file(
    ctx: Context,
    default_file: Annotated[Optional[str], Argument()] = None,
    toggle: bool = False,
    list: bool = False,
    dump: bool = False,
):
    """Manages the chat file. If you want to create an entirely new tree, do it here."""
    config = ctx.obj.config
    config.check_file(toggle, default_file, config)
    if list:
        Store(config=config).list_files()
    if dump:
        print(Store(config=config).dump())
