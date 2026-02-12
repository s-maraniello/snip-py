"""
SCRIPT 3: Progress Tracking and Mixing Async with Threads

This script demonstrates:
- Using asyncio.as_completed() for progress reporting as tasks finish
- The difference between gather() and as_completed()
- Using asyncio.to_thread() to run blocking I/O operations
- When and why to mix async with threads
- Practical pattern: async downloads + synchronous file writes

Key Terminology:
- as_completed(): Returns an iterator of futures that yields results as they complete (not in order!)
- to_thread(): Runs a blocking function in a thread pool to avoid blocking the event loop
- BLOCKING OPERATION: Code that stops execution (like file I/O, CPU-heavy work) - bad for async!
- EVENT LOOP BLOCKING: When async code can't switch to other coroutines (kills concurrency)

Real-world scenario:
You're downloading thousands of files and saving them to disk. 
- Downloads are I/O-bound and async-friendly
- Disk writes are synchronous and could block the event loop
- Solution: async downloads + threaded writes
"""

import asyncio
import random
import json
from pathlib import Path
from typing import List, Dict
import time


# ============================================================================
# SIMULATED DOMAIN CHECKING (from previous scripts)
# ============================================================================

async def fetch_domain(domain: str, delay: float = 1.0) -> Dict:
    """
    Simulates fetching domain information.
    In reality: async with httpx.AsyncClient() as client: ...
    """
    await asyncio.sleep(delay)
    
    # Simulate random failures (10% chance)
    if random.random() < 0.1:
        raise asyncio.TimeoutError(f'Timeout checking {domain}')
    
    return {
        'domain': domain,
        'status': random.choice([200, 404]),
        'response_time': delay,
        'timestamp': time.time()
    }


# ============================================================================
# DEMO 1: gather() vs as_completed()
# ============================================================================

async def demonstrate_gather_vs_as_completed(domains: List[str]):
    """
    Shows the key difference between gather() and as_completed().
    
    gather():
    - Waits for ALL tasks to complete
    - Returns results in ORIGINAL ORDER
    - Good when you need all results at once
    
    as_completed():
    - Yields results AS THEY FINISH (not in order!)
    - Good for progress reporting
    - Can process results immediately
    """
    print('\n' + '='*80)
    print('DEMO 1: gather() vs as_completed()')
    print('='*80)
    
    # Give domains different delays to see the difference
    tasks_with_delays = [
        (domains[0], 2.0),  # Slowest
        (domains[1], 0.5),  # Fastest
        (domains[2], 1.5),
        (domains[3], 1.0),
    ]
    
    # Method 1: asyncio.gather() - waits for all, returns in order
    print('\n--- Using gather() ---')
    print('Waits for ALL tasks, returns results in ORIGINAL ORDER\n')
    
    start = time.time()
    results = await asyncio.gather(
        *[fetch_domain(domain, delay) for domain, delay in tasks_with_delays],
        return_exceptions=True
    )

    print('\nResults from gather():')
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f'  {i+1}. ❌ Error: {result}')
        else:
            print(f"  {i+1}. ✅ {result['domain']} (took {result['response_time']}s)")
    
    print(f'\n⏱️  Total time: {time.time() - start:.2f}s')
    print('📝 Notice: Results are in the SAME ORDER as input (even though some finished faster)')
    
    # Method 2: asyncio.as_completed() - yields as each finishes
    print('\n--- Using as_completed() ---')
    print('Yields results AS THEY FINISH (not in order)\n')
    
    # Create tasks (not coroutines - important for as_completed!)
    tasks = [
        asyncio.create_task(fetch_domain(domain, delay))
        for domain, delay in tasks_with_delays
    ]
    
    start = time.time()
    
    # as_completed() returns an iterator that yields futures as they complete
    for i, coro in enumerate(asyncio.as_completed(tasks), 1):
        try:
            # XXX. As we used `asyncio.as_completed`, the `await` will not block until each task is done. If we had 
            # simply looped through tasks as 
            # for domain, delay in tasks_with_delays:
            #     result = await fetch_domain(domain, delay)
            #     results.append(result)
            #     ...
            # the `await` would have blocked until each task was done. In practice, this would have been a sequential 
            # execution. See `01_async_basics.py`.
            result = await coro 
            elapsed = time.time() - start
            print(f"  [{elapsed:.1f}s] Task {i}/4 completed: {result['domain']} ✅")
        except Exception as e:
            print(f'  Error: {e} ❌')
    
    print(f'\n⏱️  Total time: {time.time() - start:.2f}s')
    print('📝 Notice: Results appear AS THEY FINISH (fastest first!)')


