"""
This is a great example of using generators and lazy evaluation concepts.
"""



from random import normalvariate, randint
from itertools import count
from datetime import datetime

from itertools import groupby



def read_data(filename):
    with open(filename) as fd:
        for line in fd:
            data = line.strip().split(',')
            timestamp, value = map(int, data)
            yield datetime.fromtimestamp(timestamp), value

def read_fake_data(filename):
    """
    Generator that will Returns dummy data in format:
    >>> (datetime.datetime(1970, 1, 1, 1, 0), 100)
    """
    for timestamp in count():
        # We insert an anomalous data point approximately once a week
        if randint(0, 7 * 60 * 60 * 24 - 1) == 1:
            value = normalvariate(0, 1)
        else:
            value = 100
        yield datetime.fromtimestamp(timestamp), value

def groupby_day(iterable):
    """for each day, it will collects all outputs of `iterable` into a list.
    This only works if items coming from `iterable` are in ascending day order."""
    get_key = lambda row: row[0].day
    for day, data_group in groupby(iterable, get_key):
        # yield list(data_group)
        yield day, list(data_group)




if __name__ == "__main__":

    # get a stream of data/
    fake_data_generator = read_fake_data("dummy")
    for counter,data_tuple in enumerate(fake_data_generator):
        print(data_tuple)
        # >>> (datetime.datetime(1970, 1, 1, 1, 0), 100)
        if counter==10:
            break

    # iterator that returns items for each day. It only works if the stream is sorted by ascending day
    groupby_generator = groupby_day(read_fake_data("dummy"))
    for counter,data_tuple in enumerate(groupby_generator):
        print(data_tuple[0],len(data_tuple[1]))
        # >>> (datetime.datetime(1970, 1, 1, 1, 0), 100)
        if counter==10:
            break




    

