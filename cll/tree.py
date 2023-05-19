import iterfzf
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import click
from cll.data_structs import LoomIndex
from rich import print
from rich.console import Console
from rich.panel import Panel
from typer import Argument, Context, get_app_dir
from typing_extensions import Annotated

from typer_shell import make_typer_shell


@dataclass
class DummyTree:
    params: Optional[dict] = None
    prompt: str = ""

    def input(self, prompt):
        self.prompt = prompt

    def output(self, *_):
        pass

    def __len__(self):
        return 0


@dataclass
class Tree:
    file: Optional[str] = None
    index: Optional[LoomIndex] = None
    params: Optional[dict] = None
    name: Optional[str] = None

    def __post_init__(self):
        self.file = Path(self.file)

        if self.file and self.file.exists():
            self.index = LoomIndex.load_from_disk(str(self.file))
            return

        self.index = LoomIndex()

    @property
    def prompt_context(self):
        path = self.index.path_formatted
        prompt = self.index.context + "\n" + path
        return prompt

    @property
    def prompt(self):
        return self.index.path_formatted

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
    index = ctx.obj.tree.index
    Console().clear()

    name = ctx.command.name
    if name not in ctx.obj.params_groups:
        if ctx.parent:
            name = ctx.parent.command.name
    if name not in ctx.obj.params_groups:
        print("Cant find params!")
    else:
        params = ctx.obj.params_groups[name]['params']
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
    print(Panel.fit(path_str, title="Prompt", border_style="bold magenta"))


cli = make_typer_shell(
    prompt="🌲: ",
    launch=path_with_current,
    params={"path_neighborhood": 3, "head_neighborhood": 10},
    params_path=Path(get_app_dir("cll")) / "tree.yaml"
)


@cli.command()
def default(ctx: Context, line: str):
    """Default command"""
    ctx.invoke(send, ctx=ctx, msg=line.split(" "))


@cli.command(hidden=True)
def h(ctx: Context, count: int = 1):
    "Move to left sibling"
    for _ in range(count):
        ctx.obj.tree.index.step("up")
    path_with_current(ctx)


@cli.command(hidden=True)
def j(ctx: Context, count: int = 1):
    "Move to parent"
    for _ in range(count):
        ctx.obj.tree.index.step("right")
    path_with_current(ctx)


@cli.command(hidden=True)
def k(ctx: Context, count: int = 1):
    "Move to child"
    for _ in range(count):
        ctx.obj.tree.index.step("left")
    path_with_current(ctx)


@cli.command(hidden=True)
@cli.command(name="l", hidden=True)
def left(ctx: Context, count: int = 1):
    "Move to left sibling"
    for _ in range(count):
        ctx.obj.tree.index.step("down")
    path_with_current(ctx)


@cli.command()
def navigate(ctx: Context, direction: str, count: int = 1):
    'Navigate with "hjkl" or "wasd".'
    "You don't need to pass them to this function."
    "View may be rotated 90 degrees."
    for _ in range(count):
        ctx.obj.tree.index.step(direction)
    path_with_current(ctx)


@cli.command()
@cli.command(name="d", hidden=True)
@cli.command(name="p", hidden=True)
def display(
    ctx: Context,
    type: Annotated[Optional[str], Argument()] = "p",
    index: Annotated[Optional[str], Argument()] = None,
):
    """(d, p, t) Various display options (check helpgg).\n
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
        print(ctx.obj.tree._get_repr())

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
        prompt = ctx.obj.templater.prompt(prompt)
        print(prompt)
        return

    if type in ["n", "node"]:
        if index is None:
            print("Please provide an index")
            return

        if "," in index:
            indexes = index.split(",")
        else:
            indexes = [index]

        for index in indexes:
            if index.isdigit():
                print(ctx.obj.tree.index.index_struct.all_nodes[int(index)].text)
                continue


@cli.command(name="tree")
@cli.command(name="t", hidden=True)
def display_tree(ctx: Context):
    """(t) Display the tree."""
    path_with_current(ctx)


def _append(ctx, msg):
    if isinstance(msg, tuple) or isinstance(msg, list):
        msg = " ".join(msg)
    node = ctx.obj.tree.index._create_node(msg)
    node = ctx.obj.templater.in_(node)
    ctx.obj.tree.input(node)


@cli.command()
@cli.command(name="s", hidden=True)
def send(
    ctx: Context,
    msg: Annotated[Optional[List[str]], Argument()],
):
    """(s) Adds a new message to the chain and sends it all."""
    _append(ctx, msg)
    _send(ctx)


def _send(ctx):
    prompt = ctx.obj.tree.prompt
    prompt = ctx.obj.templater.prompt(prompt)

    params = deepcopy(ctx.obj.tree.params)
    params["prompt"] = prompt
    responses, choice = ctx.obj.simple_gen(ctx.obj.config, params)
    if len(responses) == 1:
        response = ctx.obj.tree.index._create_node(responses[0])
        response = ctx.obj.templater.out(response)
        ctx.obj.tree.extend(response)
    else:
        for response in responses.values():
            response = ctx.obj.tree.index._create_node(response)
            response = ctx.obj.templater.out(response)
            ctx.obj.tree.insert(response)

    if choice is not None:
        index = len(responses) - choice
        node_indexes = list(ctx.obj.tree.index.index_struct.all_nodes.keys())
        ctx.obj.tree.index.checkout(node_indexes[-index])
    ctx.obj.tree.save()

    path_with_current(ctx)


@cli.command()
@cli.command(name="pu", hidden=True)
def push(ctx: Context):
    """(pu) sends the tree with no new message."""
    _send(ctx)


@cli.command()
@cli.command(name="n", hidden=True)
def new(ctx: Context):
    """n[ew] starts a new chain (a new root)"""
    ctx.obj.tree.index.clear_checkout()
    ctx.obj.tree.save()


@cli.command()
@cli.command(name="ap", hidden=True)
def append(
    ctx: Context,
    msg: Annotated[Optional[List[str]], Argument()],
):
    """(ap) adds a new node at the end of the chain. If MSG is empty, an editor will be opened."""
    if not msg:
        msg = click.edit()
    _append(ctx, msg)


@cli.command()
def save_tree(ctx: Context):
    """Save the current tree"""
    ctx.obj.tree.save()


@cli.command()
def tag(
    ctx: Context,
    tag: Annotated[Optional[str], Argument()],
):
    "tags the current branch (empty shows tag list)"
    if tag:
        ctx.obj.tree.index.tag(tag)
    print(ctx.obj.tree.index.tags)


@cli.command()
@cli.command(name="c", hidden=True)
def checkout(ctx: Context, tag: str):
    "(c) checks out a tag or index"
    if tag.isdigit():
        tag = int(tag)
    ctx.obj.tree.index.checkout(tag)
    path_with_current(ctx)


@cli.command()
@cli.command(name="e", hidden=True)
def edit(ctx: Context, index: Annotated[Optional[str], Argument()] = None):
    """(e) Edit a node (default is the current node).
    Or pass "prompt" to export the full tree to an editor.
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


