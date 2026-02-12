"""
SCRIPT 6: Time-Based Rate Limiting (Beyond Simple Semaphores)

This script demonstrates:
- Why asyncio.Semaphore alone is NOT sufficient for time-based rate limits
- The difference between concurrent limits and rate limits
- How to implement a time-window rate limiter
- Using sliding window rate limiting for APIs
- Combining concurrent limits with rate limits

Real-world problem:
API says: "100 requests per minute"
- asyncio.Semaphore(100) would allow 100 CONCURRENT requests, not 100 per minute!
- If each request takes 0.1s, you'd make 600 requests/minute (⚠️ over limit!)
- You need TIME-AWARE rate limiting, not just concurrency limiting

Key insight: Semaphores limit CONCURRENT operations, not RATE over time!
"""

import asyncio
import time
from collections import deque
from typing import Deque, Optional
import random


# ============================================================================
# PROBLEM: Semaphore is NOT a Rate Limiter
# ============================================================================

async def fetch_fast_api(item_id: int) -> dict:
    """Simulates a FAST API call (0.1 seconds)."""
    await asyncio.sleep(0.1)
    return {'item_id': item_id, 'timestamp': time.time()}


async def demonstrate_semaphore_problem():
    """
    Shows why Semaphore alone doesn't enforce time-based rate limits.
    """
    print('\n' + '='*80)
    print('❌ PROBLEM: Semaphore Does NOT Enforce Time-Based Rate Limits')
    print('='*80)
    
    print('\nScenario: API allows "10 requests per second"')
    print('Using: asyncio.Semaphore(10)\n')
    
    semaphore = asyncio.Semaphore(10)  # Allows 10 CONCURRENT requests
    
    async def fetch_with_semaphore(item_id):
        async with semaphore:
            return await fetch_fast_api(item_id)
    
    start = time.time()
    
    # Launch 50 requests
    tasks = [fetch_with_semaphore(i) for i in range(50)]
    results = await asyncio.gather(*tasks)
    
    elapsed = time.time() - start
    rate = len(results) / elapsed
    
    print(f'⏱️  Time taken: {elapsed:.2f}s')
    print(f'📊 Requests completed: {len(results)}')
    print(f'🚀 Actual rate: {rate:.1f} requests/second')
    print(f'\n⚠️  PROBLEM: We wanted 10 req/s, but got {rate:.1f} req/s!')
    print('   Because semaphore limits CONCURRENCY, not RATE!')
    print('   With fast requests (0.1s each), 10 concurrent = ~100 req/s')


# ============================================================================
# SOLUTION 1: Simple Time-Window Rate Limiter
# ============================================================================

class SimpleRateLimiter:
    """
    A simple rate limiter that tracks requests in a time window.
    
    Limits: "max_requests per time_window seconds"
    Example: 100 requests per 60 seconds
    
    This uses a FIXED WINDOW approach:
    - Counts requests in the current time window
    - Resets count when window expires
    """
    
    def __init__(self, max_requests: int, time_window: float):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Deque[float] = deque()
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """
        Wait until we can make a request without exceeding the rate limit.
        
        How it works:
        1. Remove requests older than time_window
        2. If we're at the limit, wait until oldest request expires
        3. Record this request's timestamp
        """
        async with self._lock:
            now = time.time()
            
            # Remove requests outside the time window
            while self.requests and self.requests[0] < now - self.time_window:
                self.requests.popleft()
            
            # If at limit, wait until oldest request expires
            if len(self.requests) >= self.max_requests:
                oldest_request_time = self.requests[0]
                wait_time = (oldest_request_time + self.time_window) - now
                
                if wait_time > 0:
                    print(f'  ⏸️  Rate limit reached, waiting {wait_time:.2f}s...')
                    await asyncio.sleep(wait_time)
                    # After sleeping, recurse to try again
                    return await self.acquire()
            
            # Record this request
            self.requests.append(now)
    
    def __repr__(self):
        return f'RateLimiter({self.max_requests}/{self.time_window}s)'


