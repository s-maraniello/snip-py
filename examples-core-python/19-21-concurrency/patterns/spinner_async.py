# spinner_async.py

# credits: Example by Luciano Ramalho inspired by
# Michele Simionato's multiprocessing example in the python-list:
# https://mail.python.org/pipermail/python-list/2009-February/675659.html

# tag::SPINNER_ASYNC_TOP[]
import asyncio
import itertools


async def spin(msg: str) -> None:
    # w.r.t. threading and multiprocessing, we don't need to have a 3rd variable to monitor the 
    # state of the `slow` function.
    
    for char in itertools.cycle(r'\|/-'):
        status = f'\r{char} {msg}'
        print(status, flush=True, end='')

        try:
            # instead of time.sleep, which would instead block other coroutines.
            await asyncio.sleep(.1)
        except asyncio.CancelledError:
            # the Task controlling this coroutine will raise a CancelledError when is time to stop.
            break
    blanks = ' ' * len(status)
    print(f'\r{blanks}\r', end='')


async def slow() -> int:
    # If we were to use time.sleep, given that we are in a single thread, we would stop also other
    # coroutines. As such, we would not see any print from 'spin`.
    await asyncio.sleep(3)
    # uncomment below to see buggy behavior
    # import time 
    # time.sleep(3)
    return 42


def main() -> None:  # <1>
    # This is the only normal function. We use it to call the `asyncio.run` that will start the 
    # "event loop" that will drive the coroutine(s)
    result = asyncio.run(supervisor())
    print(f'Answer: {result}')

async def supervisor() -> int:
    # This is a native coroutine (await). The event loop is already created when we will call this
    # function. 

    # We create a task that control the spin coroutine. The spin function is already started at this
    # point. GIL will not block execution of this function, so we go to the next line of code.
    spinner = asyncio.create_task(spin('thinking!'))
    print(f'spinner object: {spinner}')
    
    # We now call a slow function, and we ask the code to wait for it to be finished. 
    # Note that:
    # if you replace `result = await slow()` with `result = slow()`, the code will crash, cause the
    # coroutine was never awaited. If you had not defined slow as a coroutine, it would continue. 
    # In this case, however, you will no tbe able to use asyncio.sleep. Instead, you would need to
    # use time.sleep, which will block the whole python process (including `spinner`, meaning that
    # the progress update will block)
    result = await slow() 
    # result = slow()

    # Now that slow has terminated, I cancel the spinner task. This will raise a CancelledError 
    # within the coroutine spin, which will then terminate.
    spinner.cancel()

    # Now that everything is closed, I can return the output.
    return result

if __name__ == '__main__':
    main()
# end::SPINNER_ASYNC_START[]