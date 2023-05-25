#!/usr/bin/env python3

from cll.app import App, default as model_default
from cll.config import cli as config_cli
from cll.store import cli as store_cli
from cll.templater import cli as templater_cli
from cll.tree import cli as tree_cli

from cll import OPENAI_DEFAULT_PARAMS

from typer_shell import make_typer_shell


main = make_typer_shell(
    prompt="🧵: ",
    intro="Welcome to Command Line Loom! Type help or ? to list commands.",
    obj=App(),
)


model_cli = make_typer_shell(
    prompt="📃: ",
    intro="Welcome to the Model Config! Type help or ? to list commands.",
    params=OPENAI_DEFAULT_PARAMS,
    hidden_params=["API_KEY", "API_BASE"]
)
model_cli.command()(model_default)

# TODO: check for openai api key here? or just check when it comes up?

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
main.add_typer(tree_cli, name="tree", help="(t) The tree view. This is where you want to be.")
main.add_typer(tree_cli, name="t", hidden=True)


for app in [main, tree_cli]:
    app.add_typer(templater_cli, name="template", help="(tr) Templater.")
    app.add_typer(templater_cli, name="tr", hidden=True)
    app.add_typer(app_cli, name="params", help="(p) Model params.")
    app.add_typer(app_cli, name="p", hidden=True)
