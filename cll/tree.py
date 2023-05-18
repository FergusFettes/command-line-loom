from copy import deepcopy
from dataclasses import dataclass
# from functools import partial
from pathlib import Path
from typing import List, Optional

import click
from cll.data_structs import LoomIndex
from rich import print
from rich.console import Console
from rich.panel import Panel
from typer import Argument, Context
from typing_extensions import Annotated

from .typer_shell import make_typer_shell


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
    join: str = ""

    def __post_init__(self):
        self.file = Path(self.file)

        if self.file and self.file.exists():
            self.index = LoomIndex.load_from_disk(str(self.file))
            return

        self.index = LoomIndex()

    @property
    def prompt_context(self):
        path = self.index.path
        prompt = self.index.context + "\n" + f"{self.join}".join([node.text for node in path])
        return prompt

    @property
    def prompt(self):
        return self._prompt()

    def _prompt(self, n=None):
        if n:
            path = self.index.path[:n]
        else:
            path = self.index.path
        return f"{self.join}".join([node.text for node in path])

    def input(self, prompt):
        self.extend(prompt)

    def output(self, prompt):
        self.extend(prompt, save=True)

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
    Console().clear()
    ctx.obj.tree.index.index_struct.legend()
    print(ctx.obj.tree.index.index_struct)
    if not ctx.obj.tree.index.path:
        return
    path = ctx.obj.tree.index.path
    path_str = ctx.obj.tree._prompt(-1)
    path_str += ctx.obj.tree.join
    path_str += "[bold red]"
    path_str += path[-1].text
    path_str += "[/bold red]"
    print(Panel.fit(path_str, title="Prompt", border_style="bold magenta"))


def default(msg):
    """Default command"""
    print("Default doesn't work yet :/.")


cli = make_typer_shell(
    prompt="🌲: ",
    launch=path_with_current,
    default=default,
)


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
        ctx.obj.tree.legend()
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
    msg = ctx.obj.templater.in_(msg)
    ctx.obj.tree.input(msg)
    ctx.obj.tree.save()


@cli.command()
@cli.command(name="s", hidden=True)
def send(
    ctx: Context,
    msg: Annotated[Optional[List[str]], Argument()],
):
    """(s) Adds a new message to the chain and sends it all."""
    _append(ctx, msg)

    prompt = ctx.obj.tree.prompt
    prompt = ctx.obj.templater.prompt(prompt)

    params = deepcopy(ctx.obj.tree.params)
    params["prompt"] = prompt
    responses, choice = ctx.obj.simple_gen(ctx.obj.config, params)
    if len(responses) == 1:
        response = ctx.obj.templater.out(responses[0])
        ctx.obj.tree.extend(response)
    else:
        for response in responses.values():
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

    prompt = ctx.obj.tree.prompt
    prompt = ctx.obj.templater.prompt(prompt)

    params = deepcopy(ctx.obj.tree.params)
    params["prompt"] = prompt
    responses, choice = ctx.obj.simple_gen(ctx.obj.config, params)
    if len(responses) == 1:
        response = ctx.obj.templater.out(responses[0])
        ctx.obj.tree.extend(response)
    else:
        for response in responses.values():
            response = ctx.obj.templater.out(response)
            ctx.obj.tree.insert(response)

    if choice is not None:
        index = len(responses) - choice
        node_indexes = list(ctx.obj.tree.index.index_struct.all_nodes.keys())
        ctx.obj.tree.index.checkout(node_indexes[-index])
    ctx.obj.tree.save()

    path_with_current(ctx)


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
def save(ctx: Context):
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


@cli.command()
@cli.command(name="del", hidden=True)
def delete(ctx: Context, indexes: Annotated[Optional[str], Argument()] = None):
    "(del) delete some nodes (space separated) (last one by default)"
    if not indexes:
        indexes = [ctx.obj.tree.index.path[-1].index]
    else:
        indexes = indexes.split(" ")

    for index in indexes:
        ctx.obj.tree.index.delete(int(index))


@cli.command()
@cli.command(name="cp", hidden=True)
def cherry_pick(ctx: Context, indexes: str):
    "(cp) Copy nodes onto the current branch (can be indexes or tags, space separated)"
    indexes = [int(index) if index.isdigit() else index for index in indexes.split(" ")]
    ctx.obj.tree.index.cherry_pick(indexes)


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
