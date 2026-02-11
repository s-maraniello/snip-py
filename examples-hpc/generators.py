"""
Generators

Examples from Chap.4 of "High performance computing in python"
"""


### Lists vs generators

def fibonacci_list(num_items):
    numbers = []
    a, b = 0, 1
    while len(numbers) < num_items:
        numbers.append(a)
        a, b = b, a+b
    return numbers


def fibonacci_gen(num_items):
    """Reminder this function will return a generator with __next__ method. Namely, if you type:
    >>> a = fibonacci_gen(10)
    >>> type(a)
    generator 
    """
    a, b = 0, 1
    while num_items:
        yield a
        a, b = b, a+b
        num_items -= 1


def test_fibonacci_list():
    """
    >>> %timeit test_fibonacci_list()
    332 ms ± 13.1 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)
    >>> %memit test_fibonacci_list()
    peak memory: 492.82 MiB, increment: 441.75 MiB
    """
    for i in fibonacci_list(100_000):
        pass


def test_fibonacci_gen():
    """
    >>> %timeit test_fibonacci_gen()
    126 ms ± 905 µs per loop (mean ± std. dev. of 7 runs, 10 loops each)
    >>> %memit test_fibonacci_gen()
    peak memory: 51.13 MiB, increment: 0.00 MiB
    """
    for i in fibonacci_gen(100_000):
        pass



### Generator comprehension

def count_divisible_by_x_gen(num_items:int, x:int):
    return sum( 1 for n in fibonacci_gen(num_items) if n%x==0 )

def count_divisible_by_x_list(num_items:int, x:int):
    # return sum([1 for n in fibonacci_gen(num_items) if n%x==0])
    return len([n for n in fibonacci_gen(num_items) if n%x==0])