# ============================================================================
# DEMO 2: Progress Tracking with as_completed()
# ============================================================================

async def check_domain_with_progress(domain: str, domain_num: int, total: int, delay: float) -> Dict:
    """
    Wrapper that adds progress information.
    """
    result = await fetch_domain(domain, delay)
    result['completed'] = domain_num
    result['total'] = total
    return result


async def demonstrate_progress_tracking(domains: List[str]):
    """
    Shows how to implement real-time progress tracking using as_completed().
    
    This is incredibly useful for:
    - Long-running batch operations
    - User-facing applications (show progress bars)
    - Monitoring/debugging (see what's taking time)
    """
    print('\n' + '='*80)
    print('DEMO 2: Real-time Progress Tracking')
    print('='*80)
    print(f'Processing {len(domains)} domains...\n')
    
    # Create all tasks with random delays
    tasks = [
        asyncio.create_task(
            check_domain_with_progress(domain, i+1, len(domains), random.uniform(0.5, 2.0))
        )
        for i, domain in enumerate(domains)
    ]
    
    start = time.time()
    completed = 0
    successful = 0
    failed = 0
    
    # Process results as they complete
    for coro in asyncio.as_completed(tasks):
        try:
            result = await coro
            completed += 1
            successful += 1
            
            # Calculate progress
            progress = (completed / len(domains)) * 100
            elapsed = time.time() - start
            
            # Show progress (in a real app, update a progress bar)
            print(f"[{progress:5.1f}%] ({completed}/{len(domains)}) "
                  f"{result['domain']:20s} - Status {result['status']} "
                  f"({elapsed:.1f}s elapsed)")
            
        except Exception as e:
            completed += 1
            failed += 1
            progress = (completed / len(domains)) * 100
            print(f"[{progress:5.1f}%] ({completed}/{len(domains)}) ❌ Error: {e}")
    
    elapsed = time.time() - start
    print(f'\n⏱️  Total: {elapsed:.2f}s')
    print(f'📊 Success: {successful}, Failed: {failed}')


# ============================================================================
# DEMO 3: Using asyncio.to_thread() for Blocking Operations
# ============================================================================

def save_results_to_disk(results: List[Dict], filename: str) -> None:
    """
    A BLOCKING function that writes to disk.
    
    WHY THIS IS BLOCKING:
    - File I/O is synchronous in Python (standard open/write operations)
    - While this runs, it BLOCKS the thread - no other code can run
    - In an async context, this would BLOCK THE EVENT LOOP = BAD!
    
    SOLUTIONS:
    1. Use asyncio.to_thread() to run in a thread pool (simple, good for occasional I/O). See 
        `04_async_vs_threads_discussion.py` for more info on why does this work.
    2. Use aiofiles library for true async file I/O (better for lots of file operations)
    
    WHY NOT ALWAYS USE AIOFILES?
    - More dependencies
    - Most file operations are fast enough that threading is fine
    - to_thread() works with ANY blocking function (databases, legacy code, etc.)
    """
    print(f'  💾 [BLOCKING] Writing to {filename}...')
    
    # Simulate some processing time
    time.sleep(0.5)
    
    # Write to file (blocking operation!)
    path = Path(filename)
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f'  ✅ [BLOCKING] Saved {len(results)} results to {filename}')