async def demonstrate_simple_rate_limiter():
    """
    Shows how a time-window rate limiter properly enforces rate limits.
    """
    print('\n' + '='*80)
    print('✅ SOLUTION 1: Time-Window Rate Limiter')
    print('='*80)
    
    print('\nScenario: API allows "10 requests per 1 second"')
    print('Using: SimpleRateLimiter(10, 1.0)\n')
    
    rate_limiter = SimpleRateLimiter(max_requests=10, time_window=1.0)
    
    async def fetch_with_rate_limiter(item_id):
        await rate_limiter.acquire()
        print(f'  🟢 Request {item_id} at {time.time():.2f}')
        return await fetch_fast_api(item_id)
    
    start = time.time()
    
    # Launch 25 requests
    tasks = [fetch_with_rate_limiter(i) for i in range(25)]
    results = await asyncio.gather(*tasks)
    
    elapsed = time.time() - start
    avg_rate = len(results) / elapsed
    
    print(f'\n⏱️  Time taken: {elapsed:.2f}s')
    print(f'📊 Requests completed: {len(results)}')
    print(f'✅ Average rate: {avg_rate:.1f} requests/second')
    print(f'   Much closer to our 10 req/s target!')


# ============================================================================
# SOLUTION 2: Combining Rate Limiter + Semaphore
# ============================================================================

class CombinedLimiter:
    """
    Combines rate limiting (requests per time window) with concurrency limiting.
    
    Why both?
    - Rate limiter: Enforces "X requests per Y seconds" (API requirement)
    - Semaphore: Limits simultaneous operations (resource protection)
    
    Example: API allows "100 req/min" but your system can only handle 10 concurrent
    """
    
    def __init__(self, rate_limit: int, time_window: float, max_concurrent: int):
        self.rate_limiter = SimpleRateLimiter(rate_limit, time_window)
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def __aenter__(self):
        # First, acquire semaphore (limit concurrency)
        await self.semaphore.acquire()
        # Then, check rate limit (limit rate over time)
        await self.rate_limiter.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Release semaphore
        self.semaphore.release()


async def demonstrate_combined_limiter():
    """
    Shows how to combine rate limiting with concurrency limiting.
    """
    print('\n' + '='*80)
    print('✅ SOLUTION 2: Combined Rate + Concurrency Limiting')
    print('='*80)
    
    print('\nScenario: API allows "10 req/second" AND max 3 concurrent requests')
    print('Using: CombinedLimiter(rate_limit=10, time_window=1.0, max_concurrent=3)\n')
    
    limiter = CombinedLimiter(rate_limit=10, time_window=1.0, max_concurrent=3)
    
    async def fetch_with_combined_limiter(item_id):
        async with limiter:
            print(f'  🔵 Request {item_id} at {time.time():.2f}')
            return await fetch_fast_api(item_id)
    
    start = time.time()
    
    # Launch 20 requests
    tasks = [fetch_with_combined_limiter(i) for i in range(20)]
    results = await asyncio.gather(*tasks)
    
    elapsed = time.time() - start
    avg_rate = len(results) / elapsed
    
    print(f'\n⏱️  Time taken: {elapsed:.2f}s')
    print(f'📊 Requests completed: {len(results)}')
    print(f'✅ Average rate: {avg_rate:.1f} requests/second')
    print('   Both rate and concurrency limits respected!')


# ============================================================================
# SOLUTION 3: Adaptive Rate Limiter (Dynamic Adjustment)
# ============================================================================

