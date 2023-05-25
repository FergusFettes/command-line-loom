import os
import datetime
import logging
from pathlib import Path

from rich import print


file_path = Path("/tmp/cll/")
file_path.mkdir(parents=True, exist_ok=True)

log_path = file_path / "logs"
log_path.mkdir(parents=True, exist_ok=True)

timestamp = datetime.datetime.now().replace(microsecond=0).isoformat()
logfile = log_path / f"{timestamp}.log"

DEBUG = os.environ.get("DEBUG", False)

if DEBUG:
    print("DEBUG MODE")
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.INFO,
    )
else:
    logging.basicConfig(
        filename=logfile,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.INFO,
    )
logger = logging.getLogger()


OPENAI_DEFAULT_PARAMS = {
    "frequency_penalty": 0,
    "logprobs": 1,
    "max_tokens": 200,
    "model": "gpt-3.5-turbo",
    "n": 1,
    "presence_penalty": 0,
    "stop": ["I'm sorry", "As an AI"],
    "temperature": 0.9,
    "top_p": 1,
    "stream": True,
}

TEMPLATE_DEFAULT_PARAMS = {
    "in_prefix": "\nHuman: ",
    "out_prefix": "\nGPT:",
    "template": True,
    "template_path": "~/.config/cll/templates",
    "template_file": "assist.j2",
}

TREE_DEFAULT_PARAMS = {
    "path_neighborhood": 3,
    "head_neighborhood": 10,
    "encoder": None,
    "chat_path": "~/.config/cll/chats",
    "chat_name": "default",
    "echo_prompt": False,
    "append": False,
}

