import binascii
from copy import deepcopy
from dataclasses import dataclass
from typing import List, Optional

import iterfzf
import click
from cll.data_structs import LoomIndex
from rich import print
from rich.console import Console
from rich.panel import Panel
from typer import Argument, Context
from typing_extensions import Annotated

from typer_shell import get_params, _update, save as save_config, print as print_config, get_params_path
from .encoder import Encoder


@dataclass
class Tree:
    file: Optional[str] = None
    index: Optional[LoomIndex] = None
    params: Optional[dict] = None
    name: Optional[str] = None
    encoder: Encoder = Encoder(Encoder.none)
    decoder: Encoder = Encoder(Encoder.none)

    def __post_init__(self):
        if self.file and self.file.exists():
            self.index = LoomIndex.load_from_disk(str(self.file))
            return

        self.file.parent.mkdir(parents=True, exist_ok=True)
        self.index = LoomIndex()

    @staticmethod
    def list_files(path):
        if path.exists():
            Tree._list_dir(path)

    @staticmethod
    def _list_dir(path):
        files = [x for x in path.glob("*.json")]
        print(f"Found {len(files)} chats.")
        for file in files:
            print(f"{file.stem}")

    @property
    def prompt_context(self):
        path = self.index.path_formatted
        prompt = self.index.context + "\n" + path
        return prompt

    @property
    def prompt(self):
        if self.encoder.callback == Encoder.none:
            return self.index.path_formatted
        return self._prompt

    @property
    def _prompt(self):
        prompt = ""
        for node in self.index.index_struct.path_nodes:
            prompt += node.prefix
            prompt += self.encoder(node.text)
        return prompt

    def input(self, node):
        self.extend(node, save=True)

    def output(self, node):
        self.extend(node, save=True)

    def extend(self, response, save=False):
        self.index.extend(response)
        if save:
            self.save()

    def insert(self, response, save=False):
        self.index._insert(response)
        if save:
            self.save()

    def save(self):
        self.index.save_to_disk(self.file)

    def __len__(self):
        return len(self.index.index_struct.all_nodes)


def path_with_current(ctx):
    if not getattr(ctx.obj.tree, "index", None):
        return
    index = ctx.obj.tree.index
    Console().clear()

    params = get_params(ctx)
    if params:
        index.index_struct.path_neighborhood = params["path_neighborhood"]
        index.index_struct.head_neighborhood = params["head_neighborhood"]

    index.index_struct.legend()
    print(index.index_struct._get_repr())
    path = index.index_struct.path
    if not len(path):
        return
    path_str = ""
    if len(path) > 1:
        path_str += "".join([str(node) for node in path[:-1]])
    path_str += "[bold red]"
    path_str += str(path[-1])
    path_str += "[/bold red]"
    print(Panel.fit(path_str, title="Prompt (unencoded, without template)", border_style="bold magenta"))


def set_encoder(ctx, string=None):
    params = get_params(ctx)
    params_path = get_params_path(ctx)
    file_path = params_path.parent / "chats" / f"{params['chat_name']}.json"
    ctx.obj.tree = Tree(file_path)
    if not string and params:
        string = params.get("encoder", "none")
    if not string:
        string = "none"
    ctx.obj.tree.encoder = Encoder.get_encoder(string)
    ctx.obj.tree.decoder = Encoder.get_decoder(string)

    if Encoder._get_encoder(string) == Encoder.none:
        string = "none"
    if params:
        params["encoder"] = string
    print(params)
    path_with_current(ctx)


def list_chats(
    ctx: Context,
    list: bool = False,
    dump: bool = False,
):
    """List available chat files."""
    config = ctx.obj.config
    if list:
        Tree(config=config).list_files()
    if dump:
        print(Tree(config=config).dump())


def default(ctx: Context, line: str):
    """Default command"""
    if len(line) < 20:
        print("Ill assume you didn't mean to send that. If you do, use 'send X'. (Below 20 chars.)")
        return
    ctx.invoke(send, ctx=ctx, msg=line.split(" "))


