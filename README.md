# snip-py

A collection of snippets, notes, examples and links for Python developers and data scientist/analysts.

## Setup

The code in this repo has been tested with Python 3.11 or higher. This project uses [uv](https://docs.astral.sh/uv/) for Python version and dependency management.

### Prerequisites

Install uv if you haven't already:

```sh
# Or with Homebrew
brew install uv
```

### Project Structure

This repository is organized into separate example collections, each with its own environment:

- [examples-core-python](examples-core-python) - Core Python language features (sequences, dicts, dataclasses, concurrency, etc.)
- [examples-datascience](examples-datascience) - Data science libraries (pandas, plotly, seaborn, scikit-learn)
- [examples-hpc](examples-hpc) - High Performance Computing examples
- [examples-tensorflow](examples-tensorflow) - TensorFlow and Keras for machine learning

### Environment Setup

Each folder has its own `pyproject.toml` file. Navigate to the folder you're interested in and set up the environment:

```sh
# Example: Setting up the data science environment
cd examples-datascience
uv sync

# Activate the environment
source .venv/bin/activate

# Or run commands directly without activating
uv run jupyter notebook
uv run python your_script.py
```

Repeat for any other folder you want to work with:

```sh
cd examples-core-python  # or examples-hpc, or examples-tensorflow
uv sync
source .venv/bin/activate
```

### Running Jupyter Notebooks

To work with Jupyter notebooks in VS Code:

1. Install the Python and Jupyter extensions in VS Code (they're safe and won't interfere with uv)
2. Navigate to the relevant folder and sync: `cd examples-datascience && uv sync`
3. Open a notebook in VS Code
4. Click "Select Kernel" in the top-right → "Python Environments" → choose the `.venv/bin/python` from the folder

Alternatively, run Jupyter from the command line:

```sh
cd examples-datascience
uv run jupyter notebook
```

### Notes

- The [examples-core-python](examples-core-python) folder contains pure Python examples (mostly inspired from [Fluent Python](https://github.com/fluentpython/example-code-2e)) with minimal dependencies
- The [examples-tensorflow](examples-tensorflow) folder has GPU acceleration notes - see the local [README.md](examples-tensorflow/README.md)
- The [examples-hpc](examples-hpc) folder follows examples from [High Performance Computing in Python](https://books-library.net/files/books-library.net-11301954Yq8A7.pdf)

## Documentation and testing

- [doctest](docs/documentation.md)

## Recognitions

A lot of examples are taken, or inspired, from (Fluent Python)[https://github.com/fluentpython/example-code-2e].
