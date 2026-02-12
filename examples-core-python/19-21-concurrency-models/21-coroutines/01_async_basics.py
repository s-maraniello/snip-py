"""
SCRIPT 1: Async Basics - Awaitability, create_task, and gather

This script demonstrates:
- The concept of AWAITABILITY: what can be awaited and why
- Difference between `await coro()` (delegation) vs `asyncio.create_task(coro())` (scheduling)
- Using asyncio.gather() to run multiple coroutines concurrently
- A practical example: checking multiple domains with a spinner animation

Key Terminology:
- COROUTINE: A function defined with `async def`. When called, returns a coroutine object (not executed yet!)
- AWAITABLES: Objects that can be used with `await` - coroutines, Tasks, and Futures
- TASK: A wrapper around a coroutine that schedules it for execution in the event loop
- DELEGATION: Using `await` yields control to the event loop until the awaitable completes
- EVENT LOOP: The core of asyncio - a scheduler that runs coroutines, switches between them, and handles I/O

IMPORTANT - The GIL Misconception:
────────────────────────────────────
Async/await does NOT "release the GIL"! This is a common misunderstanding.

What actually happens:
- All async code runs in a SINGLE THREAD → The GIL is held the entire time
- We're doing COOPERATIVE MULTITASKING, not parallel execution
- When you `await`, you YIELD CONTROL to the event loop (not release GIL)
- The event loop switches to another coroutine (still in same thread, still holding GIL)
- Think of it like: "I'm waiting for something, you can work on other tasks while I wait"

GIL is only relevant for MULTI-THREADING:
- Multiple threads compete for the GIL
- Only one thread executes Python bytecode at a time
- Threads release GIL during I/O operations (time.sleep, network calls)
- That's when another thread can grab the GIL and run

Async vs Threading:
┌─────────────────────────────────────────────────────────────┐
│ THREADING (GIL matters)           │ ASYNC (GIL irrelevant)  │
├───────────────────────────────────┼─────────────────────────┤
│ Multiple threads                  │ Single thread           │
│ OS switches threads (preemptive)  │ Event loop switches     │
│ GIL released during I/O           │ GIL held always         │
│ Parallel waiting for I/O          │ Concurrent via yield    │
└───────────────────────────────────┴─────────────────────────┘
"""

import asyncio
import itertools
from typing import List


# ============================================================================
# CONCEPT: What happens when we `await` vs when we `create_task`
# ============================================================================

async def fetch_domain(domain: str, delay: float = 1.0) -> dict:
    """
    Simulates checking if a domain is available by 'fetching' it (with a fake delay).
    
    In a real scenario, this would be:
        async with httpx.AsyncClient() as client:
            response = await client.get(f'https://{domain}')
            return {'domain': domain, 'status': response.status_code}
    
    IMPORTANT: This function is a COROUTINE. When you call fetch_domain('example.com'), it doesn't execute!
    It returns a coroutine object that must be awaited or scheduled as a Task.
    """
    print(f'  🔍 Checking {domain}...')
    
    # ═══════════════════════════════════════════════════════════════════════════════════════
    # WHAT HAPPENS WHEN WE await asyncio.sleep(delay):
    # ═══════════════════════════════════════════════════════════════════════════════════════
    # 1. This coroutine YIELDS CONTROL to the event loop (it says "I'm waiting, do other work")
    # 2. The event loop marks this coroutine as "sleeping for `delay` seconds"
    # 3. The event loop looks for OTHER coroutines that are ready to run
    # 4. It switches to one of them (e.g., the spinner coroutine)
    # 5. After `delay` seconds, the event loop wakes this coroutine back up
    # 6. This coroutine continues from where it left off (next line after await)
    #
    # IMPORTANT: We're NOT "releasing the GIL" - we're in ONE THREAD!
    # We're doing COOPERATIVE MULTITASKING: voluntarily yielding via `await`
    # The event loop is like a traffic controller switching between waiting tasks
    # ═══════════════════════════════════════════════════════════════════════════════════════
    await asyncio.sleep(delay)
    
    # Simulate the result
    status = 200 if delay < 2.0 else 404
    result = {'domain': domain, 'status': status, 'available': status == 404}
    
    print(f'  ✅ {domain}: {status}')
    return result


async def spin_while_working(msg: str) -> None:
    """
    A spinner coroutine that runs until cancelled.
    
    This demonstrates that multiple coroutines can run "concurrently" in the same thread.
    When fetch_domain() awaits asyncio.sleep(), control returns to the event loop,
    which can then run this spinner coroutine.
    
    THE EVENT LOOP IN ACTION:
    ┌─────────────────────────────────────────────────────────────────────┐
    │ Time │ What the Event Loop is Doing                                 │
    ├──────┼──────────────────────────────────────────────────────────────┤
    │ 0.0s │ Starts spinner coroutine → prints '\\', awaits 0.1s         │
    │      │ Spinner yields → event loop switches to fetch_domain         │
    │      │ fetch_domain prints, awaits 1.0s → yields back to loop       │
    │ 0.1s │ Spinner wakes up → prints '|', awaits 0.1s → yields          │
    │ 0.2s │ Spinner wakes up → prints '/', awaits 0.1s → yields          │
    │ 0.3s │ Spinner wakes up → prints '-', awaits 0.1s → yields          │
    │  ... │ (pattern continues)                                          │
    │ 1.0s │ fetch_domain wakes up → completes and returns                │
    │      │ Event loop cancels spinner → spinner handles CancelledError  │
    └──────┴──────────────────────────────────────────────────────────────┘
    
    All of this happens in ONE THREAD. The GIL is never released.
    The event loop just switches between coroutines that have yielded control.
    """
    for char in itertools.cycle(r'\|/-'):
        status = f'\r{char} {msg}'
        print(status, flush=True, end='')
        # Here we yield control - the event loop can switch to other coroutines
        await asyncio.sleep(0.1)


