from typing import Callable, Optional

from click_shell import make_click_shell
from rich import print
from typer import Argument, Context, Typer
from typing_extensions import Annotated


def make_typer_shell(
    prompt: str = ">> ",
    intro: str = "\n Welcome to typer-shell! Type help to see commands.\n",
    default: Optional[Callable] = None,
    obj: Optional[object] = None,
    launch: Optional[Callable] = None,
    # params: bool = True,
    # params_path: Optional[Path] = None
) -> None:
    """Create a typer shell
    'default' is a default command to run if no command is found
    'obj' is an object to pass to the context
    # 'params' is a boolean to add a local params command
    """
    app = Typer()

    @app.command(hidden=True)
    def help(ctx: Context, command: Annotated[Optional[str], Argument()] = None):
        print("\n Type 'command --help' or 'help <command>' for help on a specific command.")
        if not command:
            ctx.parent.get_help()
            return
        _command = ctx.parent.command.get_command(ctx, command)
        if _command:
            _command.get_help(ctx)
        else:
            print(f"Command '{command}' not found.")

    @app.command(hidden=True)
    def _default(ctx: Context, args: Annotated[Optional[str], Argument()] = None):
        """Default command"""
        if default:
            default(ctx, args)
        else:
            print("Command not found. Type 'help' to see commands.")

    @app.callback(invoke_without_command=True)
    def _launch(ctx: Context):
        if obj:
            ctx.obj = obj
        if ctx.invoked_subcommand is None:
            shell = make_click_shell(ctx, prompt=prompt, intro=intro)
            shell.default = _default
            if launch:
                launch(ctx)
            # if params:
            #     shell.params = params(params_path)
            shell.cmdloop()

    @app.command(hidden=True)
    def shell(ctx: Context):
        """Drop into an ipython shell"""
        import IPython

        IPython.embed()

    return app
