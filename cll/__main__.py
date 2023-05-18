#!/usr/bin/env python3

from cll.app import App
from cll.app import cli as app_cli
from cll.config import cli as config_cli
from cll.store import cli as store_cli
from cll.templater import cli as templater_cli
from cll.tree import cli as tree_cli

from .typer_shell import make_typer_shell

main = make_typer_shell(
    prompt="🧵: ",
    intro="Welcome to Command Line Loom! Type help or ? to list commands.",
    obj=App(),
)


main.add_typer(
    store_cli,
    name="store",
    help="(s) Store just manages the chat files at the moment. It will be updated to a full vecotor store soon.",
)
main.add_typer(store_cli, name="s", hidden=True)
main.add_typer(
    config_cli,
    name="config",
    help=(
        "(c) Config manages the configuration of the app. "
        "Just some file management at the moment. Model config is managed in the 'params'"
    ),
)
main.add_typer(config_cli, name="c", hidden=True)

main.add_typer(app_cli, name="params", help="(p) Model params.")
main.add_typer(app_cli, name="p", hidden=True)

main.add_typer(tree_cli, name="tree", help="(t) The tree view. This is where you want to be.")
main.add_typer(tree_cli, name="t", hidden=True)

tree_cli.add_typer(app_cli, name="params", help="(p) Model params.")
tree_cli.add_typer(app_cli, name="p", hidden=True)

main.add_typer(templater_cli, name="template", help="(tr) Templater.")
main.add_typer(templater_cli, name="tr", hidden=True)

tree_cli.add_typer(templater_cli, name="template", help="(tr) Templater.")
tree_cli.add_typer(templater_cli, name="tr", hidden=True)
