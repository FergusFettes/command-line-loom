# Command Line Loom

Command Line Loom is a Python command-line tool for generating text using OpenAI's GPT-3 and other models. It includes a modular model system that allows for easy integration of new models and customization of existing ones.

Includes templates, look in the [Turbo Text Transformer Prompts](https://github.com/fergusfettes/turbo-text-transformer-prompts) repository for more documentation and to find a list of the templates!

## Installation

To install Command Line Loom, you can use pip:

```sh
pip install command-line-loom
```

or clone the repository and install it manually:

```sh
git clone https://github.com/fergusfettes/command-line-loom.git
cd command-line-loom
poetry install
```

## Usage

The basic syntax for running cll is as follows:

```bash
cll <prompt> [options]
```

Here, `<prompt>` is the text that you want to transform. You can use the `--prompt_file` option to load the prompt from a file instead of typing it out on the command line, or you can cat some text in:

```
cat some_file.txt | cll
```

for example, to generate this readme I did

```
cat pyproject.toml cll/__main__.py | cll -t readme > README.md
```

where I'm using the 'readme' template, which is a template for generating a readme file.

### Options

There are several options you can use with the `cll` command:

- `--format/-f`: Output format (default: "clean"). Valid options are "clean", "json", or "logprobs".
- `--echo_prompt/-e`: Echo the prompt in the output.
- `--list_models/-l`: List available models.
- `--prompt_file/-P`: File to load for the prompt.
- `--template_file/-t`: Template file to apply to the prompt.
- `--template_args/-x`: Extra values for the template.
- `--chunk_size/-c`: Max size of chunks.
- `--summary_size/-s`: Size of chunk summaries.
- `--model/-m`: Name of the model to use (default: "gpt-3.5-turbo").
- `--number/-N`: Number of completions.
- `--logprobs/-L`: Show logprobs for completion.
- `--max_tokens/-M`: Max number of tokens to return.
- `--temperature/-T`: Temperature, [0, 2]-- 0 is deterministic, >0.9 is creative.
- `--force/-F`: Force chunking of prompt.

## Configuration

Before using Command Line Loom, you need to set up a configuration file. This should happen automatically when you run the `cll` command for the first time.

This will create a configuration file in your home directory. See the documentation for each model to learn how to obtain an API key.

```~/.config/cll/openai.yaml
api_key: sk-<your api key here>
engine_params:
  frequency_penalty: 0
  logprobs: null
  max_tokens: 1000
  model: davinci
  n: 4
  presence_penalty: 0
  stop: null
  temperature: 0.9
  top_p: 1
models:
- babbage
- davinci
- gpt-3.5-turbo-0301
- text-davinci-003
etc.
```

## Examples

Here are some examples of how to use Command Line Loom:

```
# Generate text with the default model
cll "Once upon a time, there was a"

# Generate text with a specific model
cll -m text-davinci-003 "The meaning of life is"

# Generate multiple completions
cll -n 5 "I like to eat"

# Show logprobs
cll "I like to eat" -f logprobs

# Use the JSON format
cll -f json "I like to eat"
```

If you put in the 'logprobs' flag, it will try to color the terminal output based on the logprobs. This is a bit janky at the moment.

You can also tell it to output a formatted json file with the `-f json` flag. This is useful for piping into other programs.

```
cll -f json "The cat sat on the"
```

If you want to input more text freely, just use it without a prompt and you can write or paste directly into stdin.

## Chunking

If you dump in a tonne of text, it will try to chunk it up into smaller pieces:

```
cat song-of-myself.txt | cll -t poet -x 'poet=Notorious B.I.G.' > song_of_biggie.txt
```

(Note, this is an incredibly wasteful way to extract the text from a website, but at current prices should only cost ~$0.30 so, unhinged as it its, its probably about parity with clicking and dragging.)

### Models

Command Line Loom includes support for text generation with all the openai models. Have a look at the model list with `cll -l`.

## Contributing

If you find a bug or would like to contribute to Command Line Loom, please create a new GitHub issue or pull request.

## Inspiration/Similar

Inspired by [Loom](https://github.com/socketteer/loom) (more to come on this front-- aiming for a command-line-loom).

## License

Command Line Loom is released under the MIT License. See `LICENSE` for more information.
