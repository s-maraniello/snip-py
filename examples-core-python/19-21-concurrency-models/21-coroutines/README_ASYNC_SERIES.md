# Async Python Learning Series

A progressive series of educational scripts covering asyncio concepts from Fluent Python.

## 📚 Learning Path

### Script 1: `01_async_basics.py` - Foundations
**Concepts covered:**
- Awaitability: What can be awaited and why
- `await coro()` vs `asyncio.create_task(coro())`
- Sequential vs concurrent execution
- `asyncio.gather()` for running multiple coroutines
- Spinner animation with background tasks

**Run it:**
```bash
python 01_async_basics.py
```

**Key learnings:** The fundamental difference between delegation (`await`) and scheduling (`create_task`). See how concurrent execution works in a single thread.

---

### Script 2: `02_async_semaphore_errors.py` - Throttling & Robustness
**Concepts covered:**
- Semaphores for rate limiting
- Why throttling matters (API limits, resource protection)
- Error handling with `return_exceptions=True`
- Preventing overwhelming external services

**Run it:**
```bash
python 02_async_semaphore_errors.py
```

**Key learnings:** How to control concurrency with semaphores. Essential for real-world applications dealing with API rate limits.

---

### Script 3: `03_async_progress_and_threads.py` - Progress & Hybrid Patterns
**Concepts covered:**
- `asyncio.gather()` vs `asyncio.as_completed()`
- Real-time progress tracking
- `asyncio.to_thread()` for blocking operations
- When and why to mix async with threads
- Complete pipeline: async fetch + progress + threaded save

**Run it:**
```bash
python 03_async_progress_and_threads.py
```

**Key learnings:** How to show progress as tasks complete, and how to handle blocking operations (file I/O, CPU work) without blocking the event loop.

---

### Script 4: `04_async_vs_threads_discussion.py` - Decision Guide
**Concepts covered:**
- The "async color problem" (all-or-nothing)
- When to use async vs threads vs multiprocessing
- Performance comparison for I/O-bound work
- Practical patterns for mixing async and sync code
- Migration strategies for existing codebases

**Run it:**
```bash
python 04_async_vs_threads_discussion.py
```

**Key learnings:** When async is the right choice, when threading is better, and how to make them work together. Addresses the fundamental question: "Should I use async or threads?"

---

### Script 5: `05_multiple_semaphores.py` - Multiple Resource Limits
**Concepts covered:**
- Using multiple semaphores for different resources
- Why you need separate semaphores for different APIs
- One coroutine using multiple semaphores
- Real-world pattern: respecting different rate limits
- Nested semaphore usage

**Run it:**
```bash
python 05_multiple_semaphores.py
```

**Key learnings:** How to manage multiple resources (different APIs, database, etc.) each with their own rate limits. Essential pattern for real-world applications that interact with multiple services.

---

### Script 6: `06_time_based_rate_limiting.py` - Rate Limiting Over Time
**Concepts covered:**
- Why Semaphore ≠ Rate Limiter (crucial distinction!)
- Difference between concurrent limits and time-based rate limits
- Implementing sliding window rate limiters
- Combining rate limiters with semaphores
- Adaptive/dynamic rate limit adjustment
- Parsing API response headers to adjust limits

**Run it:**
```bash
python 06_time_based_rate_limiting.py
```

**Key learnings:** How to properly implement "X requests per Y seconds" rate limiting (what APIs actually require). Semaphores only limit concurrency, not rate over time. This script shows you how to build time-aware rate limiters and when to use them vs semaphores.

---

## 🎯 Quick Reference

### ⚠️ Critical Distinction: Semaphore vs Rate Limiter

| Aspect | Semaphore | Rate Limiter |
|--------|-----------|--------------|
| **Limits** | Concurrent operations | Requests per time window |
| **Example** | "10 at once" | "100 per minute" |
| **Use when** | Protecting resources | Meeting API rate limits |
| **Time-aware?** | ❌ No | ✅ Yes |

**Common mistake:** Using `asyncio.Semaphore(100)` for "100 requests/minute"
- ❌ **Wrong:** Allows 100 concurrent (could be 1000s per minute!)
- ✅ **Right:** Use `RateLimiter(100, 60)` for time-based limits

---

### When to use ASYNC
- ✅ I/O-bound work (network, disk)
- ✅ Many concurrent operations (100s-1000s)
- ✅ Starting new projects
- ✅ Using async-native libraries (httpx, aiohttp)

### When to use THREADS
- ✅ I/O-bound with sync libraries
- ✅ Existing synchronous codebase
- ✅ Modest concurrency (< 100)
- ✅ Team unfamiliar with async

### When to use MULTIPROCESSING
- ✅ CPU-bound work
- ✅ Need multiple CPU cores
- ✅ Can parallelize independent work

---

## 📖 Recommended Reading Order

1. **Start here:** `01_async_basics.py` - Understand the fundamentals
2. **Then:** `02_async_semaphore_errors.py` - Learn production patterns
3. **Next:** `03_async_progress_and_threads.py` - Master advanced techniques
4. **After that:** `04_async_vs_threads_discussion.py` - Make informed decisions
5. **Continue with:** `05_multiple_semaphores.py` - Real-world multi-API patterns
6. **Finally:** `06_time_based_rate_limiting.py` - Proper rate limiting (crucial!)

