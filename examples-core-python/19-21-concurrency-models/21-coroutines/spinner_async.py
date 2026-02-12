# spinner_async.py

# credits: Example by Luciano Ramalho inspired by
# Michele Simionato's multiprocessing example in the python-list:
# https://mail.python.org/pipermail/python-list/2009-February/675659.html

# tag::SPINNER_ASYNC_TOP[]
from ast import If
import asyncio
import itertools
import time


async def spin(msg: str) -> None:
    """
    An async function that "runs forever" until it is cancelled. It prints a message with a spinner animation.

    XXX. The `spin` function is not a thread, but a coroutine. It will run in the same thread as other coroutines,
    but it will only run when the control is delegated to the event loop (e.g., when we await something). 
    """
    # w.r.t. threading and multiprocessing, we don't need to have a 3rd variable to monitor the state of the `slow`
    # function.
    
    for char in itertools.cycle(r'\|/-'):
        status = f'\r{char} {msg}'
        print(status, flush=True, end='')

        try:
            # Delegate control to the event loop (which can let other coroutines run). 
            # In real apps, this would be: await client.get(url), await db.query(), etc.
            # XXX. If we were to use time.sleep, we would block this function, including the for loop and the spinner 
            # animation! This is because we would not be relesing control of the execution to the event loop, and we would
            # be waiting for the time to elapse.
            # XXX. Importantly, this for loop would never terminate.
            # await time.sleep(.15)
            await asyncio.sleep(.15)
        except asyncio.CancelledError:
            # The Task controlling this coroutine will raise a CancelledError when it's time to stop.
            break
    blanks = ' ' * len(status)
    print(f'\r{blanks}\r', end='')


async def slow() -> int:
    # If we were to use time.sleep, given that we are in a single thread, we would stop also other coroutines.
    # As such, we would not see any print from 'spin`.
    await asyncio.sleep(3)
    # Uncomment below to see buggy behavior:
    # import time
    # time.sleep(3)
    return 42


def main() -> None:
    # This is the only normal function. We use it to call `asyncio.run` that will start the "event loop" that will
    # drive the coroutine(s).
    # XXX. If we had called `supervisor()` instead of `asyncio.run(supervisor())`, the code would have crashed because
    # `supervisor` is a coroutine and it needs to be awaited. 
    # XXX. If we had called `asyncio.run(supervisor())` directly in the global scope (i.e. after __name__ == '__main__'), 
    # it would have not worked.
    result = asyncio.run(supervisor())
    print(f'Answer: {result}')


async def supervisor() -> int:
    # This is a native coroutine (await). The event loop is already created when we call this function.

    # We create a task that controls the spin coroutine. The spin function is already started at this point.
    # XXX. The execution is managed by the event.loop, that will progress on this task while also progressing on other coroutines. 
    # XXX. As such, we can nmove to the next lines of code.
    # XXX. If we had called `await spin('thinking!')` instead, the code would have blocked until the completion of
    # the spin function, which in this case is never. This is because we would have told the event loop to complete the
    # execution of the spin function before moving to the next line of code.
    # XXX. if we had called just `spin('thinking!')` instead, the code would have started the coroutine, but since
    # it was never awaited anywhere else in the code, the event loop would have never bothered executing it.
    spinner = asyncio.create_task(spin('thinking!'))
    print(f'spinner object: {spinner}')
    

    # Delegate
    # 
    # We now delegate execution to another corotutine. The execution will block until the `slow` function completes. 
    # XXX. The execution of this function will block until `slow` completes. 
    # XXX. if you replace `result = await slow()` with `result = slow()`, the code will crash because the coroutine
    # was never awaited. 
    #     * If we redefined `slow` not to be a coroutine, instead, slow would be executed, but blocking the whole 
    #       execution.
    result = await slow()
    # result = slow()

    # Now that slow has terminated, I cancel the spinner task. This will raise a CancelledError within the coroutine
    # spin, which will then terminate.
    spinner.cancel()

    # Now that everything is closed, I can return the output.
    return result

if __name__ == '__main__':
    main()