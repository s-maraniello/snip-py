"""
SCRIPT 2: Semaphores and Error Handling

This script builds on Script 1 and demonstrates:
- Using SEMAPHORES to throttle/limit concurrent operations (important for rate limiting!)
- Proper error handling in async code
- The return_exceptions parameter in asyncio.gather()
- Why throttling matters when dealing with external services

Key Terminology:
- SEMAPHORE: A synchronization primitive that limits the number of concurrent operations
- THROTTLING: Controlling the rate of operations to avoid overwhelming a resource
- RATE LIMITING: Restricting the number of requests per time period (often needed for APIs)
- BACKPRESSURE: When a system can't handle the incoming rate and needs to slow down

Real-world scenario:
Many APIs and servers have rate limits (e.g., "100 requests per minute"). 
Without throttling, we might:
- Get banned from an API
- Overwhelm a server (accidental DDoS)
- Exhaust system resources (too many open connections)
"""

import asyncio
import random
from typing import List, Dict, Union


# ============================================================================
# SIMULATED FETCHING WITH POTENTIAL FAILURES
# ============================================================================

async def fetch_domain_with_errors(domain: str, delay: float = 1.0) -> Dict[str, Union[str, int]]:
    """
    Simulates fetching a domain with potential network errors.
    
    IMPORTANT: In async code, errors work the same as in sync code - they propagate up the call stack.
    However, when using gather() or create_task(), you need to handle them carefully!
    """
    print(f'  🔍 Checking {domain}...')
    
    await asyncio.sleep(delay)
    
    # Simulate occasional failures (50% chance)
    if random.random() < 0.5:
        error_msg = f'Connection timeout for {domain}'
        print(f'  ❌ {error_msg}')
        raise asyncio.TimeoutError(error_msg)
    
    status = 200 if random.random() > 0.3 else 404
    result = {'domain': domain, 'status': status, 'available': status == 404, 'error': None}
    
    print(f'  ✅ {domain}: {status}')
    return result


# ============================================================================
# DEMO 1: The Problem - Too Many Concurrent Requests
# ============================================================================

async def demonstrate_no_throttling(domains: List[str]):
    """
    Shows what happens when we don't limit concurrency.
    
    If we had 1000 domains, this would try to check ALL 1000 simultaneously:
    - Could exhaust system resources (file descriptors for connections)
    - Might get rate-limited or banned by the server
    - Creates bursty traffic patterns
    """
    print('\n' + '='*80)
    print('DEMO 1: No Throttling - All requests at once')
    print('='*80)
    print(f'Launching {len(domains)} requests simultaneously...\n')
    
    start = asyncio.get_event_loop().time()
    
    # This creates tasks for ALL domains at once
    tasks = [fetch_domain_with_errors(domain, delay=1.0) for domain in domains]
    
    # We use return_exceptions=True to prevent gather() from raising on first error.
    # Instead, exceptions are returned in the results list.
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    elapsed = asyncio.get_event_loop().time() - start
    
    successes = sum(1 for r in results if isinstance(r, dict) and not r.get('error'))
    failures = len(results) - successes
    
    print(f'\n⏱️  Completed in {elapsed:.2f}s')
    print(f'📊 Results: {successes} successful, {failures} failed')
    print(f'⚠️  Problem: All {len(domains)} requests hit the server at the same instant!\n')
    
    return results


# ============================================================================
# DEMO 2: The Solution - Semaphore for Throttling
# ============================================================================

async def fetch_with_semaphore(
    domain: str, 
    semaphore: asyncio.Semaphore, 
    delay: float = 1.0
) -> Dict[str, Union[str, int]]:
    """
    Wrapper that uses a semaphore to limit concurrent executions.
    
    HOW SEMAPHORES WORK WITH THE EVENT LOOP:
    1. A Semaphore(n) allows n coroutines to run concurrently
    2. When the limit is reached, other coroutines WAIT (yield to event loop)
    3. The event loop runs other ready coroutines while these wait
    4. When a coroutine exits `async with`, it releases the semaphore
    5. The event loop wakes up one waiting coroutine to grab the free slot
    6. Use `async with semaphore:` to acquire and automatically release
    
    Think of it like a parking lot with limited spaces:
    - If spaces available → enter and park
    - If full → wait for someone to leave (coroutine yields to event loop)
    - When leaving → automatically free up a space (wakes up a waiting coroutine)
    
    IMPORTANT: The wait is NON-BLOCKING!
    - When semaphore is full, the coroutine YIELDS to the event loop
    - It doesn't block the thread or other coroutines
    - The event loop can run other coroutines while this one waits
    - This is cooperative multitasking in action!
    """
    # The `async with` ensures the semaphore is released even if an error occurs
    async with semaphore:
        # Only N coroutines can be in this block at any given time
        # where N is the semaphore's initial value
        try:
            result = await fetch_domain_with_errors(domain, delay)
            return result
        except asyncio.TimeoutError as e:
            # Handle the error and return a structured error response
            return {
                'domain': domain,
                'status': None,
                'available': None,
                'error': str(e)
            }