# ============================================================================
# DEMONSTRATION: await vs create_task
# ============================================================================

async def demonstrate_await_vs_task():
    """
    Shows the critical difference between:
    1. `await coro()` - DELEGATION: waits for completion before continuing
    2. `asyncio.create_task(coro())` - SCHEDULING: schedules for concurrent execution
    """
    print('\n' + '='*80)
    print('DEMO 1: Using `await` - Sequential Execution')
    print('='*80)
    
    start = asyncio.get_event_loop().time()
    
    # When we `await`, we DELEGATE to the coroutine and WAIT for it to complete.
    # The next line won't execute until this completes (1 second).
    result1 = await fetch_domain('sequential1.com', delay=1.0)
    
    # Only after the first completes does this start (another 1 second).
    result2 = await fetch_domain('sequential2.com', delay=1.0)
    
    elapsed = asyncio.get_event_loop().time() - start
    print(f'⏱️  Sequential execution took: {elapsed:.2f}s (~ 2 seconds)\n')
    
    # --------------------------------------------------------------------------
    
    print('='*80)
    print('DEMO 2: Using `create_task` - Concurrent Execution')
    print('='*80)
    
    start = asyncio.get_event_loop().time()
    
    # asyncio.create_task() wraps the coroutine in a Task and SCHEDULES it to run.
    # The function returns IMMEDIATELY - it doesn't wait for the task to complete.
    task1 = asyncio.create_task(fetch_domain('concurrent1.com', delay=1.0))
    task2 = asyncio.create_task(fetch_domain('concurrent2.com', delay=1.0))
    
    # Both tasks are now running concurrently! We can await them to get results.
    # These awaits will complete almost simultaneously (both ~1 second, not 2).
    result1 = await task1
    result2 = await task2
    
    elapsed = asyncio.get_event_loop().time() - start
    print(f'⏱️  Concurrent execution took: {elapsed:.2f}s (~ 1 second)\n')


# ============================================================================
# PRACTICAL EXAMPLE: Batch domain checking with spinner
# ============================================================================

async def check_domains_with_spinner(domains: List[str]) -> List[dict]:
    """
    Demonstrates using create_task for a background spinner while gathering results from multiple coroutines.
    
    KEY PATTERN: asyncio.gather() accepts multiple awaitables and returns their results as a list.
    It runs them concurrently and waits for ALL to complete.
    """
    print('\n' + '='*80)
    print(f'Checking {len(domains)} domains with spinner...')
    print('='*80)
    
    # Start the spinner as a background Task. We don't await it yet - it runs in the background.
    spinner_task = asyncio.create_task(spin_while_working('Fetching domains'))
    
    try:
        # asyncio.gather() runs all coroutines CONCURRENTLY and waits for ALL to complete.
        # It returns results in the SAME ORDER as the input coroutines (important!).
        #
        # Note: We're passing coroutine objects (fetch_domain() calls) directly to gather.
        # We could have created Tasks first, but gather() does this internally.
        results = await asyncio.gather(
            *[fetch_domain(domains[ii], delay=1.0 + 0.5*ii) for ii in range(len(domains))]
        )
        
        return results
        
    finally:
        # Cancel the spinner (raises CancelledError inside the coroutine)
        spinner_task.cancel()
        
        # Wait for cancellation to complete (avoids warnings)
        try:
            await spinner_task
        except asyncio.CancelledError:
            pass
        
        print()  # New line after spinner


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def main():
    """
    The main coroutine that orchestrates our demonstrations.
    
    This is called by asyncio.run(), which:
    1. Creates a NEW event loop
    2. Runs the coroutine until completion
    3. Closes the event loop
    """
    print('\n' + '='*80)
    print('LEARNING ASYNC PYTHON: The Basics')
    print('='*80)
    
    # Demo 1 & 2: Understanding await vs create_task
    await demonstrate_await_vs_task()
    
    # Demo 3: Practical example with multiple domains
    domains = ['python.org', 'github.com', 'stackoverflow.com', 'reddit.com']
    results = await check_domains_with_spinner(domains)
    
    print('\n' + '='*80)
    print('RESULTS')
    print('='*80)
    for result in results:
        status = '✅ Available' if result['available'] else '❌ Taken'
        print(f"{result['domain']:25s} - {status} (HTTP {result['status']})")

if __name__ == '__main__':
    # asyncio.run() creates the event loop and runs our main coroutine.
    # This is the ONLY non-async function - everything else is async.
    # The event loop is what makes async code work - it schedules and switches between coroutines.
    asyncio.run(main())
