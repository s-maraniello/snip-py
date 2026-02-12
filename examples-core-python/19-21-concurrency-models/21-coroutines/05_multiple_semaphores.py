"""
SCRIPT 5: Using Multiple Semaphores for Different Resources

This script demonstrates:
- Using multiple semaphores to control access to different resources
- Why you need different semaphores for different APIs/services
- How coroutines can be controlled by different semaphores simultaneously
- Real-world pattern: respecting different rate limits for different services

Real-world scenario:
You're building an application that fetches data from multiple APIs:
- API A allows 10 requests/second
- API B allows 3 requests/second
- API C (your database) allows 50 concurrent connections

You need SEPARATE semaphores for each resource to respect their individual limits!
"""

import asyncio
import random
from typing import List, Dict
import time


# ============================================================================
# SIMULATED APIs WITH DIFFERENT RATE LIMITS
# ============================================================================

async def fetch_from_api_a(item_id: int, semaphore_a: asyncio.Semaphore) -> Dict:
    """
    Simulates fetching from API A (fast API, allows 10 concurrent requests).
    
    The semaphore ensures we never exceed API A's rate limit.
    """
    async with semaphore_a:  # Acquire slot from API A's semaphore
        print(f'  🟢 API-A: Fetching item {item_id}...')
        await asyncio.sleep(random.uniform(0.5, 1.0))  # Simulate API call
        return {'api': 'A', 'item_id': item_id, 'data': f'data-a-{item_id}'}


async def fetch_from_api_b(item_id: int, semaphore_b: asyncio.Semaphore) -> Dict:
    """
    Simulates fetching from API B (slower API, allows only 3 concurrent requests).
    
    Different API, different semaphore! API B is more restrictive.
    """
    async with semaphore_b:  # Acquire slot from API B's semaphore
        print(f'  🔵 API-B: Fetching item {item_id}...')
        await asyncio.sleep(random.uniform(1.0, 2.0))  # Simulate slower API
        return {'api': 'B', 'item_id': item_id, 'data': f'data-b-{item_id}'}


async def save_to_database(item: Dict, semaphore_db: asyncio.Semaphore) -> Dict:
    """
    Simulates saving to database (very fast, allows 50 concurrent connections).
    
    Yet another resource, yet another semaphore!
    """
    async with semaphore_db:  # Acquire slot from database semaphore
        print(f'  💾 DB: Saving {item["api"]}-{item["item_id"]}...')
        await asyncio.sleep(random.uniform(0.1, 0.3))  # Simulate DB write
        return {**item, 'saved': True}


# ============================================================================
# DEMO 1: Why Multiple Semaphores Matter
# ============================================================================

async def demonstrate_single_vs_multiple_semaphores():
    """
    Shows the difference between using one semaphore for everything vs 
    separate semaphores for different resources.
    """
    print('\n' + '='*80)
    print('DEMO 1: Single Semaphore vs Multiple Semaphores')
    print('='*80)
    
    # Scenario: Fetch from both APIs and save to DB
    item_ids = list(range(6))
    
    print('\n❌ BAD APPROACH: Using ONE semaphore for all resources')
    print('Problem: Treats all APIs the same, ignores their different limits\n')
    
    # Single semaphore limits TOTAL concurrency across all resources
    single_semaphore = asyncio.Semaphore(5)
    
    async def fetch_api_a_bad(item_id):
        async with single_semaphore:  # Same semaphore for everyone!
            return await fetch_from_api_a(item_id, asyncio.Semaphore(999))  # No real limit
    
    async def fetch_api_b_bad(item_id):
        async with single_semaphore:  # Same semaphore!
            return await fetch_from_api_b(item_id, asyncio.Semaphore(999))
    
    start = time.time()
    # All tasks compete for the same 5 slots
    tasks = (
        [fetch_api_a_bad(i) for i in item_ids[:3]] +
        [fetch_api_b_bad(i) for i in item_ids[:3]]
    )
    results = await asyncio.gather(*tasks)
    elapsed = time.time() - start
    
    print(f'\n⏱️  Took: {elapsed:.2f}s')
    print('📝 Problem: API B might steal slots from API A, or vice versa')
    print('   All resources forced to share the same limit!')
    
    # --------------------------------------------------------------------------
    
    print('\n' + '-'*80)
    print('\n✅ GOOD APPROACH: Separate semaphores for each resource')
    print('Benefit: Each API respects its own limit independently\n')
    
    # Separate semaphores for each resource
    semaphore_a = asyncio.Semaphore(10)  # API A allows 10 concurrent
    semaphore_b = asyncio.Semaphore(3)   # API B allows only 3 concurrent
    semaphore_db = asyncio.Semaphore(50) # DB allows 50 concurrent
    
    start = time.time()
    tasks = (
        [fetch_from_api_a(i, semaphore_a) for i in item_ids[:3]] +
        [fetch_from_api_b(i, semaphore_b) for i in item_ids[:3]]
    )
    results = await asyncio.gather(*tasks)
    elapsed = time.time() - start
    
    print(f'\n⏱️  Took: {elapsed:.2f}s')
    print('✅ Benefit: Each API has its own limit, optimally utilized!')


