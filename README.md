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

Should be self-documenting in the interface. Just type 'help'.

Some node manipulation: [vid](https://asciinema.org/a/3WatU4HNowuXAACE10eAJrzTD)

Watch this for more advanced usage: [vid](https://asciinema.org/a/tLpxm9FdW6gKdJztRnAPAOl7X).

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

## Contributing

If you find a bug or would like to contribute to Command Line Loom, please create a new GitHub issue or pull request.

## Inspiration/Similar

Inspired by [Loom](https://github.com/socketteer/loom).

## License

Command Line Loom is released under the MIT License. See `LICENSE` for more information.
