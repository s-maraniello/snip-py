"""
SCRIPT 4: Async vs Threads - When to Use What?

This script addresses the "ALL OR NOTHING" problem and provides guidance on choosing between:
- Async/await (asyncio)
- Threading
- Multiprocessing

Key Questions Answered:
1. Why is async "all or nothing"? (The Async Color Problem)
2. When should I use async vs threads?
3. For the domain-checking example, which is better?
4. How do I integrate async code with synchronous libraries?
5. What about CPU-bound work?

===============================================================================
THE "COLOR" PROBLEM: Why Async is All-or-Nothing
===============================================================================

In async, functions are "colored" - they're either async (red) or sync (blue).
- Red functions (async) can only be called by other red functions
- Blue functions (sync) can call blue functions
- Red functions can call blue, but blue CANNOT call red directly
This is the "all or nothing" problem - once you go async, everything above must be async too!

❌ PROBLEM: Cannot call async function from sync code directly

Imagine you have an existing synchronous codebase:

    def my_existing_function():
        result = fetch_data_from_db()  # sync function
        processed = process_data(result)  # sync function
        return processed

Now you want to add an async API call:

    def my_existing_function():
        result = fetch_data_from_db()  # sync
        
        # ❌ CANNOT DO THIS - fetch_from_api_async() returns a coroutine!
        api_data = fetch_from_api_async()  
        
        # ❌ CANNOT DO THIS - await only works in async functions!
        # api_data = await fetch_from_api_async()
        
        processed = process_data(result)
        return processed

✅ SOLUTIONS:

1. Make EVERYTHING async (hence "all or nothing"):

    async def my_existing_function():  # Now async!
        result = await fetch_data_from_db_async()  # Need async version
        api_data = await fetch_from_api_async()  # Now works!
        processed = await process_data_async(result)  # Need async version
        return processed

   Problem: Requires rewriting fetch_data_from_db, process_data, etc.
   This cascades up - every caller must also become async!

2. Use asyncio.to_thread() or run_in_executor() (hybrid approach):

    async def my_existing_function():
        # Run sync function in thread pool
        result = await asyncio.to_thread(fetch_data_from_db)
        
        # Async call works naturally
        api_data = await fetch_from_api_async()
        
        processed = await asyncio.to_thread(process_data, result)
        return processed

   Better: Can mix sync and async, but still need async at top level

3. Use asyncio.run() to call async from sync (creates new event loop):

    def my_existing_function():
        result = fetch_data_from_db()  # sync
        
        # Create event loop and run async function
        api_data = asyncio.run(fetch_from_api_async())
        
        processed = process_data(result)
        return processed

   ⚠️  Problem: Cannot call asyncio.run() if already in async context!
   Only works at boundaries (sync → async entry point)

===============================================================================
UNDERSTANDING: The GIL and Event Loop (COMMON MISCONCEPTIONS!)
===============================================================================

❌ MISCONCEPTION: "Async releases the GIL to achieve concurrency"
✅ REALITY: Async has NOTHING to do with the GIL!

───────────────────────────────────────────────────────────────────────────────
WHAT IS THE GIL (Global Interpreter Lock)?
───────────────────────────────────────────────────────────────────────────────

The GIL is a mutex (lock) that protects access to Python objects, preventing 
multiple threads from executing Python bytecode at once.

Key points about the GIL:
• Only relevant for MULTI-THREADING (multiple threads in one process)
• Only ONE thread can execute Python code at a time
• Threads take turns holding the GIL
• Thread releases GIL during I/O operations (network, file, sleep)
• Other threads can grab the GIL when it's released
• This is why threading works for I/O-bound work (threads wait, not compute)
• But threading is BAD for CPU-bound work (only one thread computes at a time)

┌─────────────────────────────────────────────────────────────────────┐
│ THREADING WITH GIL:                                                 │
│                                                                     │
│ Thread 1: [████ GIL] → I/O (releases) → waits → [████ GIL] → ...    │
│ Thread 2:            waits → [████ GIL] → I/O (releases) → ...      │
│ Thread 3:                   waits → [████ GIL] → ...                │
│                                                                     │
│ • Threads COMPETE for the GIL                                       │
│ • Only one runs Python code at a time                               │
│ • Others wait or do I/O (when GIL is released)                      │
└─────────────────────────────────────────────────────────────────────┘

───────────────────────────────────────────────────────────────────────────────
WHAT IS THE EVENT LOOP?
───────────────────────────────────────────────────────────────────────────────

The event loop is asyncio's SCHEDULER that manages coroutines in a SINGLE thread.

Key points about the event loop:
• Runs in ONE THREAD - no parallelism, just concurrency
• Maintains queues of: ready tasks, sleeping tasks, waiting tasks
• When a coroutine hits `await`, it YIELDS control to the event loop
• Event loop picks another ready coroutine to run
• Eventually returns to the first coroutine when it's ready
• This is COOPERATIVE MULTITASKING - coroutines voluntarily yield
• No GIL competition because there's only ONE THREAD!

┌─────────────────────────────────────────────────────────────────────┐
│ ASYNC WITH EVENT LOOP (Single Thread):                               │
│                                                                       │
│ Time 0.0: [Coro 1 runs] → awaits (yields) →                         │
│ Time 0.0:   └→ [Event Loop] picks next → [Coro 2 runs] → awaits →   │
│ Time 0.1:      └→ [Event Loop] picks next → [Coro 3 runs] → awaits →│
│ Time 0.1:         └→ [Event Loop] checks timers → [Coro 1 ready] →  │
│ Time 0.2: [Coro 1 continues] → ...                                   │
│                                                                       │
│ • All happens in ONE THREAD                                          │
│ • GIL is held the ENTIRE time                                        │
│ • Coroutines cooperatively share the thread via `await`              │
│ • No GIL contention, no thread switching overhead                    │
└─────────────────────────────────────────────────────────────────────┘

───────────────────────────────────────────────────────────────────────────────
KEY DIFFERENCES: THREADING vs ASYNC
───────────────────────────────────────────────────────────────────────────────

┌────────────────────────┬─────────────────────────┬────────────────────────┐
│ Aspect                 │ Threading               │ Async                  │
├────────────────────────┼─────────────────────────┼────────────────────────┤
│ Number of threads      │ Multiple                │ Single                 │
│ Concurrency mechanism  │ OS preemptive switching │ Cooperative yielding   │
│ GIL relevance          │ CRITICAL - bottleneck   │ IRRELEVANT - one thread│
│ Switching control      │ OS decides when         │ Coroutine decides when │
│ Overhead               │ Higher (thread context) │ Lower (function calls) │
│ When threads/coros run │ OS interrupts threads   │ await yields control   │
│ Can block event loop?  │ N/A                     │ Yes! (if no await)     │
│ Best for               │ I/O + existing sync code│ I/O + high concurrency │
└────────────────────────┴─────────────────────────┴────────────────────────┘

───────────────────────────────────────────────────────────────────────────────
SO WHY DOES ASYNC WORK?
───────────────────────────────────────────────────────────────────────────────

Async achieves concurrency WITHOUT needing to release the GIL because:

1. It's all in ONE THREAD → No GIL competition → No waiting for GIL
2. When awaiting I/O, the coroutine yields to event loop
3. Event loop switches to another coroutine (just a function call!)
4. No OS thread switching overhead
5. Can handle THOUSANDS of concurrent operations efficiently

The key insight:
• THREADING: Concurrency via multiple threads fighting over GIL
• ASYNC: Concurrency via one thread voluntarily yielding control

Both work for I/O-bound tasks, but async is more efficient because:
• No thread creation/destruction overhead
• No GIL contention
• No OS context switching
• Lower memory per "concurrent task" (coroutine vs thread)

───────────────────────────────────────────────────────────────────────────────
WHEN THE GIL MATTERS:
───────────────────────────────────────────────────────────────────────────────

✅ GIL matters for THREADING:
   • Multiple threads compete for the GIL
   • Only one thread executes Python code at a time
   • Great for I/O (threads release GIL during I/O)
   • Terrible for CPU work (threads wait for GIL)

❌ GIL doesn't matter for ASYNC:
   • Single thread → GIL held continuously
   • No competition, no contention
   • Concurrency via yielding, not parallelism
   • Still terrible for CPU work (blocks the single thread)

✅ GIL doesn't matter for MULTIPROCESSING:
   • Separate processes → Separate Python interpreters
   • Each process has its own GIL
   • True parallelism for CPU-bound work
   • But high overhead for inter-process communication

───────────────────────────────────────────────────────────────────────────────
⚠️  CRITICAL CLARIFICATION: Threading and CPU-Bound Work
───────────────────────────────────────────────────────────────────────────────

❌ COMMON MISCONCEPTION:
"I can use asyncio.to_thread() to run CPU-intensive work without blocking"

✅ REALITY: For PURE PYTHON CPU-intensive work, threading provides NO speedup!

Why? Because of the GIL:

    # Two CPU-intensive functions
    def compute_fibonacci(n):  # Pure Python CPU work
        # ... lots of Python calculations ...
    
    # Sequential execution: 10 seconds
    compute_fibonacci(35)  # 5 seconds
    compute_fibonacci(35)  # 5 seconds
    
    # With threading: STILL ~10 seconds (or worse!)
    with ThreadPoolExecutor() as executor:
        future1 = executor.submit(compute_fibonacci, 35)
        future2 = executor.submit(compute_fibonacci, 35)
        # Both compete for GIL, run one at a time
        # Plus: context switching overhead!

The threads compete for the GIL and execute essentially sequentially.
Total time = same or WORSE due to context switching overhead.

✅ WHEN TO USE asyncio.to_thread() or ThreadPoolExecutor:

1. **BLOCKING I/O** (no async version available):
   • File I/O: open(), read(), write()
   • Synchronous database calls (psycopg2, sqlite3)
   • Requests library (requests.get() instead of httpx)
   • Legacy libraries without async support
   
   Why it helps: I/O operations release the GIL, allowing other threads to run

2. **CPU work that RELEASES the GIL**:
   • NumPy operations: np.dot(), np.linalg.solve()
   • Pandas operations: df.groupby(), df.merge()
   • C extensions and compiled libraries
   • Image processing: Pillow, OpenCV
   • Scientific computing: SciPy, scikit-learn
   
   Why it helps: These libraries release the GIL during computation

3. **NOT for pure Python CPU work**:
   • List comprehensions
   • Pure Python loops and calculations
   • String processing
   • Dictionary operations
   
   Solution for these: Use multiprocessing, not threading!

📊 EXAMPLE: When threading helps vs doesn't help

    # ❌ Threading does NOT help here (pure Python CPU):
    def pure_python_calculation(n):
        total = 0
        for i in range(n):
            total += i ** 2  # Pure Python, holds GIL
        return total
    
    # ✅ Threading DOES help here (releases GIL):
    import numpy as np
    def numpy_calculation(n):
        arr = np.arange(n)
        return np.sum(arr ** 2)  # NumPy releases GIL

✅ FOR TRUE CPU PARALLELISM: Use multiprocessing

    from multiprocessing import Pool
    
    with Pool() as pool:
        results = pool.map(compute_fibonacci, [35, 35])
        # Now actually runs in parallel on different cores!
        # Time: ~5 seconds instead of 10

===============================================================================
DECISION GUIDE: When to Use What?
===============================================================================

┌─────────────────────────────────────────────────────────────────────────────┐
│                     ASYNC vs THREADS vs MULTIPROCESSING                      │
└─────────────────────────────────────────────────────────────────────────────┘

🔹 USE ASYNC (asyncio) WHEN:
   ✅ I/O-bound work (network requests, disk I/O)
   ✅ Many concurrent operations (100s or 1000s)
   ✅ Starting new project or using async-native libraries
   ✅ Need precise control over concurrency
   ✅ Low overhead is critical
   
   ❌ BUT NOT WHEN:
   ⚠️  Working with sync-only libraries (no async version available)
   ⚠️  Small codebase where threading is simpler
   ⚠️  Team unfamiliar with async patterns

🔹 USE THREADING WHEN:
   ✅ I/O-bound work with existing synchronous code
   ✅ Modest concurrency needs (< 100 concurrent operations)
   ✅ Need to integrate with sync-only libraries
   ✅ Want simple parallel execution without rewriting code
   ✅ Codebase is already synchronous
   
   ❌ BUT NOT WHEN:
   ⚠️  CPU-bound work (GIL limits to single core)
   ⚠️  Need 1000s of concurrent operations (thread overhead)

🔹 USE MULTIPROCESSING WHEN:
   ✅ CPU-bound work (calculations, data processing)
   ✅ Need to utilize multiple CPU cores
   ✅ Can parallelize independent chunks of work
   ✅ Willing to handle IPC overhead
   
   ❌ BUT NOT WHEN:
   ⚠️  I/O-bound work (unnecessary overhead)
   ⚠️  Shared state is complex (IPC is expensive)
   ⚠️  High process creation overhead is a concern

───────────────────────────────────────────────────────────────────────────────
📊 FOR THE DOMAIN CHECKING EXAMPLE:

Q: Should we use async or threads?
A: EITHER works well! Here's why:

   Async is IDEAL because:
   • I/O-bound operation (network requests)
   • May need to check 1000s of domains
   • Modern HTTP libraries support async (httpx, aiohttp)
   • Lower resource usage for many connections
   
   Threading is ACCEPTABLE because:
   • Works with standard requests library (no rewrite)
   • Easier for teams unfamiliar with async
   • Domain checking usually isn't 1000s at once
   • Simpler error handling and debugging
   
   Verdict for this example: 
   🏆 ASYNC wins for scalability, THREADING wins for simplicity

───────────────────────────────────────────────────────────────────────────────
💡 HYBRID APPROACH (Best of Both Worlds):

   Use async as the main framework, but integrate sync code with:
   
   • asyncio.to_thread(sync_func, args) - Run blocking I/O in thread pool
   • loop.run_in_executor() - More control over executor
   
   Example:
   
       async def hybrid_example():
           # Async I/O
           data = await async_fetch_from_api()
           
           # Blocking I/O in thread (e.g., sync database, file I/O)
           # OR: CPU work that releases GIL (NumPy, Pandas, etc.)
           result = await asyncio.to_thread(blocking_sync_function, data)
           
           # Async database write
           await async_save_to_db(result)
   
   ⚠️  NOTE: asyncio.to_thread() does NOT help with pure Python CPU work!
            For CPU parallelism, use multiprocessing instead.

===============================================================================
PRACTICAL PATTERNS: Dealing with the All-or-Nothing Problem
===============================================================================

PATTERN 1: Async Wrapper Around Sync Library
──────────────────────────────────────────────────────────────
Problem: Want to use requests (sync) in async code

Solution:

    import asyncio
    import requests

    async def fetch_url_async(url: str) -> str:
        # Run the blocking requests.get() in a thread pool
        response = await asyncio.to_thread(requests.get, url)
        return response.text

    # Now can use like: data = await fetch_url_async('https://...')

When to use: Have sync library, need async interface


PATTERN 2: Sync Wrapper Around Async Function  
──────────────────────────────────────────────────────────────
Problem: Want to use async library from sync code

Solution:

    import asyncio
    import httpx

    async def fetch_async(url: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            return response.text

    def fetch_sync(url: str) -> str:
        return asyncio.run(fetch_async(url))

    # Now can use like: data = fetch_sync('https://...')

⚠️  Warning: Cannot use asyncio.run() inside existing event loop!
When to use: Entry point from sync to async


PATTERN 3: Gradual Migration to Async
──────────────────────────────────────────────────────────────
Problem: Large sync codebase, want to migrate to async

Strategy:
1. Start at the "leaves" (I/O functions)
2. Make them async
3. Gradually move up the call stack
4. Use hybrid approach at boundaries

Example:

    # Step 1: Convert I/O functions
    async def fetch_data_async():
        ...

    # Step 2: Convert functions that call them  
    async def process_data_async():
        data = await fetch_data_async()
        ...

    # Step 3: At boundary, keep sync with wrapper
    def legacy_sync_function():
        # Still sync, uses thread pool
        return asyncio.run(process_data_async())


PATTERN 4: Mixing Async and Threads (Hybrid)
──────────────────────────────────────────────────────────────
Problem: Some operations are async-friendly, others aren't

Solution:

    async def hybrid_pipeline():
        # Async I/O (network)
        data = await fetch_from_api_async()
        
        # Blocking I/O in thread pool (e.g., sync file I/O)
        await asyncio.to_thread(write_to_file, data)
        
        # GIL-releasing work in thread pool (e.g., NumPy)
        processed = await asyncio.to_thread(numpy_heavy_computation, data)
        
        # Async database
        await save_to_database_async(processed)

⚠️  When to use: 
    • Blocking I/O without async version
    • CPU work that releases GIL (NumPy, Pandas, C extensions)
    
⚠️  NOT for:
    • Pure Python CPU work (use multiprocessing instead)
    • Operations that already have async versions


PATTERN 5: Running Multiple Async Functions from Sync
──────────────────────────────────────────────────────────────
Problem: Need to call multiple async functions from sync code

Solution:

    async def async_main():
        # Gather all async work
        results = await asyncio.gather(
            fetch_async('url1'),
            fetch_async('url2'),
            fetch_async('url3'),
        )
        return results

    def sync_entry_point():
        # Single sync → async boundary
        return asyncio.run(async_main())

Key: Single asyncio.run() call, async coordination inside

===============================================================================
KEY TAKEAWAYS
===============================================================================

1. THE COLOR PROBLEM: Async is "all or nothing"
   • Async functions can only be called by async functions
   • This cascades up the call stack
   • Solution: Use hybrid approach with asyncio.to_thread()

2. THE GIL MISCONCEPTION:
   • Async does NOT release the GIL - it's not about the GIL at all!
   • Async runs in ONE THREAD with the GIL held the entire time
   • Concurrency via COOPERATIVE YIELDING (await), not GIL release
   • GIL only matters for THREADING (multiple threads competing)
   • This is why async is more efficient than threading (no GIL contention)

3. THE EVENT LOOP:
   • A scheduler that runs in a single thread
   • Switches between coroutines when they yield (await)
   • Maintains ready, sleeping, and waiting tasks
   • Creates concurrency through rapid context switching, not parallelism

4. ASYNC vs THREADS for I/O:
   • Async: Better for 100s/1000s of connections, lower overhead, no GIL contention
   • Threads: Works with existing sync code, simpler to understand
   • Both are valid for I/O-bound work!

5. DOMAIN CHECKING EXAMPLE:
   • Async is ideal (I/O-bound, scalable)
   • Threading is acceptable (simpler, good enough for modest scale)
   • Choose based on scale and team familiarity

6. HYBRID APPROACH:
   • Async for I/O-bound coordination
   • asyncio.to_thread() for BLOCKING I/O (not pure Python CPU work!)
   • For CPU parallelism: Use multiprocessing, not threading

7. CRITICAL: Threading does NOT speed up pure Python CPU work!
   • GIL ensures only one thread executes Python code at a time
   • Threading helps with I/O (releases GIL) or GIL-releasing libraries (NumPy)
   • For CPU parallelism: multiprocessing only

8. WHEN IN DOUBT:
   • Starting new → Consider async from the start
   • Existing codebase → Threading or hybrid approach
   • Need 1000s of connections → Definitely async
   • CPU-bound work → Multiprocessing, not async or threads

===============================================================================
"""

