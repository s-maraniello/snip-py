# Profiling tools
*S. Maraniello*, Dec-2023

This repo contains a mix of code and documentation for python profiling. The content follows closely [High performance computing in python](https://books-library.net/files/books-library.net-11301954Yq8A7.pdf).


## Setup

This code was tested using python 3.11.4. If you use `pyenv`, you may have to preliminary run `pyenv install 3.11.4`; after that Python 3.11.4 will be automatically selected when opening a terminal in this folder. If for any reasons this fails, try to set the environmental variable `PYENV_VERSION`.


Create an environment with all needed profiling tools as:

```sh
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```



## Timing

A few options for timing functions execution:

- `time` module and `print` statements. This can be wrapped as a decorator as per `utils.timefn`.

- `timeit` module. This returns the shortest run over a number.
    ```sh
    python -m timeit -n 5 -r 1 -s "import julia1" \
        "julia1.calc_pure_python(desired_width=1000, max_iterations=300)"
    ```

- `%timeit` magic function in IPython (this is a different implementation than in the `timeit` module and returns mean and standard deviation over a number of executions).
    
    ```python
    import julia1
    %timeit julia1.calc_pure_python(desired_width=1000, max_iterations=300)
    ```

- using the Unix command `/usr/bin/time` (on Mac/Linux).

    ```sh
    /usr/bin/time \
        -p \ # portability flag. This provides 3 results
        --verbose \ # this can be removed
        python julia1.py

    # sample output
    real 2.60 # wall clock or elapsed time.
    user 2.56 # time the CPU spent on your task outside of kernel functions.
    sys 0.02 # time spent in kernel-level functions.
    # the diff between sys+user and real can be the time spent in I/O or if system spent time on other tasks
    ```

- `cProfile` module:
    ```sh
    python -m cProfile -s cumulative julia1.py
    ```

## memory profiling

- `memit` magic function. This requires

    ```python
    # pip install memory_profiler 
    # pip install psutil (optional)
    %load_ext memory_profiler
    %memit xxx
    ```

    It returns a:
    - *peak memory* usage of your system (including memory usage of other processes) during the program runtime. Not extra useful, but helps understanding how close you are to burning all of your RAM.
    - *increment* in memory usage relative to the memory usage just before the program is run (i.e. increment = peak memory - starting memory). This is the most useful to debug a command/piece of code.


## Lists vs Tuples




## Generators

https://wiki.python.org/moin/Generators This is the most clear and simple explanation on why we need a generator. Also, this highlights the difference between a generator and a generator function (which is a python syntax to quickly define a generator). 