class AdaptiveRateLimiter:
    """
    An adaptive rate limiter that can adjust limits dynamically.
    
    Useful when:
    - API returns rate limit info in response headers
    - You want to back off after hitting limits
    - Rate limits change based on subscription tier
    """
    
    def __init__(self, initial_rate: int, time_window: float):
        self.max_requests = initial_rate
        self.time_window = time_window
        self.requests: Deque[float] = deque()
        self._lock = asyncio.Lock()
        self.adjustment_count = 0
    
    def adjust_limit(self, new_limit: int):
        """
        Dynamically adjust the rate limit.
        
        Use cases:
        - API returns X-RateLimit-Remaining header
        - Hit 429 (Too Many Requests) → reduce limit
        - Upgrade subscription → increase limit
        """
        old_limit = self.max_requests
        self.max_requests = new_limit
        self.adjustment_count += 1
        print(f'  ⚙️  Rate limit adjusted: {old_limit} → {new_limit} req/{self.time_window}s')
    
    async def acquire(self):
        async with self._lock:
            now = time.time()
            
            # Remove old requests
            while self.requests and self.requests[0] < now - self.time_window:
                self.requests.popleft()
            
            # If at limit, wait
            if len(self.requests) >= self.max_requests:
                oldest = self.requests[0]
                wait_time = (oldest + self.time_window) - now
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    return await self.acquire()
            
            self.requests.append(now)


async def demonstrate_adaptive_limiter():
    """
    Shows how to dynamically adjust rate limits based on API responses.
    """
    print('\n' + '='*80)
    print('✅ SOLUTION 3: Adaptive Rate Limiter (Dynamic Adjustment)')
    print('='*80)
    
    print('\nScenario: Start with 10 req/s, adjust based on "API feedback"\n')
    
    rate_limiter = AdaptiveRateLimiter(initial_rate=10, time_window=1.0)
    
    async def fetch_with_adaptive_limiter(item_id):
        await rate_limiter.acquire()
        
        # Simulate API response with rate limit info
        result = await fetch_fast_api(item_id)
        
        # Simulate: Every 7th request, API says "slow down!"
        if item_id > 0 and item_id % 7 == 0:
            print(f'  ⚠️  Request {item_id}: API says "slow down!"')
            rate_limiter.adjust_limit(max(5, rate_limiter.max_requests - 2))
        
        # Simulate: Every 15th request, API says "you can speed up"
        if item_id > 0 and item_id % 15 == 0:
            print(f'  ✨ Request {item_id}: API says "you can speed up!"')
            rate_limiter.adjust_limit(min(20, rate_limiter.max_requests + 3))
        
        return result
    
    start = time.time()
    
    # Launch 25 requests
    tasks = [fetch_with_adaptive_limiter(i) for i in range(25)]
    results = await asyncio.gather(*tasks)
    
    elapsed = time.time() - start
    
    print(f'\n⏱️  Time taken: {elapsed:.2f}s')
    print(f'📊 Requests completed: {len(results)}')
    print(f'⚙️  Adjustments made: {rate_limiter.adjustment_count}')
    print(f'🎯 Final rate limit: {rate_limiter.max_requests} req/{rate_limiter.time_window}s')


# ============================================================================
# REAL-WORLD PATTERN: Multiple APIs with Different Rate Limiters
# ============================================================================