import asyncio
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
import random


# ============================================================================
# DOMAIN CHECKING: Implemented THREE ways
# ============================================================================

# 1. SYNCHRONOUS VERSION (baseline)
def fetch_domain_sync(domain: str) -> Dict:
    """Traditional synchronous function - blocks while waiting."""
    time.sleep(1.0)  # Simulates network I/O
    return {'domain': domain, 'status': 200}


# 2. ASYNC VERSION
async def fetch_domain_async(domain: str) -> Dict:
    """Async version - yields control during I/O."""
    await asyncio.sleep(1.0)  # Simulates network I/O
    return {'domain': domain, 'status': 200}


# 3. SYNC VERSION (for use with threads)
# (Same as #1 - threads can run regular sync functions)


# ============================================================================
# PERFORMANCE COMPARISON: Domain Checking - Three Approaches
# ============================================================================

def synchronous_approach(domains: List[str]) -> List[Dict]:
    """Sequential synchronous approach - simple but slow."""
    results = []
    for domain in domains:
        results.append(fetch_domain_sync(domain))
    return results


def threading_approach(domains: List[str], max_workers: int = 5) -> List[Dict]:
    """Threading approach - parallel execution with threads."""
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_domain = {executor.submit(fetch_domain_sync, domain): domain for domain in domains}
        
        for future in as_completed(future_to_domain):
            results.append(future.result())
    
    return results