def h(ctx: Context, count: int = 1):
    "Move to left sibling"
    for _ in range(count):
        ctx.obj.tree.index.step("up")
    path_with_current(ctx)


def j(ctx: Context, count: int = 1):
    "Move to parent"
    for _ in range(count):
        ctx.obj.tree.index.step("right")
    path_with_current(ctx)


def k(ctx: Context, count: int = 1):
    "Move to child"
    for _ in range(count):
        ctx.obj.tree.index.step("left")
    path_with_current(ctx)


def left(ctx: Context, count: int = 1):
    "Move to left sibling"
    for _ in range(count):
        ctx.obj.tree.index.step("down")
    path_with_current(ctx)


def navigate(ctx: Context, direction: str, count: int = 1):
    'Navigate with "hjkl" or "wasd".'
    "You don't need to pass them to this function."
    "View may be rotated 90 degrees."
    for _ in range(count):
        ctx.obj.tree.index.step(direction)
    path_with_current(ctx)


def neighborhood(ctx: Context):
    "The tree view is truncated for nodes that are far from the current path.\n"
    "This command changes the size of the neighborhood.\n"
    "There are two params: the path neighborhood and the head neighborhood.\n"
    "The path neighborhood is the maximum distance a node can be from the current path.\n"
    "The head neighborhood is the maximum distance a node can be from the head of the tree.\n"
    params = get_params(ctx)
    for key, value in params.items():
        if key not in ["path_neighborhood", "head_neighborhood"]:
            continue
        value = input(f"{key} [{value}]: ")
        if not value:
            continue
        _update(key, value, params)
    save_config(ctx)
    path_with_current(ctx)
    print(params)


def encoder(
        ctx: Context,
        encoder: Annotated[Optional[str], Argument()] = None
):
    '(en) Set the encoder to use. Text will be encoded and decoded before being sent.\n'
    'Available encoders:\n'
    '\t"none": no encoding\n'
    '\t"base64": base64 encoding\n'
    '\t"rot13": rot13 encoding\n'
    '\t"caesar X": caesar encoding, rot by X (rot13 == "ceaser 13")\n'
    if not encoder:
        click.echo(
            "Ender a choice. I will tell you what I parse it as. "
            "If you are happy, hit enter. "
            "Lambdas are probably ceaser cypers correctly interpreted."
        )
        current_encoder = ctx.obj.tree.encoder.callback
        last_encoder = "none"
        while True:
            new_encoder_name = current_encoder.__name__
            new_encoder = input(f"encoder [{new_encoder_name}]: ")
            if not new_encoder:
                encoder = last_encoder
                break
            current_encoder = Encoder._get_encoder(new_encoder)
            last_encoder = new_encoder

    set_encoder(ctx, encoder)
    save_config(ctx)
    print_config(ctx)


def reencode(ctx: Context, index: Annotated[Optional[str], Argument()] = None):
    "(re) Reencode the current node."
    if not index:
        index = ctx.obj.tree.index.path[-1].index
    index = int(index)

    node = ctx.obj.tree.index.index_struct.all_nodes[index]
    node.text = ctx.obj.tree.encoder(node.text)
    ctx.obj.tree.index.index_struct.all_nodes[index] = node
    ctx.obj.tree.save()
    path_with_current(ctx)


def redecode(ctx: Context, index: Annotated[Optional[str], Argument()] = None):
    "(de) Reencode the current node backwards."
    if not index:
        index = ctx.obj.tree.index.path[-1].index
    index = int(index)

    node = ctx.obj.tree.index.index_struct.all_nodes[index]
    node.text = ctx.obj.tree.decoder(node.text)
    ctx.obj.tree.index.index_struct.all_nodes[index] = node
    ctx.obj.tree.save()
    path_with_current(ctx)


