#!/usr/bin/env python3

from pathlib import Path

from cll.app import App, default as model_default
from cll.templater import cli as templater_cli
from cll.tree import (
    set_encoder,
    file,
    default,
    h,
    j,
    k,
    left,
    neighborhood,
    navigate,
    encoder,
    reencode,
    redecode,
    display,
    display_tree,
    display_all,
    send,
    push,
    new,
    append,
    save_tree,
    tag,
    checkout,
    edit,
    edit_prompt,
    delete,
    cherry_pick,
    hoist,
    dump
)


from cll.config import OPENAI_DEFAULT_PARAMS, TREE_DEFAULT_PARAMS

from typer_shell import make_typer_shell
from typer import get_app_dir


main = make_typer_shell(
    prompt="🧵: ",
    intro="Welcome to Command Line Loom! Type help or ? to list commands.",
    obj=App(),
)


model_cli = make_typer_shell(
    prompt="📃: ",
    intro="Welcome to the Model Config! Type help or ? to list commands.",
    params=OPENAI_DEFAULT_PARAMS,
    params_path=Path(get_app_dir("cll")) / "model.yaml",
)
model_cli.command(name="default")(model_default)


tree_cli = make_typer_shell(
    prompt="🌲: ",
    launch=set_encoder,
    params=TREE_DEFAULT_PARAMS,
    params_path=Path(get_app_dir("cll")) / "tree.yaml"
)
tree_cli.command()(file)
tree_cli.command()(default)
tree_cli.command()(h)
tree_cli.command()(j)
tree_cli.command()(k)
tree_cli.command()(left)
tree_cli.command(name="l", hidden=True)(left)
tree_cli.command()(navigate)
tree_cli.command()(neighborhood)
tree_cli.command(name="nb")(neighborhood)
tree_cli.command()(encoder)
tree_cli.command(name="en", hidden=True)(encoder)
tree_cli.command(name="encoding", hidden=True)(encoder)
tree_cli.command()(reencode)
tree_cli.command(name="re", hidden=True)(reencode)
tree_cli.command()(redecode)
tree_cli.command(name="de", hidden=True)(redecode)
tree_cli.command()(display)
tree_cli.command(name="d", hidden=True)(display)
tree_cli.command(name="p", hidden=True)(display)
tree_cli.command(name="t", hidden=True)(display_tree)
tree_cli.command(name="dt", hidden=True)(display_tree)
tree_cli.command(name="a", hidden=True)(display_all)
tree_cli.command(name="da", hidden=True)(display_all)
tree_cli.command()(send)
tree_cli.command(name="s", hidden=True)(send)
tree_cli.command()(push)
tree_cli.command(name="pu", hidden=True)(push)
tree_cli.command(name="r", hidden=True)(push)
tree_cli.command()(new)
tree_cli.command(name="n", hidden=True)(new)
tree_cli.command()(append)
tree_cli.command(name="ap", hidden=True)(append)
tree_cli.command()(save_tree)
tree_cli.command("st", hidden=True)(save_tree)
tree_cli.command()(tag)
tree_cli.command()(checkout)
tree_cli.command(name="c", hidden=True)(checkout)
tree_cli.command(name="co", hidden=True)(checkout)
tree_cli.command()(edit)
tree_cli.command(name="e", hidden=True)(edit)
tree_cli.command()(edit_prompt)
tree_cli.command(name="prompt", hidden=True)(edit_prompt)
tree_cli.command()(delete)
tree_cli.command(name="del", hidden=True)(delete)
tree_cli.command()(cherry_pick)
tree_cli.command(name="cp", hidden=True)(cherry_pick)
tree_cli.command()(hoist)
tree_cli.command(name="hh", hidden=True)(hoist)
tree_cli.command()(dump)


main.add_typer(tree_cli, name="tree", help="(t) The tree view. This is where you want to be.")
main.add_typer(tree_cli, name="t", hidden=True)


for app in [main, tree_cli]:
    app.add_typer(templater_cli, name="template", help="(tr) Templater.")
    app.add_typer(templater_cli, name="tr", hidden=True)
    app.add_typer(model_cli, name="params", help="(p) Model params.")
    app.add_typer(model_cli, name="p", hidden=True)