async def demonstrate_with_semaphore(domains: List[str], max_concurrent: int = 3):
    """
    Shows throttling with a semaphore - limits concurrent operations.
    
    WHY THIS MATTERS:
    - APIs often have rate limits (e.g., "10 requests/second")
    - Servers can be overwhelmed by too many simultaneous connections
    - Network/system resources (sockets, file descriptors) are limited
    - More controlled = more predictable performance
    """
    print('\n' + '='*80)
    print(f'DEMO 2: With Semaphore - Max {max_concurrent} concurrent requests')
    print('='*80)
    print(f'Processing {len(domains)} domains with throttling...\n')
    
    # Create a semaphore that allows only `max_concurrent` operations at once
    semaphore = asyncio.Semaphore(max_concurrent)
    
    start = asyncio.get_event_loop().time()
    
    # We create all tasks at once, but the semaphore ensures only N run simultaneously
    tasks = [fetch_with_semaphore(domain, semaphore, delay=1.0) for domain in domains]
    
    # gather() still returns results in the same order as input
    results = await asyncio.gather(*tasks)
    
    elapsed = asyncio.get_event_loop().time() - start
    
    successes = sum(1 for r in results if isinstance(r, dict) and not r.get('error'))
    failures = len(results) - successes
    
    print(f'\n⏱️  Completed in {elapsed:.2f}s')
    print(f'📊 Results: {successes} successful, {failures} failed')
    print(f'✅ Benefit: Never more than {max_concurrent} requests running at once!\n')
    
    return results


# ============================================================================
# DEMO 3: Error Handling Patterns
# ============================================================================

async def demonstrate_error_handling():
    """
    Shows different approaches to error handling in async code.
    """
    print('\n' + '='*80)
    print('DEMO 3: Error Handling Patterns')
    print('='*80)
    
    domains = ['error1.com', 'error2.com', 'error3.com']
    
    print('\nPattern 1: gather with return_exceptions=False (default)')
    print('Result: First exception is raised')
    try:
        results = await asyncio.gather(
            *[fetch_domain_with_errors(d, delay=0.5) for d in domains],
            return_exceptions=False  # This is the default
        )
    except asyncio.TimeoutError as e:
        print(f'⚠️  Caught exception: {e}')
        print('Note: Other tasks may still be running!\n')
    
    print('\nPattern 2: gather with return_exceptions=True')
    print('Result: Exceptions returned in the results list')
    results = await asyncio.gather(
        *[fetch_domain_with_errors(d, delay=0.5) for d in domains],
        return_exceptions=True  # Exceptions become part of results
    )
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f'  Domain {i+1}: ❌ Exception: {result}')
        else:
            print(f'  Domain {i+1}: ✅ Success: {result}')
    
    print('\n✅ All tasks completed (with or without errors)')


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def main():
    """
    Orchestrates all demonstrations.
    """
    print('\n' + '='*80)
    print('LEARNING ASYNC PYTHON: Semaphores and Error Handling')
    print('='*80)
    
    # Generate a list of dummy domains
    domains = [f'example{i}.com' for i in range(10)]
    
    # Demo 1: No throttling
    print('\n⚠️  WARNING: Without throttling, all requests launch at once!')
    results1 = await demonstrate_no_throttling(domains[:8])
    
    # Demo 2: With semaphore
    print('\n✅ BETTER: Semaphore limits concurrent operations')
    results2 = await demonstrate_with_semaphore(domains, max_concurrent=3)
    
    # Demo 3: Error handling
    await demonstrate_error_handling()
    
if __name__ == '__main__':
    asyncio.run(main())