def display(
    ctx: Context,
    type: Annotated[Optional[str], Argument()] = "t",
    index: Annotated[Optional[str], Argument()] = None,
):
    """(d, p, t) Various display options (check 'help display').\n
    Types:\n
        \ttree/t: display the tree structure\n
        \tall/a: display the full tree including other roots\n
        \tpath/p: display the path to the current node\n
        \tprompt/pr: display the current prompt\n
        \ttemplated/tr: display the current prompt with templated values\n
        \tsummary/s: display the current context and latest summary\n
        \tnode/n: display the specific node(s) (pass the index of the node(s))
    """
    Console().clear()
    if type in ["t", "tree"]:
        ctx.obj.tree.index.index_struct.legend()
        print(ctx.obj.tree.index.index_struct._get_repr())

    if type in ["a", "all"]:
        print(ctx.obj.tree.index.index_struct.get_full_repr())
        return

    if type in ["c", "context"]:
        print(ctx.obj.tree.index.context)
        return

    if type in ["p", "path"]:
        print(ctx.obj.tree.index.path)
        return

    if type in ["pr", "prompt"]:
        print(Panel.fit(ctx.obj.tree.prompt, title="Prompt", border_style="bold magenta"))
        return

    if type in ["tr", "templated"]:
        prompt = ctx.obj.tree.prompt
        prompt = ctx.obj.templater.prompt(ctx, prompt)
        print(prompt)
        return

    if type in ["n", "node"]:
        if index is None:
            print("Please provide an index")
            return

        for index in parse_indexes(index):
            if isinstance(index, int):
                print(index)
                print(ctx.obj.tree.index.index_struct.all_nodes[int(index)].text)
                continue


def display_tree(ctx: Context):
    """(t) Display the tree."""
    display(ctx, "t")


def display_all(ctx: Context):
    """(t) Display the tree."""
    display(ctx, "a")


def _append(ctx, msg):
    if isinstance(msg, tuple) or isinstance(msg, list):
        msg = " ".join(msg)
    node = ctx.obj.tree.index._create_node(msg)
    node = ctx.obj.templater.in_(ctx, node)
    ctx.obj.tree.input(node)


def send(
    ctx: Context,
    msg: Annotated[Optional[List[str]], Argument()],
):
    """(s) Adds a new message to the chain and sends it all."""
    _append(ctx, msg)
    _send(ctx)


def _send(ctx):
    # Encoding happens in the tree
    prompt = ctx.obj.tree.prompt
    params = deepcopy(get_params(ctx, "model"))

    # Then templating (so template stays in english)
    prompt = ctx.obj.templater.prompt(prompt)
    params["prompt"] = prompt

    responses, choice = ctx.obj.simple_gen(ctx.obj.config, params)
    if len(responses) == 1:
        callback = ctx.obj.tree.extend
    else:
        callback = ctx.obj.tree.insert

    for response in responses.values():
        # Decode the response first
        try:
            response = ctx.obj.tree.decoder(response)
        except (binascii.Error, UnicodeDecodeError):
            # Probably the response wasn't encoded?
            pass
        response = ctx.obj.tree.index._create_node(response)
        # Then template
        response = ctx.obj.templater.out(ctx, response)
        callback(response)

    if choice is not None:
        index = len(responses) - choice
        node_indexes = list(ctx.obj.tree.index.index_struct.all_nodes.keys())
        ctx.obj.tree.index.checkout(node_indexes[-index])
    ctx.obj.tree.save()

    path_with_current(ctx)


def push(ctx: Context):
    """(pu, r) sends the tree with no new message."""
    _send(ctx)


def new(ctx: Context):
    """n[ew] starts a new chain (a new root)"""
    ctx.obj.tree.index.clear_checkout()
    ctx.invoke(append, ctx=ctx, msg=None)
    ctx.obj.tree.save()
    path_with_current(ctx)


def append(
    ctx: Context,
    msg: Annotated[Optional[List[str]], Argument()] = None,
):
    """(ap) adds a new node at the end of the chain. If MSG is empty, an editor will be opened."""
    if not msg:
        msg = click.edit()
    _append(ctx, msg)


def save_tree(ctx: Context):
    """(st) Save the current tree"""
    ctx.obj.tree.save()


def tag(
    ctx: Context,
    tag: Annotated[Optional[str], Argument()],
):
    "tags the current branch (empty shows tag list)"
    if tag:
        ctx.obj.tree.index.tag(tag)
    print(ctx.obj.tree.index.tags)