@cli.command()
@cli.command(name="prompt", hidden=True)
def edit_prompt(ctx: Context, index: Annotated[Optional[str], Argument()] = None):
    """(prompt) Export the full prompt to an editor for saving."""
    input = str(ctx.obj.tree.prompt)
    click.edit(input)


# @cli.command()
# @cli.command(name="del", hidden=True)
# def delete(ctx: Context, indexes: Annotated[Optional[str], Argument()] = None):
#     "(del) delete some nodes (space separated) (last one by default)"
#     if not indexes:
#         indexes = [ctx.obj.tree.index.path[-1].index]
#     else:
#         indexes = indexes.split(" ")
#     ctx.obj.tree.index.delete(indexes)


@cli.command()
@cli.command(name="cp", hidden=True)
def cherry_pick(ctx: Context, indexes: str):
    "(cp) Copy nodes onto the current branch (can be indexes or tags, space separated)"
    indexes = [int(index) if index.isdigit() else index for index in indexes.split(" ")]
    ctx.obj.tree.index.cherry_pick(indexes)


@cli.command()
def dump(ctx: Context):
    "Dump nodes into a fuzzy finder"
    selection = iterfzf.iterfzf(ctx.obj.tree.index.index_struct.active_tree_with_index, multi=True)
    if selection is None:
        return
    ids = [int(index.split(":")[0]) for index in selection]
    print("\n".join(selection))
    choice = click.prompt(
        f"You selected {ids}, what do you want to do?\n"
        "\t(edit) dump the nodes into one file and open it in an editor\n"
        "\t(cherry pick) copy the nodes onto the current branch\n"
        "\t(delete) delete the nodes\n"
        "\t(cancel)",
        type=click.Choice(["edit", "cherry pick", "delete", "cancel", "e", "cp", "d", "c"]),
    )
    if choice in ["e", "edit"]:
        text = "\n".join([ctx.obj.tree.index.index_struct.all_nodes[id].text for id in ids])
        output = click.edit(text)
        if output is None:
            return
        ctx.obj.tree.extend(output)
    elif choice in ["cp", "cherry pick"]:
        ctx.obj.tree.index.cherry_pick(ids)
    elif choice in ["d", "delete"]:
        ctx.obj.tree.index.delete(ids)

    path_with_current(ctx)


# @staticmethod
# def context(_, command_params, tree):
#     if command_params and command_params[0] == "help":
#         click.echo(
#             "modify the context. context can be added to nodes but are not part of the main path\n"
#             "\t\t\tsubcommands are clear, list, remove or add"
#         )
#         return
#
#     if command_params[0] == "clear":
#         for node in tree.index.path:
#             if node.node_info.get("context"):
#                 del node.node_info["context"]
#
#     if command_params[0] == "list":
#         docs = [(tree.index.get_context(node), node.index) for node in tree.index.path]
#         docs = [(doc, index) for doc, index in docs if doc is not None]
#         for doc, index in docs:
#             doc_text = doc.text.replace("\n", " ")[: tree.termwidth]
#             click.echo(f"{index}: {doc_text}")
#         return
#
#     if command_params[0] == "remove":
#         for index in command_params[1:]:
#             tree.index.delete_context(int(index))
#
#     if command_params[0] == "add":
#         # If no context is given, just add the last node as context
#         if len(command_params) == 1:
#             new_context = tree.index.path[-1].text
#         else:
#             new_context = " ".join(command_params[1:])
#
#         tree.index.add_context(new_context, tree.index.path[-1])
#
#     tree.save()
