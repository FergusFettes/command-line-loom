from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from rich.console import Console
from rich.markdown import Markdown

from cll.model import App


app = FastAPI()
app.obj = App()
app.obj.load()


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

