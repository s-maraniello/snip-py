#!/usr/bin/env python3
"""
Pattern to run concurrent jobs in a thread pool. This pattern is the same for multi-thread and 
multi-processes; however, all threads/processes must run the same task (`run_single_job` function 
in this script).

To adapt this script, look for the UPDATEME tag in the document. The changes required are:
- Update JobInputs and JobOutputs attributes.
- Update run_single_job to use do whatever it is that you need to do.

Note: This pattern is inspired to 
https://github.com/fluentpython/example-code-2e/blob/master/20-executors/getflags/flags2_threadpool.py
and
https://github.com/fluentpython/example-code-2e/blob/master/20-executors/demo_executor_map.py
"""

# tag::FLAGS2_THREADPOOL[]
from typing import NamedTuple
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed

import time
import random

import tqdm  # this is not a standard python library, but useful to display progress


# ---------------- Define classes to pack/unpack inputs/outputs for each job
random.seed(1263)


def run_single_task(task_number: int, exec_time_scaler=2.0, error_rate=.0) -> int:
    """This represents the task you want to run. It may be a download job. Inputs are arbitrary.

    Args:
        task_number (int): this is a dummy input.
        exec_time_scaler (float, optional): Use this to control the runtime. Defaults to 2.0.
        error_rate (float, optional): Use this to control the error rate. Defaults to .25.

    Raises:
        ValueError: A dummy error

    Returns:
        int: A dummy output. You can use this to verify the execution order.
    """

    time.sleep(exec_time_scaler * random.random())
    if random.random() < error_rate:
        raise ValueError('Task terminated with an error')

    return task_number


class JobInputs(NamedTuple):
    # UPDATEME
    task_number: int
    error_rate: float


class JobOutput(NamedTuple):
    """Store here output from each process."""
    # standard output
    inputs: JobInputs
    elapsed: float
    # UPDATEME
    task_output: int


# ------------------------------------ Function for single thread execution
def run_single_job(inputs: JobInputs) -> JobOutput:
    """This function wraps run_single_task.

    Args:
        inputs (JobInputs): Job inputs.

    Returns:
        JobOutput: Job outputs, packed in a namedTuple.
    """
    t0 = time.perf_counter()

    # If the main function you are running accepts exactly the same attributed
    # of JobInputs, you can pass all items as keywords arguments, or, if arguments
    # order is preserved, you can use `*inputs`.
    # res = check_is_prime(*inputs)
    # UPDATEME
    task_output = run_single_task(**inputs._asdict())
    # UPDATEME
    return JobOutput(inputs, time.perf_counter() - t0, task_output)


def display(*args):
    """Print whatever arguments received, preceded by timestamp."""
    print(time.strftime('[%H:%M:%S]'), end=' ')
    print(*args)


def main_no_error_handling(pool_type: str = 'multiprocess', max_workers=3, error_rate=0.0):
    """Execute multiple jobs using a pool of processors or threads. This is the simpliest 
    implementation of a pool, using `executor.map`. Features:
    - Results are mapped in the same order as the inputs.
    - No error handling.
    - Jobs can only execute the same task.

    Args:
        pool_type (str, optional): Type of pool to use. Can be ['multithread','multiprocess']. Defaults to 'multithread'.
        max_workers (int, optional): Number of workers (either threads or processes, depending on `pool_type`). Defaults 
            to 3.
        error_rate (float, optional): How often the tasks will fail. Defaults to 0.0.  
    """

    display('Script starting.')
    t0 = time.perf_counter()

    if pool_type == 'multiprocess':
        executor = ProcessPoolExecutor(max_workers)
    elif pool_type == 'multithread':
        executor = ThreadPoolExecutor(max_workers)
    else:
        raise ValueError('`pool_type` not recognised.')

    # For large files you can pass a generator, or a process that reads/generates input data on
    # the flight.
    jobs_inputs_list = [JobInputs(task_number=n, error_rate=error_rate) for n in range(6)]

    # The executor map will allow retrieving the results in the same order as they were submitted.
    # This means that slow tasks may block the output of faster tasks that were submitted later (see
    # also below when we retrieve results).
    results = executor.map(run_single_job, jobs_inputs_list)
    display('Waiting for individual results:')

    # Display/retrieve results in same orders orders they were sent. The enumerate call in the for
    # loop will implicitly invoke next(results), which in turn will invoke _f.result() on the
    # (internal) _f future representing the first call to run_single_job. The result method will
    # block until the future is done, therefore each iteration in this loop will have to wait for
    # the next result to be ready.
    for i, result in enumerate(results):
        display(f'result {i}: {result}')

    display(f'All jobs done in {time.perf_counter()-t0:.3f}s.')


def main_error_handling(pool_type: str = 'multiprocess', max_workers=3, error_rate=0.3):
    """Execute multiple jobs using a pool of processors or threads. This implementation of a pool, 
    uses `executor.submit` and `executor.as_completed` to:
     - allow returning results as soon as they are completed;
     - error handling;
     - executing different tasks.

    Args:
        pool_type (str, optional): Type of pool to use. Can be ['multithread','multiprocess']. Defaults to 'multithread'.
        max_workers (int, optional): Number of workers (either threads or processes, depending on `pool_type`). Defaults 
            to 3.
        error_rate (float, optional): How often the tasks will fail. Defaults to 0.3.    
    """

    display('Script starting.')
    t0 = time.perf_counter()

    if pool_type == 'multiprocess':
        Executor = ProcessPoolExecutor
    elif pool_type == 'multithread':
        Executor = ThreadPoolExecutor
    else:
        raise ValueError('`pool_type` not recognised.')

    # For large files you can pass a generator, or a process that reads/generates input data on
    # the flight.
    jobs_inputs_list = [JobInputs(task_number=n, error_rate=error_rate) for n in range(6)]

    with Executor(max_workers=max_workers) as executor:

        to_do_map = {}
        for job_number, job_inputs in enumerate(jobs_inputs_list):
            # returns a concurrent.futures.Future instance, i.e. the result of an async computation.
            future_job = executor.submit(run_single_job, job_inputs)
            # we could package this in a list as well, but we would not know how to map the future
            # to the inputs, when we retrieve them.
            # Important: the key MUST be the future!
            to_do_map[future_job] = job_number

        # This iterator will yield each future job, as they complete (with a max wait of 10 sec.).
        # Note that,if to_do_map was a list, futures would not be retrieved in the same order as
        # to_do_map.
        # Note: this is an iterator, and not a dict or list. It does not depend on `to_do_map` type.
        futures_iterator = as_completed(to_do_map, timeout=20)

        # progress display using tqdm. The command consumes an iterable and produces an iterator
        # which, while it’s consumed, displays the progress bar and estimates the remaining time to
        # complete all iterations (hence the need to pass the len argument if the iterable does not
        # have a length)
        futures_iterator = tqdm.tqdm(futures_iterator, total=len(jobs_inputs_list))

        results = {}
        for future_job in futures_iterator:
            # retrieve job number associated to the future
            job_number = to_do_map[future_job]
            try:
                res = future_job.result()
            except ValueError:
                res = 'failed'

            display(f'result {job_number}: {res}')
            results[job_number] = res

    display(f'All jobs done in {time.perf_counter()-t0:.3f}s.')

    # display results in input order
    for job_number in range(len(jobs_inputs_list)):
        display(f'result {job_number}: {results[job_number]}')


if __name__ == '__main__':
    # main_no_error_handling('multithread', error_rate=0.0)

    main_error_handling('multiprocess', error_rate=0.2, max_workers=4)
