import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from typing_extensions import Annotated

import click
import jinja2
import rich
from rich import print
from rich.panel import Panel
from rich.table import Table
from typer import Context, Argument

from typer_shell import get_params, get_params_path

import tttp


@dataclass
class Templater:
    """
    Templates are stored as editable files.
    """

    def in_(self, node):
        in_prefix = self.template_config["in_prefix"] or ""
        node.prefix = in_prefix
        return node

    def prompt(self, prompt):
        out_prefix = self.template_config["out_prefix"] or ""
        prompt = prompt + out_prefix
        if self.template_config["template"]:
            prompt = self._prompt(prompt)
        return prompt

    def _prompt(self, prompt):
        args = {"prompt": prompt}
        template = Path(self.template_file).read_text()
        return jinja2.Template(template).render(**args)

    def out(self, node):
        out_prefix = self.template_config["out_prefix"] or ""
        node.prefix = out_prefix
        return node

    def save(self):
        self.config._dict["templater"] = self.template_config
        self.config.save()

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


def default(ctx: Context, filename: str):
    "(d) Set the default template file."
    if not filename.endswith(".j2"):
        filename = filename + ".j2"
    ctx.obj.templater.template_config["template_file"] = filename
    ctx.obj.templater.save()


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
    ctx.obj.templater.template_config["in_prefix"] = prefix
    ctx.obj.templater.save()


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
    ctx.obj.templater.template_config["out_prefix"] = prefix
    ctx.obj.templater.save()


def edit(
    ctx: Context,
    filename: Annotated[Optional[str], Argument()] = None,
):
    """(e) Edit a template file (default current)."""
    if filename is None:
        filename = Path(ctx.obj.templater.template_file).stem
    if not filename.endswith(".j2"):
        filename = filename + ".j2"
    templates_path = get_params_path(ctx).parent / "templates"
    filename = templates_path / Path(filename)
    click.edit(filename=filename)

    if filename.stem != Path(ctx.obj.templater.template_file).stem:
        default = click.confirm("Make default?", abort=True)
        if default:
            ctx.obj.config._dict["template_file"] = filename.stem
            ctx.obj.config.save()


def telescope(ctx: Context):
    """(t) Find and edit a template with telescope + neovim"""
    command = "nvim +'Telescope find_files' /conf/cll/templates/"
    subprocess.run(command, shell=True)


def new(ctx: Context, filename: str):
    """(n) New template."""
    if not filename.endswith(".j2"):
        filename = filename + ".j2"
    templates_path = get_params_path(ctx).parent / "templates"
    filename = templates_path / Path(filename)

    click.edit(filename=filename)

    default = click.confirm("Make default?", abort=True)
    if default:
        ctx.obj.config._dict["template_file"] = filename.stem
        ctx.obj.config.save()


def show(ctx: Context, filename: str):
    """(s) Show a template."""
    if filename is None:
        filename = Path(ctx.obj.templater.template_file).stem
    if not filename.endswith(".j2"):
        filename = filename + ".j2"
    templates_path = get_params_path(ctx).parent / "templates"
    filename = templates_path / Path(filename)

    print(Panel.fit(filename.read_text(), title=filename.stem, border_style="blue"))