async def async_approach(domains: List[str], max_concurrent: int = 5) -> List[Dict]:
    """Async approach - concurrent execution with event loop."""
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def fetch_with_semaphore(domain):
        async with semaphore:
            return await fetch_domain_async(domain)
    
    return await asyncio.gather(*[fetch_with_semaphore(d) for d in domains])


def compare_approaches(domains: List[str]):
    """
    Compares the three approaches for I/O-bound work (domain checking).
    """
    print('\n' + '='*80)
    print(f'COMPARISON: Checking {len(domains)} Domains')
    print('='*80)
    
    # 1. Synchronous
    print('\n1. SYNCHRONOUS (baseline):')
    start = time.time()
    results = synchronous_approach(domains)
    sync_time = time.time() - start
    print(f'   ⏱️  Time: {sync_time:.2f}s')
    print('   📝 Simple, but SLOW - each domain checked one at a time')
    
    # 2. Threading
    print('\n2. THREADING:')
    start = time.time()
    results = threading_approach(domains, max_workers=5)
    thread_time = time.time() - start
    print(f'   ⏱️  Time: {thread_time:.2f}s')
    print(f'   📝 {sync_time/thread_time:.1f}x faster - parallel execution')
    print('   ✅ Works with existing sync code!')
    print('   ⚠️  Thread overhead, GIL contention for CPU work')
    
    # 3. Async
    print('\n3. ASYNC:')
    start = time.time()
    results = asyncio.run(async_approach(domains, max_concurrent=5))
    async_time = time.time() - start
    print(f'   ⏱️  Time: {async_time:.2f}s')
    print(f'   📝 {sync_time/async_time:.1f}x faster - concurrent execution')
    print('   ✅ Lower overhead than threads, handles 1000s of connections')
    print('   ⚠️  Requires async versions of all functions (all-or-nothing)')


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run performance comparison demonstration."""
    print('\n' + '='*80)
    print('ASYNC vs THREADS: Performance Comparison for Domain Checking')
    print('='*80)
    print('\n📖 See the file docstring at the top for complete explanations of:')
    print('   • The "Color Problem" (why async is all-or-nothing)')
    print('   • GIL and Event Loop mechanics')
    print('   • Decision guide (when to use async vs threads vs multiprocessing)')
    print('   • Practical patterns for mixing async and sync code')
    
    # Performance comparison
    domains = [f'example{i}.com' for i in range(10)]
    compare_approaches(domains)


if __name__ == '__main__':
    main()