---

## 💡 Key Terminology

| Term | Definition | Example |
|------|------------|---------|
| **Coroutine** | Function defined with `async def` | `async def fetch()` |
| **Awaitable** | Object that can be used with `await` | Coroutines, Tasks, Futures |
| **Task** | Scheduled coroutine in event loop | `asyncio.create_task(coro)` |
| **Delegation** | Yielding control with `await` | `result = await coro()` |
| **Semaphore** | Limits concurrent operations | `asyncio.Semaphore(5)` |
| **Rate Limiter** | Limits requests per time window | `RateLimiter(100, 60)` |
| **Event Loop** | Schedules and runs coroutines | Created by `asyncio.run()` |

---

## 🧠 Understanding the Event Loop and GIL

### The Event Loop
The **event loop** is asyncio's scheduler that manages coroutines in a **single thread**:
- Maintains queues of ready, sleeping, and waiting coroutines
- When a coroutine hits `await`, it yields control to the event loop
- Event loop picks another ready coroutine to run
- Eventually returns to the first coroutine when it's ready
- This is **cooperative multitasking** - coroutines voluntarily yield

### The GIL Misconception ⚠️

**Common Misconception**: "Async releases the GIL to achieve concurrency"

**Reality**: Async has **NOTHING** to do with the GIL!

**Key Points:**
- Async runs in **ONE THREAD** - the GIL is held the entire time
- No "GIL release" happens - we achieve concurrency through **cooperative yielding**
- When you `await`, you yield control to the event loop (not release GIL)
- The event loop switches to another coroutine (still same thread, still holding GIL)

**When the GIL Matters:**
- ✅ **Threading**: Multiple threads compete for the GIL, only one runs at a time
- ❌ **Async**: Single thread = GIL held continuously = no competition
- ✅ **Multiprocessing**: Separate processes = separate GILs = true parallelism

**Why Async is Efficient:**
- No GIL contention (only one thread!)
- No thread switching overhead
- Lower memory per concurrent task
- Can handle thousands of connections efficiently

### Async vs Threading

| Aspect | Threading | Async |
|--------|-----------|-------|
| Threads | Multiple | Single |
| Switching | OS preemptive | Cooperative yielding |
| GIL | Critical bottleneck | Irrelevant |
| Overhead | Higher | Lower |
| Best for | I/O + existing code | I/O + high concurrency |

---

## 🔧 Common Patterns

### Pattern 1: Concurrent I/O with throttling
```python
async def fetch_with_limit(urls: List[str], max_concurrent: int = 10):
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def fetch_one(url):
        async with semaphore:
            return await fetch(url)
    
    return await asyncio.gather(*[fetch_one(url) for url in urls])
```

### Pattern 2: Progress tracking
```python
tasks = [asyncio.create_task(fetch(url)) for url in urls]
for coro in asyncio.as_completed(tasks):
    result = await coro
    print(f"Completed: {result}")
```

### Pattern 3: Mixing async and sync
```python
async def hybrid():
    # Async I/O
    data = await fetch_from_api()
    
    # Sync blocking work in thread
    result = await asyncio.to_thread(blocking_function, data)
    
    return result
```

### Pattern 4: Multiple semaphores for different resources
```python
async def process_item(item_id):
    # Separate semaphores for separate resources!
    semaphore_api_a = asyncio.Semaphore(10)  # API A: 10 concurrent
    semaphore_api_b = asyncio.Semaphore(3)   # API B: 3 concurrent
    semaphore_db = asyncio.Semaphore(50)     # DB: 50 concurrent
    
    # Each operation respects its own limit
    async with semaphore_api_a:
        data_a = await fetch_from_api_a(item_id)
    
    async with semaphore_api_b:
        data_b = await fetch_from_api_b(item_id)
    
    async with semaphore_db:
        await save_to_db(data_a, data_b)
```

### Pattern 5: Time-based rate limiting (NOT just concurrency!)
```python
class RateLimiter:
    def __init__(self, max_requests, time_window):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
    
    async def acquire(self):
        now = time.time()
        # Remove old requests
        while self.requests and self.requests[0] < now - self.time_window:
            self.requests.popleft()
        
        # Wait if at limit
        if len(self.requests) >= self.max_requests:
            wait_time = (self.requests[0] + self.time_window) - now
            await asyncio.sleep(wait_time)
        
        self.requests.append(now)

# Use it
rate_limiter = RateLimiter(100, 60)  # 100 requests per 60 seconds
async with rate_limiter:
    await fetch_from_api()
```

---

## 🚀 Where to Go Next

After mastering these scripts, explore:
- Real HTTP requests with `httpx` or `aiohttp`
- Async database operations with `asyncpg` or `motor`
- Web frameworks: FastAPI, aiohttp, Quart
- Advanced patterns: task groups, context managers, timeouts

---

## 📝 Credits

Examples inspired by Luciano Ramalho's **Fluent Python** and adapted for educational purposes.