async def demonstrate_multiple_rate_limiters():
    """
    Shows the real-world pattern: different APIs, different rate limiters.
    """
    print('\n' + '='*80)
    print('🌍 REAL-WORLD PATTERN: Multiple APIs with Rate Limiters')
    print('='*80)
    
    print('\nScenario: Three APIs with different rate limits')
    print('  • API A: 10 requests/second')
    print('  • API B: 5 requests/second')
    print('  • API C: 20 requests/second\n')
    
    # Each API gets its own rate limiter
    limiter_a = SimpleRateLimiter(max_requests=10, time_window=1.0)
    limiter_b = SimpleRateLimiter(max_requests=5, time_window=1.0)
    limiter_c = SimpleRateLimiter(max_requests=20, time_window=1.0)
    
    async def fetch_api_a(item_id):
        await limiter_a.acquire()
        print(f'  🟢 API-A: Request {item_id}')
        return await fetch_fast_api(item_id)
    
    async def fetch_api_b(item_id):
        await limiter_b.acquire()
        print(f'  🔵 API-B: Request {item_id}')
        return await fetch_fast_api(item_id)
    
    async def fetch_api_c(item_id):
        await limiter_c.acquire()
        print(f'  🟣 API-C: Request {item_id}')
        return await fetch_fast_api(item_id)
    
    start = time.time()
    
    # Mix requests to all three APIs
    tasks = (
        [fetch_api_a(i) for i in range(10)] +
        [fetch_api_b(i) for i in range(5)] +
        [fetch_api_c(i) for i in range(15)]
    )
    
    results = await asyncio.gather(*tasks)
    elapsed = time.time() - start
    
    print(f'\n⏱️  Total time: {elapsed:.2f}s')
    print(f'📊 Total requests: {len(results)}')
    print('✅ Each API respected its own rate limit!')


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def main():
    """
    Run all demonstrations.
    """
    print('\n' + '='*80)
    print('LEARNING ASYNC PYTHON: Time-Based Rate Limiting')
    print('='*80)
    
    # Problem: Semaphore is not a rate limiter
    await demonstrate_semaphore_problem()
    
    # Solution 1: Time-window rate limiter
    await demonstrate_simple_rate_limiter()
    
    # Solution 2: Combined rate + concurrency
    await demonstrate_combined_limiter()
    
    # Solution 3: Adaptive rate limiter
    await demonstrate_adaptive_limiter()
    
    # Real-world pattern
    await demonstrate_multiple_rate_limiters()
    
    # Summary
    print('\n' + '='*80)
    print('KEY TAKEAWAYS')
    print('='*80)
    print('''
1. SEMAPHORE ≠ RATE LIMITER:
   • Semaphore limits CONCURRENT operations
   • Rate limiter limits REQUESTS PER TIME WINDOW
   • asyncio.Semaphore(10) ≠ "10 requests per second"!

2. TIME-BASED RATE LIMITING requires:
   • Tracking request timestamps
   • Sliding or fixed time windows
   • Waiting when limit is exceeded

3. IMPLEMENTATION PATTERN:
   ```python
   class RateLimiter:
       def __init__(self, max_requests, time_window):
           self.max_requests = max_requests
           self.time_window = time_window
           self.requests = deque()  # Track timestamps
       
       async def acquire(self):
           # Remove old requests
           # Wait if at limit
           # Record new request
   ```

4. COMBINING LIMITS:
   Use BOTH when needed:
   • Rate limiter for API requirements ("100 req/min")
   • Semaphore for resource protection (max concurrent)

5. DYNAMIC ADJUSTMENT:
   Rate limits can change based on:
   • API response headers (X-RateLimit-Remaining)
   • 429 status codes (Too Many Requests)
   • Subscription tier changes
   • Time of day pricing

6. REAL-WORLD PATTERN:
   ```python
   limiters = {
       'github': RateLimiter(5000, 3600),    # 5000/hour
       'twitter': RateLimiter(900, 900),     # 900/15min
       'database': Semaphore(50),             # 50 concurrent
   }
   
   async def fetch_github(item_id):
       await limiters['github'].acquire()
       return await fetch_data()
   ```

7. ALTERNATIVE LIBRARIES:
   For production, consider:
   • aiolimiter - Popular async rate limiter
   • aiohttp-retry - Includes rate limiting
   • asyncio-throttle - Another option
   
   But understanding the concept is crucial!
''')
    print('='*80)
    
    print('\n💡 PRO TIPS:')
    print('''
1. Read API docs carefully:
   • "100 concurrent" → Use Semaphore
   • "100 per minute" → Use RateLimiter
   • Both specified? → Use both!

2. Parse rate limit headers:
   • X-RateLimit-Limit
   • X-RateLimit-Remaining
   • X-RateLimit-Reset
   → Adjust limiter dynamically!

3. Handle 429 responses:
   • Back off exponentially
   • Reduce rate limit temporarily
   • Retry after Retry-After header

4. Monitor your rates:
   • Log actual request rates
   • Compare to limits
   • Alert when approaching limits
''')
    print('='*80)


if __name__ == '__main__':
    asyncio.run(main())