# ============================================================================
# DEMO 2: Real-World Pattern - Multiple APIs with Different Limits
# ============================================================================

async def fetch_enrich_save_pipeline(
    item_id: int,
    semaphore_a: asyncio.Semaphore,
    semaphore_b: asyncio.Semaphore,
    semaphore_db: asyncio.Semaphore
) -> Dict:
    """
    A realistic pipeline that uses multiple resources, each with its own semaphore.
    
    Pipeline:
    1. Fetch basic data from API A (controlled by semaphore_a)
    2. Enrich data from API B (controlled by semaphore_b)
    3. Save to database (controlled by semaphore_db)
    
    IMPORTANT: Each step acquires and releases its semaphore independently!
    This allows fine-grained control over each resource.
    """
    # Step 1: Fetch from API A
    basic_data = await fetch_from_api_a(item_id, semaphore_a)
    # semaphore_a is now released! Other coroutines can use API A
    
    # Step 2: Fetch additional data from API B
    enriched_data = await fetch_from_api_b(item_id, semaphore_b)
    # semaphore_b is now released!
    
    # Combine data
    combined = {**basic_data, 'enriched': enriched_data['data']}
    
    # Step 3: Save to database
    result = await save_to_database(combined, semaphore_db)
    # semaphore_db is now released!
    
    return result


async def demonstrate_real_world_pattern():
    """
    Shows a complete real-world example with multiple APIs and a database.
    """
    print('\n' + '='*80)
    print('DEMO 2: Real-World Pattern - Fetch, Enrich, Save')
    print('='*80)
    print('\nScenario: Process 20 items using multiple APIs with different rate limits')
    print('  • API A: 10 concurrent requests allowed')
    print('  • API B: 3 concurrent requests allowed')
    print('  • Database: 50 concurrent connections allowed\n')
    
    # Create separate semaphores for each resource
    semaphore_a = asyncio.Semaphore(10)  # API A limit
    semaphore_b = asyncio.Semaphore(3)   # API B limit
    semaphore_db = asyncio.Semaphore(50) # Database limit
    
    item_ids = list(range(20))
    
    start = time.time()
    
    # Create all tasks - they run concurrently but respect individual limits
    tasks = [
        fetch_enrich_save_pipeline(item_id, semaphore_a, semaphore_b, semaphore_db)
        for item_id in item_ids
    ]
    
    results = await asyncio.gather(*tasks)
    
    elapsed = time.time() - start
    
    print(f'\n⏱️  Processed {len(results)} items in {elapsed:.2f}s')
    print(f'✅ All done! Each API limit was respected independently.')


# ============================================================================
# DEMO 3: Nested Semaphores - A Coroutine Using Multiple Semaphores
# ============================================================================

