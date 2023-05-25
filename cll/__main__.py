#!/usr/bin/env python3

from pathlib import Path

from cll.app import App, default as model_default
from cll.config import reinit
from cll.store import cli as store_cli
from cll.templater import cli as templater_cli
from cll.tree import (
    set_encoder,
)


from cll.config import OPENAI_DEFAULT_PARAMS, TREE_DEFAULT_PARAMS

from typer_shell import make_typer_shell
from typer import get_app_dir


main = make_typer_shell(
    prompt="🧵: ",
    intro="Welcome to Command Line Loom! Type help or ? to list commands.",
    obj=App(),
)

main.add_command(name="reinit")(reinit)


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


main.add_typer(
    store_cli,
    name="store",
    help="(s) Store just manages the chat files at the moment. It will be updated to a full vecotor store soon.",
)
main.add_typer(store_cli, name="s", hidden=True)
main.add_typer(tree_cli, name="tree", help="(t) The tree view. This is where you want to be.")
main.add_typer(tree_cli, name="t", hidden=True)


for app in [main, tree_cli]:
    app.add_typer(templater_cli, name="template", help="(tr) Templater.")
    app.add_typer(templater_cli, name="tr", hidden=True)
    app.add_typer(model_cli, name="params", help="(p) Model params.")
    app.add_typer(model_cli, name="p", hidden=True)
