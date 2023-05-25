import re
import shutil
from collections import defaultdict
from dataclasses import dataclass

import openai
import rich
import typer
from rich import print
from rich.live import Live
from rich.table import Table
from typer import Context
import tiktoken

from cll.config import Config
from cll.store import Store
from cll.templater import Templater

from typer_shell import get_params, IO


@dataclass
class App:
    echo_prompt: bool = False
    append: bool = False
    model_tokens = {
        "gpt-4": 4096 - 8,
        "gpt-3.5-turbo": 4096 - 8,
        "text-davinci-003": 4096 - 8,
        "text-davinci-002": 4096 - 8,
        "code-davinci-002": 4096 - 8,
    }

    def __post_init__(self):
        self.config = Config.check_config()
        self.store = Store(config=self.config)
        self.templater = Templater(config=self.config)
        self.io = IO
        self.tree = self.store.load_file()

    @staticmethod
    def get_encoding(model):
        try:
            encoding = tiktoken.encoding_for_model(model)
        except (KeyError, ValueError):
            encoding = tiktoken.get_encoding("gpt2")
        return encoding

    @staticmethod
    def simple_gen(config, params):
        if params["model"] == "test":
            return params["prompt"]
        App.max_tokens(params)
        if params["model"] == "code-davinci-002":
            if "cd2_base" not in config or "cd2_key" not in config:
                raise typer.Exit("Please set cd2_base and cd2_key in your config file")
            openai.api_base = config.get("cd2_base")
            openai.api_key = config.get("cd2_key")
            params["stream"] = False
        generations, choice = OAIGen.gen(params)
        if params["model"] == "code-davinci-002":
            openai.api_key = config.get("api_key")
            openai.api_base = config.get("api_base", "https://api.openai.com/v1")

        for i, gen in generations.items():
            if gen.startswith("\n"):
                generations[i] = gen[1:]
        choice = choice - 1 if choice != -1 else None
        return generations, choice

    @staticmethod
    def max_tokens(params):
        model_max = Config.model_tokens.get(params["model"], 2048)

        encoding = Config.get_encoding(params.get("model", "gpt-3.5-turbo"))
        request_total = params["max_tokens"] + len(encoding.encode(params["prompt"]))

        if request_total > model_max:
            params["max_tokens"] = model_max - len(encoding.encode(params["prompt"]))

    def output(self, response):
        self.io.return_prompt(
            response, self.prompt if self.echo_prompt else None, self.prompt_file if self.append else None
        )


class OAIGen:
    @staticmethod
    def gen(params):
        if params["model"].startswith("gpt-3.5") or params["model"].startswith("gpt-4"):
            return OAIGen._chat(params)
        return OAIGen._gen(params)

    @staticmethod
    def _gen(params):
        resp = openai.Completion.create(**params)
        if not params["stream"]:
            resp = [resp]

        choice = -1
        with Live(screen=True) as live:
            completions = defaultdict(str)
            for part in resp:
                choices = part["choices"]
                for chunk in sorted(choices, key=lambda s: s["index"]):
                    c_idx = chunk["index"]
                    if not chunk["text"]:
                        continue
                    completions[c_idx] += chunk["text"]
                    OAIGen.richprint(params["prompt"], completions, live)
            if len(completions):
                OAIGen.richprint(params["prompt"], completions, live, final=True)
                choice = typer.prompt("Choose a completion", default=-1, type=int)
        return completions, choice

    @staticmethod
    def _chat(params):
        params["messages"] = [{"role": "user", "content": params["prompt"]}]
        if "prompt" in params:
            prompt = params["prompt"]
            del params["prompt"]
        if "logprobs" in params:
            del params["logprobs"]

        resp = openai.ChatCompletion.create(**params)

        if not params["stream"]:
            resp = [resp]

        choice = -1
        with Live(screen=True) as live:
            completions = defaultdict(str)
            for part in resp:
                choices = part["choices"]
                for chunk in sorted(choices, key=lambda s: s["index"]):
                    c_idx = chunk["index"]
                    delta = chunk["delta"]
                    if "content" not in delta:
                        continue
                    content = chunk["delta"]["content"]
                    if not content:
                        break
                    completions[c_idx] += content
                    OAIGen.richprint(prompt, completions, live)
            if len(completions):
                OAIGen.richprint(prompt, completions, live, final=True)
                choice = typer.prompt("Choose a completion", default=-1, type=int)

        for i, gen in completions.items():
            # If the completion starts with a letter, prepend a space
            if re.match(r"^[a-zA-Z]", gen):
                completions[i] = " " + gen
        return completions, choice

    @staticmethod
    def richprint(prompt, messages, live, final=False):
        messages = {k: v for k, v in sorted(messages.items(), key=lambda item: item[0])}
        choice_msg = ""
        if final:
            choice_msg = "Choose a completion (optional). [Enter] to continue. "
        table = Table(
            box=rich.box.MINIMAL_DOUBLE_HEAD,
            width=shutil.get_terminal_size().columns,
            show_lines=True,
            show_header=False,
            title=prompt[-1000:],
            title_justify="left",
            caption=choice_msg + ", ".join([str(i + 1) for i in messages.keys()]),
            style="bold blue",
            highlight=True,
            title_style="bold blue",
            caption_style="bold blue",
        )
        for i, message in messages.items():
            table.add_row(str(i + 1), f"[bold]{message}[/bold]")
        live.update(table)


def default(ctx: Context, line: str):
    """Default command"""
    args = line.split(" ")
    params = get_params(ctx)
    if args[0] in params:
        Config._update(args[0], args[1], params)
    else:
        print(
            f"[red]Unknown command/param {args[0]}[/red]. "
            "If you need to add it to the dict, use 'update'."
        )
    print(params)