async def demonstrate_blocking_operations(domains: List[str]):
    """
    Shows the problem with blocking operations and the solution using to_thread().
    """
    print('\n' + '='*80)
    print('DEMO 3: Handling Blocking Operations with to_thread()')
    print('='*80)
    
    print('\n🔍 Scenario: Download async, save to disk (which is blocking)\n')
    
    # Fetch domains asynchronously
    print('Step 1: Fetching domains (async, non-blocking)...')
    tasks = [fetch_domain(domain, delay=random.uniform(0.3, 0.8)) for domain in domains]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out exceptions
    successful_results = [r for r in results if isinstance(r, dict)]
    
    print(f'✅ Fetched {len(successful_results)} domains\n')
    
    # --- THE PROBLEM: Blocking write ---
    print('Step 2: Saving to disk (blocking operation)...')
    print('⚠️  If we call save_results_to_disk() directly, it BLOCKS the event loop!')
    print('    No other coroutines can run during the write.\n')
    
    # --- THE SOLUTION: asyncio.to_thread() ---
    print('✅ Solution: Use asyncio.to_thread() to run in a thread pool\n')
    
    # Run the blocking function in a thread pool
    # The event loop remains free to handle other coroutines
    await asyncio.to_thread(
        save_results_to_disk,
        successful_results,
        '/tmp/domain_results.json'
    )
    
    print('\n💡 EXPLANATION:')
    print('   - asyncio.to_thread() runs the function in a ThreadPoolExecutor')
    print('   - The event loop is NOT blocked - other coroutines can run')
    print('   - Good for: file I/O, CPU-bound work, legacy blocking libraries')
    print('   - Alternative: Use aiofiles for truly async file operations')


# ============================================================================
# DEMO 4: Complete Example - Async Download + Progress + Threaded Save
# ============================================================================

async def complete_pipeline_example(domains: List[str]):
    """
    A complete example combining everything:
    - Async downloads with semaphore (throttling)
    - Progress tracking with as_completed()
    - Threaded disk writes with to_thread()
    """
    print('\n' + '='*80)
    print('DEMO 4: Complete Pipeline')
    print('='*80)
    print('Combining: Async downloads + Progress tracking + Threaded saves\n')
    
    semaphore = asyncio.Semaphore(5)  # Max 5 concurrent fetches
    
    async def fetch_with_semaphore(domain: str) -> Dict:
        async with semaphore:
            return await fetch_domain(domain, delay=random.uniform(0.3, 1.5))
    
    # Create all tasks
    tasks = [asyncio.create_task(fetch_with_semaphore(domain)) for domain in domains]
    
    results = []
    completed = 0
    
    # Process as they complete
    for coro in asyncio.as_completed(tasks):
        try:
            result = await coro
            results.append(result)
            completed += 1
            progress = (completed / len(domains)) * 100
            print(f"[{progress:5.1f}%] Downloaded: {result['domain']}")
        except Exception as e:
            completed += 1
            print(f'[{progress:5.1f}%] ❌ Failed: {e}')
    
    # Save to disk using thread pool (non-blocking)
    print('\n💾 Saving results to disk (in thread pool)...')
    await asyncio.to_thread(save_results_to_disk, results, '/tmp/complete_results.json')
    
    print(f'\n✅ Pipeline complete! Processed {len(domains)} domains')


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def main():
    """
    Run all demonstrations.
    """
    print('\n' + '='*80)
    print('LEARNING ASYNC PYTHON: Progress Tracking and Threading')
    print('='*80)
    
    domains = [f'example{i}.com' for i in range(12)]
    
    # Demo 1: gather vs as_completed
    await demonstrate_gather_vs_as_completed(domains[:4])
    
    # Demo 2: Progress tracking
    await demonstrate_progress_tracking(domains[:8])
    
    # Demo 3: Blocking operations
    await demonstrate_blocking_operations(domains[:5])
    
    # Demo 4: Complete pipeline
    await complete_pipeline_example(domains)
    
    # Summary
    print('\n' + '='*80)
    print('KEY TAKEAWAYS')
    print('='*80)
    print('1. asyncio.gather(*coros):')
    print('   - Waits for ALL tasks')
    print('   - Returns results in ORIGINAL order')
    print('   - Use when: You need all results at once')
    print()
    print('2. asyncio.as_completed(tasks):')
    print('   - Yields results AS THEY FINISH')
    print('   - Results in COMPLETION order (not original)')
    print('   - Use when: Progress tracking, early result processing')
    print()
    print('3. asyncio.to_thread(func, *args):')
    print('   - Runs blocking function in thread pool')
    print('   - Event loop stays free for other coroutines')
    print('   - Use when: File I/O, CPU work, blocking libraries')
    print()
    print('4. PATTERN: Async I/O + Threaded Blocking')
    print('   - Download/fetch: async (many concurrent operations)')
    print('   - Disk/CPU work: to_thread() (occasional blocking)')
    print('   - Best of both worlds!')
    print('='*80)


if __name__ == '__main__':
    asyncio.run(main())
