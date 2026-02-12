#!/usr/bin/env python3

"""
Multiprocessing using queues.

To adapt this script, look for the UPDATEME in the document. The updates required are:
- Update JobInputs and JobOutputs attributes.
- Update run_single_job to use do whatever it is that you need to do.
- Modify the main to read the inputs (and stuck them into a sequence/iterator of some sort)
"""

# tag::PRIMES_PROC_TOP[]
import sys
from time import perf_counter
from typing import NamedTuple

from multiprocessing import Process, cpu_count
from multiprocessing import SimpleQueue  # this is method, not a cxlass!
from multiprocessing import queues # only needed to import SimpleQueue class for type hinting

from primes import check_is_prime, PRIME_FIXTURE


##### ---------------- Define classes to pack/unpack inputs/outputs for each job

# This is the function you want to run concurrently.Allowed  inputs and outputs must serialise
# (e.g. native Python data structures)
run_single_task = check_is_prime


class JobInputs(NamedTuple):
    # UPDATEME
    n: int


class JobOutput(NamedTuple):
    """Store here output from each process."""
    # standard output
    inputs: JobInputs
    elapsed: float
    # UPDATEME
    is_prime: bool


JobInputsQueue = queues.SimpleQueue[JobInputs | int]  # int is for poison pill
JobOutputsQueue = queues.SimpleQueue[JobOutput]

# POISON_PILL must be 0 to `worker` to function correctly in some of the examples. Here we use
# the ellipsis (as using integers, or None, or else may be a legit output of the process, hence
# generating a bug).
# Another useful way to get a unique value for the poison pill / workers, is to use object(), 
# which returns a featureless instance.
POISON_PILL, WORKER_IS_DONE = ..., ...
POISON_PILL, WORKER_IS_DONE = object(), object()


##### -------------------------------------- Function for single core execution

def run_single_job(inputs: JobInputs) -> JobOutput:
    """This function allows execution on a single core. Modify

    Args:
        inputs (JobInputs): Job inputs.

    Returns:
        JobOutput: Job outputs, packed in a namedTuple.
    """
    t0 = perf_counter()

    # If the main function you are running accepts exactly the same attributed
    # of JobInputs, you can pass all items as keywords arguments, or, if arguments
    # order is preserved, you can use `*inputs`.
    # res = check_is_prime(*inputs)
    # UPDATEME
    is_prime = check_is_prime(**inputs._asdict())
    # UPDATEME
    return JobOutput(inputs, perf_counter() - t0, is_prime)


def worker(jobs: JobInputsQueue, results: JobOutputsQueue) -> None:
    """Define operations that each worker needs to do. The worker has access to queues including 
    inputs and a queue to dump the outputs. No need to modify this function.

    Args:
        jobs (JobInputsQueue): queue with jobs inputs. The queue must include a POISON_PILL, i.e. 
        a signal to indicate the worker to stop.
        results (JobOutputsQueue): queue to store outputs. When the worker has completed, it will
        add a WORKER_IS_DONE to the queue.
    """

    # This is a common pattern in concurrent programming. A worker loops indefintively across all jobs in the  queue. 
    # Each time `jobs.get()`, the jobs input are take out from the job list - this how another worker will not execute
    # the same job.
    # Eventually, jobs will be empty and the get nothing (None), so we can terminate the worker and exit the while loop. 
    # As None may be a legit out of the process (actually, in our case no, as we use JobOutput NamedTuple), we send a 
    # specific sentinel value (aka poison pill).

    while True:
        inputs = jobs.get()
        if inputs == POISON_PILL:
            # Once the worker receives the poison pill, it will send a signal that it has completed.
            results.put(WORKER_IS_DONE)
            return
        results.put(run_single_job(inputs))
    
    # This is more compact, because assumes the poison pill is 0 or False
    # while inputs := jobs.get():
    #    results.put(run_single_job(inputs))  # <9>
    # results.put(WORKER_IS_DONE)


# tag::PRIMES_PROC_MAIN[]
def main() -> None:

    # set number of processes
    num_procs = cpu_count()
    if len(sys.argv) == 2:
        num_procs = int(sys.argv[1])

    # UPDATEME: Prepare inputs
    inputs_list = [JobInputs(n=n) for n, _ in PRIME_FIXTURE]
    print(f"Computing {len(inputs_list)} items on {num_procs} processes")

    t0 = perf_counter()

    # create queues for jobs and results
    jobs: JobInputsQueue = SimpleQueue()
    results: JobOutputsQueue = SimpleQueue()

    # start all jobs
    for inputs in inputs_list:
        jobs.put(inputs)
    for _ in range(num_procs):
        proc = Process(target=worker, args=(jobs, results))  # Fork a child process
        proc.start()
        jobs.put(POISON_PILL)  # For each process, remind to put a POISON PILL

    # Get results. 
    # This is also a while loop that goes on forever. As time elapses, results are retrieved.
    # Important: Results are retrieved in random order (this is why we attach the inputs to the
    # outputs).
    jobs_completed, procs_done = 0, 0
    while procs_done < num_procs:  # <7>
        res = results.get()  # <8>
        if res == WORKER_IS_DONE:  # <9>
            procs_done += 1
        else:
            jobs_completed += 1  # <10>
            msg = "P" if res.is_prime else " "
            print(f"{res.inputs.n:16}  {msg} {res.elapsed:9.6f}s")

    # start_jobs(num_procs, jobs, results, args=numbers)  # <3>
    # checked = report(num_procs, results)  # <4>
    elapsed = perf_counter() - t0
    print(f"{jobs_completed} jobs completed in {elapsed:.2f}s")  # <5>


if __name__ == "__main__":

    # inputs = JobInputs(17)
    # print(run_single_job(inputs))

    main()
# end::PRIMES_PROC_MAIN[]
