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

> **VS Code Workspace Setup**: This project is configured to work seamlessly with VS Code using a multi-folder workspace (`snip-py.code-workspace`). Each folder has its own Python environment that VS Code automatically detects based on your current location. This setup ensures seamless Jupyter notebook integration with multiple Python environments. **When prompted by VS Code to open the workspace**, select **"Open Workspace"** to enable this functionality.

### Environment Setup

Each folder has its own `pyproject.toml` and `Makefile`. You can set up environments using either Make or uv directly.

#### Using Make (Recommended)

```sh
# Setup all environments at once
make setup

# Or setup a specific environment
make setup-datascience
make setup-core-python
make setup-hpc
make setup-tensorflow

# Clean all environments
make clean

# Clean a specific environment
make clean-datascience
```

From within any example folder:

```sh
cd examples-datascience
make setup          # Set up the environment
make jupyter        # Start Jupyter notebook
make shell          # Open Python shell
make clean          # Clean up .venv and cache files
make help           # See all available commands
```

#### Using uv directly

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

### Running Jupyter Notebooks

To work with Jupyter notebooks in VS Code:

1. Install the Python and Jupyter extensions in VS Code (they're safe and won't interfere with uv)
2. Navigate to the relevant folder and setup: `cd examples-datascience && make setup`
3. Open a notebook in VS Code
4. Click "Select Kernel" in the top-right → "Python Environments" → choose the `.venv/bin/python` from the folder

Alternatively, run Jupyter from the command line:

```sh
cd examples-datascience
make jupyter
# Or: uv run jupyter notebook
```

### Notes

- The [examples-core-python](examples-core-python) folder contains pure Python examples (mostly inspired from [Fluent Python](https://github.com/fluentpython/example-code-2e)) with minimal dependencies
- The [examples-tensorflow](examples-tensorflow) focuses on tensorflow and vertex AI - see the local [README.md](examples-tensorflow/README.md)
- The [examples-hpc](examples-hpc) folder follows examples from [High Performance Computing in Python](https://books-library.net/files/books-library.net-11301954Yq8A7.pdf)

## Documentation and testing

- [doctest](docs/documentation.md)

## Recognitions

A lot of examples are taken, or inspired, from (Fluent Python)[https://github.com/fluentpython/example-code-2e].
