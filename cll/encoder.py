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
class Encoder:
    """
    Encode each word of the input with a cypher.
    """

    def map(self, string, callback):
        """Go through the string, extracting each word and applying the callback."""
        return " ".join([callback(word) for word in string.split(" ")])

    def rot13(self, string):
        """Encode the string with rot13."""
        return self.map(string, lambda word: word.encode("rot13"))
