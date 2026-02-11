"""Profiling tools. Examples from "High performance computing in python", Ch. 2."""

from functools import wraps
import time


def timefn(fn):
    """Decorator for timing functions extacution time. Usage:
    >>>@timefin
    >>>def my_function(...):
    >>>    ...
    """

    @wraps(fn)
    def measure_time(*args, **kwargs):
        t1 = time.time()
        result = fn(*args, **kwargs)
        t2 = time.time()
        print(f"@timefn: {fn.__name__} took {t2 - t1:.8f} seconds")
        return result
    return measure_time



if __name__ == "__main__":
    # how to use timefn decorator
    @timefn
    def my_function(N: int):
        for i in range(N):
            pass
    

    my_function(1000)

    