async def complex_operation(
    item_id: int,
    semaphore_api: asyncio.Semaphore,
    semaphore_compute: asyncio.Semaphore
) -> Dict:
    """
    Demonstrates a single coroutine that needs to acquire MULTIPLE semaphores
    for different parts of its work.
    
    This is perfectly valid! A coroutine can:
    1. Acquire semaphore A for one operation
    2. Release semaphore A
    3. Acquire semaphore B for another operation
    4. Release semaphore B
    """
    # Phase 1: API call (limited by API semaphore)
    async with semaphore_api:
        print(f'  🌐 Item {item_id}: Making API call...')
        await asyncio.sleep(0.5)
        api_data = {'item_id': item_id, 'raw_data': f'api-data-{item_id}'}
    # semaphore_api released here
    
    # Phase 2: Heavy computation (limited by compute semaphore)
    async with semaphore_compute:
        print(f'  ⚙️  Item {item_id}: Processing data...')
        await asyncio.sleep(1.0)  # Simulate CPU-intensive work (in real: asyncio.to_thread)
        processed_data = {'item_id': item_id, 'processed': f'processed-{item_id}'}
    # semaphore_compute released here
    
    return {**api_data, **processed_data}


async def demonstrate_nested_semaphores():
    """
    Shows how a single coroutine can use multiple semaphores for different phases.
    """
    print('\n' + '='*80)
    print('DEMO 3: A Coroutine Using Multiple Semaphores')
    print('='*80)
    print('\nScenario: Each task has two phases:')
    print('  1. API call (limited to 5 concurrent)')
    print('  2. Heavy processing (limited to 2 concurrent)\n')
    
    # Different limits for different phases
    semaphore_api = asyncio.Semaphore(5)      # Allow 5 concurrent API calls
    semaphore_compute = asyncio.Semaphore(2)  # Allow only 2 concurrent processing
    
    tasks = [
        complex_operation(i, semaphore_api, semaphore_compute)
        for i in range(10)
    ]
    
    start = time.time()
    results = await asyncio.gather(*tasks)
    elapsed = time.time() - start
    
    print(f'\n⏱️  Completed in {elapsed:.2f}s')
    print('📝 Notice: Many API calls happened concurrently (limit: 5)')
    print('   But only 2 items were processed at a time!')


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def main():
    """
    Run all demonstrations.
    """
    print('\n' + '='*80)
    print('LEARNING ASYNC PYTHON: Multiple Semaphores')
    print('='*80)
    
    # Demo 1: Why multiple semaphores matter
    await demonstrate_single_vs_multiple_semaphores()
    
    # Demo 2: Real-world pattern
    await demonstrate_real_world_pattern()
    
    # Demo 3: One coroutine, multiple semaphores
    await demonstrate_nested_semaphores()
    
    # Summary
    print('\n' + '='*80)
    print('KEY TAKEAWAYS')
    print('='*80)
    print('''
1. MULTIPLE SEMAPHORES are essential when working with multiple resources:
   • Each API/service has its own rate limit
   • Each semaphore enforces one specific limit
   • Don't use a single semaphore for everything!

2. PATTERN: One semaphore per resource
   ```python
   semaphore_api_a = asyncio.Semaphore(10)  # API A: 10 req/sec
   semaphore_api_b = asyncio.Semaphore(3)   # API B: 3 req/sec
   semaphore_db = asyncio.Semaphore(50)     # DB: 50 connections
   ```

3. Each coroutine can use MULTIPLE semaphores:
   • Acquire semaphore A for operation A
   • Release it when done
   • Acquire semaphore B for operation B
   • Each resource has its own protection

4. REAL-WORLD EXAMPLE:
   ```python
   async def process_item(item_id, sem_api, sem_db):
       # Respects API limit
       async with sem_api:
           data = await fetch_from_api(item_id)
       
       # Respects database limit (separately!)
       async with sem_db:
           await save_to_db(data)
   ```

5. WHY THIS MATTERS:
   • Different APIs have different limits
   • Prevents "slowest resource" from blocking others
   • Optimal utilization of each resource
   • Respects all rate limits simultaneously

6. COMMON MISTAKE to avoid:
   ❌ Using one semaphore for all resources
   ✅ Use separate semaphores for separate resources
''')
    print('='*80)
    
    print('\n💡 PRO TIP: In production, read rate limits from config:')
    print('''
   RATE_LIMITS = {
       'api_a': 10,
       'api_b': 3,
       'database': 50,
   }
   
   semaphores = {
       name: asyncio.Semaphore(limit)
       for name, limit in RATE_LIMITS.items()
   }
''')
    print('='*80)


if __name__ == '__main__':
    asyncio.run(main())
