import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from typing_extensions import Annotated
import re

import click
import jinja2
import rich
from rich import print
from rich.panel import Panel
from rich.table import Table
from typer import Context, Argument

from typer_shell import get_params, get_params_path, update, save

import tttp


@dataclass
class Templater:
    """
    Templates are stored as editable files.
    """

    @staticmethod
    def in_(ctx: Context, node):
        params = get_params(ctx)
        in_prefix = params["in_prefix"] or ""
        node.prefix = in_prefix
        return node

    @staticmethod
    def prompt(ctx: Context, prompt):
        params = get_params(ctx)
        out_prefix = params["out_prefix"] or ""
        prompt = prompt + out_prefix
        if params["template"]:
            prompt = Templater._prompt(prompt)
        return prompt

    @staticmethod
    def _prompt(ctx: Context, prompt):
        templates_path = get_params_path(ctx).parent / "templates"
        params = get_params(ctx)

        args = {"prompt": prompt}
        template = (templates_path / params["template_file"]).read_text()
        return jinja2.Template(template).render(**args)

    def out(ctx: Context, node):
        params = get_params(ctx)
        out_prefix = params["out_prefix"] or ""
        node.prefix = out_prefix
        return node

    @staticmethod
    def list(ctx: Context, short: bool = True):
        templates_path = get_params_path(ctx).parent / "templates"
        if not templates_path.exists():
            return

        files = [x for x in templates_path.glob("*.j2")]
        print(f"Found {len(files)} templates.")
        if short:
            table = Table("Filename", "Text", box=rich.box.MINIMAL_DOUBLE_HEAD, show_lines=True)

        for file in files:
            if short:
                table.add_row(file.stem, file.read_text().replace("\n", "\\n"))
            else:
                print(Panel(file.read_text(), title=file.stem, border_style="blue"))

        if short:
            print(table)


def create(ctx: Context):
    # Find the templates, and make sure they are in the right place
    tttpath = Path(tttp.__file__).parent
    new_templates = tttpath.parent / "templates"
    templates_path = get_params_path(ctx).parent / "templates"
    templates_path.mkdir(parents=True, exist_ok=True)
    for template in new_templates.glob("*.j2"):
        if not (templates_path / template.name).exists():
            (templates_path / template.name).write_text(template.read_text())


def launch(ctx):
    params = get_params(ctx)
    params_path = get_params_path(ctx)
    template_file = params_path.parent / "templates" / params["template_file"]
    if template_file.exists():
        contents = template_file.read_text()
        print(Panel(contents, title=params["template_file"], border_style="blue"))
    else:
        print(f"Template file {template_file} does not exist.")


def set_default(ctx: Context, filename: str):
    "(d) Set the default template file."
    if not filename.endswith(".j2"):
        filename = filename + ".j2"
    update(ctx, "template_file", filename)
    save(ctx)


def in_(
    ctx: Context,
    prefix: Annotated[str, Argument()] = "",
    newline: bool = True,
):
    """Set the prefix for input prompts (eg 'Human').\n
    If no prefix is provided, the prefix will be removed.\n
    Newline [default] inserts a newline between messages. It is false by default when there is no prefix.
    """
    newline = newline and bool(prefix)
    if newline:
        prefix = "\n" + prefix
    update(ctx, "in_prefix", prefix)
    save(ctx)


def out(
    ctx: Context,
    prefix: Annotated[str, Argument()] = "",
    newline: bool = True,
):
    """Set the prefix for return prompts (eg 'GPT-4').\n
    If no prefix is provided, the prefix will be removed.\n
    Newline [default] inserts a newline between messages. It is false by default when there is no prefix.
    """
    newline = newline and bool(prefix)
    if newline:
        prefix = "\n" + prefix
    update(ctx, "out_prefix", prefix)
    save(ctx)


def edit(
    ctx: Context,
    filename: Annotated[Optional[str], Argument()] = None,
):
    """(e) Edit a template file (default current)."""
    templates_path = get_params_path(ctx).parent / "templates"

    if filename is None:
        filename = (templates_path / filename).stem
    if not filename.endswith(".j2"):
        filename = filename + ".j2"
    templates_path = get_params_path(ctx).parent / "templates"
    filename = templates_path / Path(filename)
    click.edit(filename=filename)

    params = get_params(ctx)
    current_file = templates_path / params["template_file"]

    if filename.stem != current_file.stem:
        default = click.confirm("Make default?", abort=True)
        if default:
            update(ctx, "template_file", filename.stem)
            save(ctx)


def telescope(ctx: Context):
    """(t) Find and edit a template with telescope + neovim"""
    command = "nvim +'Telescope find_files' /conf/cll/templates/"
    subprocess.run(command, shell=True)


def new(ctx: Context, filename: str):
    """(n) New template."""
    if not filename.endswith(".j2"):
        filename = filename + ".j2"
    templates_path = get_params_path(ctx).parent / "templates"
    filename = templates_path / filename

    click.edit(filename=filename)
    # Open the file, and check that there is a string like "{.{0,1}prompt.{0,1}} in it"
    with filename.open('r') as fi:
        contents = fi.read()
    if not re.search(r"{.{0,1}prompt.{0,1}}", contents):
        print("File does not contain a prompt. You need a string like { prompt } in it.")
        return

    default = click.confirm("Make default?", abort=True)
    if default:
        update(ctx, "template_file", filename.stem)
        save(ctx)


def show(ctx: Context, filename: str):
    """(s) Show a template."""
    params = get_params(ctx)
    if filename is None:
        filename = Path(params["template_file"]).stem
    if not filename.endswith(".j2"):
        filename = filename + ".j2"
    templates_path = get_params_path(ctx).parent / "templates"
    filename = templates_path / Path(filename)

    print(Panel.fit(filename.read_text(), title=filename.stem, border_style="blue"))
