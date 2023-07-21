from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from rich.console import Console
from rich.markdown import Markdown

from cll.model import App
from typer_shell import get_params


app = FastAPI()
app.obj = App.load()


@app.get("/", response_class=HTMLResponse)
def introduction():
    """Command Line Loom API!"""
    with open("README.md", "r") as f:
        readme = f.read()
    console = Console(record=True, stderr=True)
    markdown = Markdown(readme)
    console.print(markdown, style="bold red")
    return console.export_html()


@app.get("/model")
def model_params():
    return get_params(app, "model")
# clone for the others


@app.get("/tree/tree")
def get_tree():
    return {"tree": app.obj.tree.index.index_struct.get_full_repr()}


@app.get("/tree/prompt")
def get_prompt():
    return {"prompt": app.obj.tree.prompt}
