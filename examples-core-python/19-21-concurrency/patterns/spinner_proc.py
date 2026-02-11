import itertools
import time
from multiprocessing import Process
from multiprocessing import Event       # w.r.t. threading, Event now is a function (not a class)...
from multiprocessing import synchronize # ... that returns a synchronize.Event instance


def spin(msg: str, done: synchronize.Event) -> None:
    # Aside for signature, the rest of spin functions is unchanged from previous example

    refresh_rate = 0.1

    # Progress function. Will run in process 1.
    for char in itertools.cycle(r'\|/-'):
        # The `\r` moves cursor back at beginning of the start of the line
        status = f'\r{char} {msg}' 
        print(status, end='', flush=True) 

        # Check if other process is ready.
        # - Wait effectively blocks this process (hence the function) for some time.
        # - The process is stopped for a maximum of `refresh rate` seconds.
        # - Unless some other process sets the Event to True in the meanwhile, execution resumes.
        # - the fact that the process stops for a while is what allows us to see the animation, else
        #   the spin would spin too fast!
        if done.wait(refresh_rate):
            break
    blanks = ' ' * len(status) 
    print(f'\r{blanks}\r', end='')


def slow() -> int: 
    # A slow to execute function that is releasing the GIL (e.g. writing I/O).
    # Will run in process 2.
    time.sleep(3)
    return 1


def supervisor() -> int: 
    
    # Create an event to signal when the slow process is completed.
    # - Initially, done is False
    # - Note. This must be an instance of Event. If you replace with a simple bool, the spinner
    #   process will start, but will never complete.
    done = Event() 

    # Create (and start) a different process to show the progress.
    # - We specify which function is executed in the process, as well as its arguments.
    # - One of the arguments is the `done` event, that will allow us to signal when the process must
    #   be closed
    spinner = Process(target=spin, args=('thinking!', done))
    print(f'spinner object: {spinner}')
    spinner.start()

    # Now we start a slow operation in the current process. 
    # - This operation is formally blocking the main process.
    # - T spinner process is already running in the background, instead.
    result = slow()

    # Once result is available, I can change the event status.
    # - The spin function will terminate as soon as it sees `done is True`
    done.set()

    # In fact, the spinner process does not terminate instantly (as it checks for `done` being True
    # only every x seconds). Hence, with this command I officially tell the main process to wait for 
    # spinner process to terminate, before continuing.
    spinner.join() 

    # Now that spinner is closed, I can terminate the function and return the outcome.
    return result



if __name__ == '__main__':
    supervisor()