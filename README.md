# snip-py

A collection of snippets, notes, examples and links for Python developers and data scientist/analysts.

## Setup

The code in this repo has been tested with python 3.11.4 or higher. In general, examples regarding
pure python (mostly inspired from (Fluent Python)[https://github.com/fluentpython/example-code-2e]),
do not require any external package. You can use `pyenv` to manage python versions.

Some folders on specific topics may require their own environments:

- In [examples](examples), we have some snippets about common python libraries, (e.g. `pandas`, `plotly`, `seaborn`); for these, build a python environment as:

  ```sh
  cd examples
  python -m venv venv
  source venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
  ```

- A different environment is used in the [tf-keras-examples](tf-keras-examples) folder; you can activate in a similar way. See also the local [README.md](tf-keras-examples/README.md) for more info on optimising the installation for GPU acceleration.

- The [hpc-examples](hpc-examples) follows examples from [High performance computing in python](https://books-library.net/files/books-library.net-11301954Yq8A7.pdf).

## Documentation and testing

- [doctest](docs/documentation.md)

## Recognitions

A lot of examples are taken, or inspired, from (Fluent Python)[https://github.com/fluentpython/example-code-2e].
