import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import click
import jinja2
import rich
from rich import print
from rich.panel import Panel
from rich.table import Table
from typer import Argument, Context
from typing_extensions import Annotated

from .config import Config
from typer_shell import make_typer_shell


@dataclass
class Templater:
    """
    Templates are stored as editable files.
    """

    config: Optional["Config"] = None  # type: ignore
    template_config: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.config:
            self.template_config = self.config._dict["templater"]

    @property
    def template_file(self):
        """The template_file property."""
        return str(self.template_path / self.template_config["template_file"])

    @template_file.setter
    def template_file(self, value):
        self.template_config["template_file"] = str(value)

    @property
    def template_path(self):
        """The template_path property."""
        return Path(self.template_config["template_path"]).expanduser()

    @template_path.setter
    def template_path(self, value):
        self.template_config["template_file"] = str(value)

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

    def list_templates(self, short):
        if not self.template_path.exists():
            return

        files = [x for x in self.template_path.glob("*.j2")]
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


def launch(ctx):
    if Path(ctx.obj.templater.template_file).exists():
        contents = Path(ctx.obj.templater.template_file).read_text()
        print(Panel(contents, title=ctx.obj.templater.template_file, border_style="blue"))
    else:
        print(f"Template file {ctx.obj.templater.template_file} does not exist.")


cli = make_typer_shell(prompt="🤖: ", intro="Welcome to the templater shell.", launch=launch)


@cli.command(name="print")
@cli.command(name="p", hidden=True)
def _print(ctx: Context):
    "(p) Print the current config."
    print(ctx.obj.templater.template_config)


@cli.command()
@cli.command(name="s", hidden=True)
def save(ctx: Context):
    "(s) Save the current config to the config file."
    config = ctx.obj.templater.config
    config["templater"] = ctx.obj.templater.template_config
    Config.save_config(ctx.obj.templater.config)


@cli.command()
@cli.command(name="u", hidden=True)
def update(
    ctx: Context,
    name: Annotated[Optional[str], Argument()] = None,
    value: Annotated[Optional[str], Argument()] = None,
    kv: Annotated[Optional[str], Argument()] = None,
):
    "(u) Update a config value, or set of values. (kv in the form of 'name1=value1,name2=value2')"
    if kv:
        updates = kv.split(",")
        for kv in updates:
            name, value = kv.split("=")
            ctx.obj._update(name, value, ctx.obj.templater.template_config)
        return
    ctx.obj.config._update(name, value, ctx.obj.templater.template_config)


@cli.command()
def toggle(ctx: Context):
    ctx.obj.templater.template_config["template"] = not ctx.obj.templater.template_config["template"]
    print(f"Template mode is {'on' if ctx.obj.templater.template_config['template'] else 'off'}.")
    config = ctx.obj.templater.config
    config["templater"] = ctx.obj.templater.template_config
    Config.save_config(ctx.obj.templater.config)


@cli.command()
@cli.command(name="d", hidden=True)
def default(ctx: Context, filename: str):
    "(d) Set the default template file."
    if not filename.endswith(".j2"):
        filename = filename + ".j2"
    ctx.obj.templater.template_config["template_file"] = filename
    ctx.obj.templater.save()


@cli.command(name="in")
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


@cli.command()
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


@cli.command()
@cli.command(name="l", hidden=True)
@cli.command(name="ls", hidden=True)
def list(ctx: Context, short: bool = True):
    """(l, ls) List all templates."""
    ctx.obj.templater.list_templates(short)


@cli.command()
@cli.command(name="e", hidden=True)
def edit(
    ctx: Context,
    filename: Annotated[Optional[str], Argument()] = None,
):
    """(e) Edit a template file (default current)."""
    if filename is None:
        filename = Path(ctx.obj.templater.template_file).stem
    if not filename.endswith(".j2"):
        filename = filename + ".j2"
    filename = ctx.obj.templater.template_path / Path(filename)
    click.edit(filename=filename)

    if filename.stem != Path(ctx.obj.templater.template_file).stem:
        default = click.confirm("Make default?", abort=True)
        if default:
            ctx.obj.config._dict["template_file"] = filename.stem
            ctx.obj.config.save()


@cli.command()
@cli.command(name="t", hidden=True)
def telescope(ctx: Context):
    """(t) Find and edit a template with telescope + neovim"""
    command = "nvim +'Telescope find_files' /conf/cll/templates/"
    subprocess.run(command, shell=True)


@cli.command()
@cli.command(name="n", hidden=True)
def new(ctx: Context, filename: str):
    """(n) New template."""
    if not filename.endswith(".j2"):
        filename = filename + ".j2"
    filename = ctx.obj.templater.template_path / Path(filename)

    click.edit(filename=filename)

    default = click.confirm("Make default?", abort=True)
    if default:
        ctx.obj.config._dict["template_file"] = filename.stem
        ctx.obj.config.save()


@cli.command()
@cli.command(name="s", hidden=True)
def show(ctx: Context, filename: str):
    """(s) Show a template."""
    if filename is None:
        filename = Path(ctx.obj.templater.template_file).stem
    if not filename.endswith(".j2"):
        filename = filename + ".j2"
    filename = ctx.obj.templater.template_path / Path(filename)

    print(Panel.fit(filename.read_text(), title=filename.stem, border_style="blue"))