def checkout(ctx: Context, tag: str):
    "(c, co) checks out a tag or index"
    if tag.isdigit():
        tag = int(tag)
    ctx.obj.tree.index.checkout(tag)
    path_with_current(ctx)


def edit(ctx: Context, index: Annotated[Optional[str], Argument()] = None):
    """(e) Edit a node (default is the current node).
    """
    if not index:
        index = ctx.obj.tree.index.path[-1].index
    index = int(index)

    input = ctx.obj.tree.index.index_struct.all_nodes[index].text
    output = click.edit(input)
    if output is None:
        return
    # Vim adds a newline at the end
    output = output.strip("\n")
    ctx.obj.tree.index.index_struct.all_nodes[index].text = output
    print(output)


def edit_prompt(ctx: Context, index: Annotated[Optional[str], Argument()] = None):
    """(prompt) Export the full prompt to an editor for saving."""
    prev_encoder = ctx.obj.tree.encoder
    ctx.obj.tree.encoder = Encoder.get_encoder("none")
    input = str(ctx.obj.tree.prompt)
    ctx.obj.tree.encoder = prev_encoder
    click.edit(input)


def parse_indexes(indexes):
    if "," in indexes:
        indexes = indexes.split(",")
    elif ":" in indexes:
        indexes = indexes.split(":")
    else:
        indexes = indexes.split(" ")
    return [int(index) if index.isdigit() else index for index in indexes]


def delete(ctx: Context, indexes: Annotated[Optional[str], Argument()] = None, all: bool = False):
    "(del) delete some nodes (space separated) (last one by default) (and subnodes if --all)"
    if not indexes:
        indexes = [ctx.obj.tree.index.path[-1].index]
    else:
        indexes = parse_indexes(indexes)
    ctx.obj.tree.index.delete(indexes, all=all)


def cherry_pick(ctx: Context, indexes: str):
    "(cp) Copy nodes onto the current branch (can be indexes or tags, space separated)"
    indexes = parse_indexes(indexes)
    ctx.obj.tree.index.cherry_pick(indexes)
    path_with_current(ctx)


def hoist(ctx: Context, target: Annotated[Optional[str], Argument()] = None):
    "(hh) Copies the node and all downstreams to a new root (or to a target if specified)."
    index = ctx.obj.tree.index.path[-1].index
    ctx.obj.tree.index.hoist(index, target)
    path_with_current(ctx)


def dump(ctx: Context):
    "Dump nodes into a fuzzy finder"
    selection = iterfzf.iterfzf(ctx.obj.tree.index.index_struct.active_tree_with_index, multi=True)
    if selection is None:
        return
    ids = [int(index.split(":")[0]) for index in selection]
    text = "\n".join(selection)
    print(Panel(
        f"[bold magenta]Selected:[/bold magenta]\n{text}\n"
        f"\n[bold magenta]What do you want to do with these nodes?[/bold magenta]\n"
        "\t([bold red]edit, e[/bold red]) dump the nodes into one file and open it in an editor\n"
        "\t([bold red]cherry pick, cp[/bold red]) copy the nodes onto the current branch\n"
        "\t([bold red]delete, d[/bold red]) delete the nodes\n"
        "\t([bold red]cancel, c[/bold red])",
        title="Dump",
        border_style="bold magenta",
    ))
    choice = click.prompt(
        "Choice:",
        type=click.Choice(["edit", "cherry pick", "delete", "cancel", "e", "cp", "d", "c"]),
    )
    if choice in ["e", "edit"]:
        text = "\n".join([ctx.obj.tree.index.index_struct.all_nodes[id].text for id in ids])
        output = click.edit(text)
        if output is None:
            return
        node_template = deepcopy(ctx.obj.tree.index.index_struct.all_nodes[ids[0]])
        node_template.child_indices = set()
        node_template.text = output
        ctx.obj.tree.extend(node_template)
    elif choice in ["cp", "cherry pick"]:
        ctx.obj.tree.index.cherry_pick(ids)
    elif choice in ["d", "delete"]:
        ctx.obj.tree.index.delete(ids)

    path_with_current(ctx)
