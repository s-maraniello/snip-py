# Python Concurrency Models: Complete Guide

> **📖 This is a summary document.** For detailed explanations, code examples, and deep dives, see:
> - **[19-21-concurrency-models.ipynb](19-21-concurrency-models.ipynb)** - Interactive notebook with threading/multiprocessing examples
> - **[21-coroutines/](21-coroutines/)** - Complete async/await learning series (6 progressive scripts)
> - **[examples/](examples/)** - Threading and multiprocessing design patterns

---

## Table of Contents

1. [Glossary](#glossary)
2. [Concurrency Models in Python](#concurrency-models-in-python)
3. [The GIL and Its Impact](#the-gil-and-its-impact)
4. [Decision Guide: When to Use What](#decision-guide-when-to-use-what)
5. [Design Patterns](#design-patterns)
6. [Learning Path](#learning-path)

---

## Glossary

### Core Concepts

**Concurrency**  
The ability to handle multiple tasks, making progress one at a time or in parallel.

  - **Two ways to achieve it:**
    - **(Preemptive) Multitasking**: A single-core CPU achieves concurrency when an **OS scheduler** interleaves the execution of pending tasks by temporarily interrupting them to execute something else, with the intention to resume later.
    - **Parallelism**: The ability to execute multiple computations at the same time (multicore CPU, multiple CPUs, GPU, or cluster).

**Execution Unit**  
Objects that execute code concurrently (either in parallel or multitasking), each with **independent state** and **call stack**. Python supports three kinds:

### The Three Execution Units

**1. Process**  
An **instance** of a computer program while it's running.

- Uses memory and is allocated a slice of CPU time
- **OS manages processes** concurrently
- Each process has **its own private memory** space
- Processes communicate through pipes, sockets, or memory-mapped files
- **Python objects must be serialized** (converted to bytes) to be shared between processes
- **Due to serialization, not all Python objects can be shared across processes**
- Creating multiple processes allows preemptive multitasking or parallelism
- Each process has its **own GIL** (Global Interpreter Lock)

**Related file:** [examples/spinner_proc.py](examples/spinner_proc.py), [examples/queue_procs.py](examples/queue_procs.py)

---

**2. Thread**  
An execution unit within a process.

- When a process starts, it's always single-threaded
- A process can create multiple threads by calling OS APIs
- Threads within a process **share the same memory**, therefore:
  - **Python threads can share ANY objects** (no serialization needed)
  - **Data can be corrupted** if multiple threads access simultaneously (need locks)
- Threads allow preemptive multitasking
- Threads consume **less resources than processes** (due to memory sharing)
- All threads in a process **compete for the same GIL**
- Only **ONE thread can execute Python code at a time** (due to GIL)

**Related files:** 
- [19-21-concurrency-models.ipynb](19-21-concurrency-models.ipynb) - Multi-thread spinner example
- [examples/pool_thread_and_proc.py](examples/pool_thread_and_proc.py) - ThreadPoolExecutor examples

---

**3. Coroutine**  
A function that can suspend itself and resume later.

- Two types:
  - **Classic coroutines**: Built from generator functions
  - **Native coroutines**: Defined with `async def`
- Python coroutines **run within a single thread** under an event loop's supervision
- Frameworks like asyncio, Curio, or Trio provide the event loop
- Support **cooperative multitasking**: Each coroutine explicitly yields control with `yield` or `await`
- **Not parallel** - concurrent but in a single thread
- **Blocking code in one coroutine blocks ALL coroutines** (and the event loop)
- Each coroutine consumes **far fewer resources** than a thread or process
- **No GIL contention** (runs in single thread, GIL held continuously)

**Related files:**  
- [21-coroutines/](21-coroutines/) - Complete async learning series (6 scripts)
- [19-21-concurrency-models.ipynb](19-21-concurrency-models.ipynb) - Some definitions.

---


## Concurrency Models in Python

### Threading (Preemptive Multitasking)

**How it works:**
- OS scheduler manages multiple threads
- Threads interrupt each other preemptively (OS decides when)
- Multiple threads within one process
- All threads share the same memory and **compete for the GIL**

**Characteristics:**
- ✅ Great for **I/O-bound work** (network, disk, database)
- ✅ Works with **existing synchronous code**
- ✅ Can share Python objects directly (no serialization)
- ❌ **Only ONE thread executes Python code at a time** (GIL!)
- ❌ **NO speedup for pure Python CPU-bound work** (GIL ensures sequential execution)
- ❌ Higher overhead than async (thread creation, context switching)
- ⚠️ Risk of data corruption (need locks for shared mutable data)

**When threads achieve parallelism:**
- During I/O operations (threads release GIL while waiting)
- When using GIL-releasing libraries (NumPy, Pandas, compiled extensions)
- **NOT with pure Python CPU computations**

**Related files:** [19-21-concurrency-models.ipynb](19-21-concurrency-models.ipynb), [examples/pool_thread_and_proc.py](examples/pool_thread_and_proc.py)

---

### Async/Await (Cooperative Multitasking)

**How it works:**
- Event loop scheduler manages coroutines
- Coroutines voluntarily yield control with `await`
- Single thread (no parallelism, just concurrency)
- **No GIL contention** (only one thread)

**Characteristics:**
- ✅ **Excellent for async I/O-bound work** with high concurrency (1000s of connections)
  - Network I/O with async libraries (httpx, aiohttp, websockets)
  - Database I/O with async drivers (asyncpg, motor, aiosqlite)
  - File I/O with async libraries (aiofiles)
- ✅ **Very low overhead** (no thread creation, no context switching)
- ✅ **No GIL contention** (single thread)
- ✅ Precise control over concurrency
- ❌ **"All-or-nothing"** - async functions can only be called by async functions
- ❌ **Blocking I/O blocks the event loop** - even if it releases the GIL!
  - Standard file I/O: `open()`, `read()`, `write()` → Use `asyncio.to_thread()` or aiofiles
  - Sync HTTP: `requests.get()` → Use async libraries (httpx, aiohttp) or `to_thread()`
  - Sync database: `sqlite3`, `psycopg2` → Use async drivers or `to_thread()`
- ❌ **No speedup for CPU-bound work** (single thread alone)

**The "Color Problem":**
Functions are "colored" - async (red) or sync (blue). Red functions can only be called by other red functions. This cascades up the call stack.

**Solutions for mixing async with blocking I/O/CPU work:**
- `asyncio.to_thread()` - Run blocking code in thread pool (prevents event loop blocking)
  - **Always helps:** Keeps event loop responsive for other coroutines
  - **Use for:** Blocking I/O (file operations, sync database, requests library)
  - **Bonus speedup:** Parallel execution if work releases GIL (I/O, NumPy, etc.)
  - **No speedup:** Pure Python CPU work in threads still competes for GIL
- Async-native libraries - Preferred when available (httpx vs requests, asyncpg vs psycopg2)
- `asyncio.run()` - Entry point from sync to async (at boundaries only)

**Critical: Why blocking I/O needs special handling in async:**
Even though `open()`, `read()`, `write()` release the GIL, they still block the event loop because the coroutine waits synchronously. The event loop can't switch to other coroutines during this time!

**Related files:** [21-coroutines/](21-coroutines/) (complete learning series), [21-coroutines/04_async_vs_threads_discussion.py](21-coroutines/04_async_vs_threads_discussion.py)

---

### Multiprocessing (True Parallelism)

**How it works:**
- OS manages multiple processes
- Each process has its own Python interpreter
- Each process has its own GIL (no GIL contention!)
- Processes have isolated memory spaces

**Characteristics:**
- ✅ **TRUE PARALLELISM** for CPU-bound work
- ✅ Each process has its own GIL (no contention)
- ✅ Can utilize multiple CPU cores simultaneously
- ❌ High overhead (process creation, memory duplication)
- ❌ **Must serialize data** to share between processes
- ❌ Not all Python objects can be serialized
- ❌ Higher memory usage (separate memory spaces)

**When to use:**
- CPU-intensive pure Python code
- Need to utilize multiple CPU cores
- Can parallelize independent chunks of work

**Related files:** [examples/spinner_proc.py](examples/spinner_proc.py), [examples/queue_procs.py](examples/queue_procs.py), [examples/pool_thread_and_proc.py](examples/pool_thread_and_proc.py)

---

## The GIL and Its Impact

### What is the GIL?

The **Global Interpreter Lock (GIL)** is a mutex in CPython that protects access to Python objects, **allowing only ONE thread to execute Python bytecode at a time**.

**Key facts:**
- Only relevant for **threading** (not async, not multiprocessing)
- Every Python process has its own GIL
- You **cannot control or release the GIL** from Python code
- The GIL is released automatically:
  - Every 5ms (to allow other threads a turn)
  - During I/O operations (disk, network, `time.sleep()`)
  - By some C extensions (NumPy, Pandas, compression libraries)

### GIL Impact by Concurrency Model

| Model | GIL Impact | Why |
|-------|------------|-----|
| **Threading** | 🔴 **CRITICAL** | Threads compete for GIL, only one runs at a time |
| **Async** | 🟢 **IRRELEVANT** | Single thread, GIL held continuously, no competition |
| **Multiprocessing** | 🟢 **IRRELEVANT** | Each process has its own GIL, true parallelism |

### Critical Misconception: Threading and CPU Work

❌ **WRONG:** "I can use threads to speed up CPU-intensive work"  
✅ **CORRECT:** "Threading provides NO speedup for pure Python CPU work"

**Why?** The GIL ensures only one thread executes Python code at a time:

```python
# Two CPU-intensive functions
def compute_fibonacci(n):  # Pure Python CPU work
    # ... lots of Python calculations ...

# Sequential: 10 seconds
compute_fibonacci(35)  # 5 seconds
compute_fibonacci(35)  # 5 seconds

# With threading: STILL ~10 seconds (or worse!)
with ThreadPoolExecutor() as executor:
    future1 = executor.submit(compute_fibonacci, 35)
    future2 = executor.submit(compute_fibonacci, 35)
    # Threads compete for GIL, essentially run sequentially
    # Plus context switching overhead!
```

**When threading DOES help:**
1. **I/O operations** - Threads release GIL during I/O
2. **GIL-releasing libraries** - NumPy, Pandas, C extensions release GIL during computation
3. **NOT pure Python loops, list comprehensions, or string processing**

**For pure Python CPU work:** Use **multiprocessing**, not threading!

**See:** [21-coroutines/04_async_vs_threads_discussion.py](21-coroutines/04_async_vs_threads_discussion.py) for detailed explanation with examples.

---

## Decision Guide: When to Use What

### Quick Reference Table

| Scenario | Best Choice | Why | Alternatives |
|----------|-------------|-----|--------------|
| **I/O-bound: Async libraries available** (httpx, aiohttp, asyncpg) | **Async** | Lowest overhead, handles thousands efficiently | Threading (simpler) |
| **I/O-bound: Blocking/sync libraries only** (requests, psycopg2, file I/O) | **Threading** | Blocking I/O would block event loop | Hybrid (async + `to_thread()`) |
| **I/O-bound: High concurrency** (100s-1000s connections) | **Async** (with async libs) | Handles massive concurrency efficiently | Threading won't scale |
| **I/O-bound: Simple/modest concurrency** | **Threading** | Works with sync code, easier to understand | Async (for better scalability) |
| **CPU-bound: Pure Python** | **Multiprocessing** | Only way to use multiple cores | None (GIL prevents threads/async) |
| **CPU-bound: NumPy/Pandas** | **Threading or Async + `to_thread()`** | These libraries release GIL | Multiprocessing (overkill) |
| **Mixed: Async I/O + blocking I/O + CPU** | **Async + `to_thread()`** (Hybrid) | Best of both worlds | Threading (simpler) |
| **Starting new project** | **Async** (if async libs exist) | Future-proof, scalable | Threading (team familiarity) |
| **Legacy codebase migration** | **Hybrid** (async + threads) | Gradual migration path | Full rewrite to async |

### Detailed Decision Guide

#### Use **Async (asyncio)** When:
✅ **Async I/O-bound work** (network requests, database, APIs)  
✅ **Many concurrent operations** (100s or 1000s)  
✅ **Starting new project** with async-compatible libraries available  
✅ **Need precise control** over concurrency  
✅ **Low overhead is critical**  

❌ **But NOT When:**  
⚠️ Working with **sync-only libraries** (no async version available)  
⚠️ Heavy use of **blocking I/O** (standard file operations, sync databases)  
⚠️ Small codebase where threading is simpler  
⚠️ Team unfamiliar with async patterns  

**Important:** Async is for **async I/O**, not all I/O!
- ✅ Use: httpx, aiohttp, asyncpg, aiofiles, websockets
- ❌ Avoid directly in coroutines: open(), read(), write(), requests, psycopg2
- 🔧 Solution: Use `asyncio.to_thread()` for blocking I/O or switch to async libraries  

**Key patterns:**
- Semaphores for rate limiting → [21-coroutines/02_async_semaphore_errors.py](21-coroutines/02_async_semaphore_errors.py)
- Multiple resource limits → [21-coroutines/05_multiple_semaphores.py](21-coroutines/05_multiple_semaphores.py)
- Time-based rate limits → [21-coroutines/06_time_based_rate_limiting.py](21-coroutines/06_time_based_rate_limiting.py)
- Progress tracking → [21-coroutines/03_async_progress_and_threads.py](21-coroutines/03_async_progress_and_threads.py)

---

#### Use **Threading** When:
✅ **I/O-bound work** with existing synchronous code  
✅ **Modest concurrency** needs (< 100 concurrent operations)  
✅ **Need to integrate** with sync-only libraries  
✅ Want **simple parallel execution** without rewriting code  
✅ Codebase is **already synchronous**  

❌ **But NOT When:**  
⚠️ **CPU-bound pure Python work** (GIL limits to single core)  
⚠️ Need 1000s of concurrent operations (thread overhead)  

**See:** [19-21-concurrency-models.ipynb](19-21-concurrency-models.ipynb), [examples/pool_thread_and_proc.py](examples/pool_thread_and_proc.py)

---

#### Use **Multiprocessing** When:
✅ **CPU-bound work** (calculations, data processing)  
✅ Need to **utilize multiple CPU cores**  
✅ Can **parallelize independent chunks** of work  
✅ Willing to handle serialization/IPC overhead  

❌ **But NOT When:**  
⚠️ I/O-bound work (unnecessary overhead)  
⚠️ Shared state is complex (IPC is expensive)  
⚠️ High process creation overhead is a concern  

**See:** [examples/spinner_proc.py](examples/spinner_proc.py), [examples/queue_procs.py](examples/queue_procs.py)

---

#### Use **Hybrid Approach** (Async + Threading) When:
✅ Mix of **I/O-bound** (use async) and **blocking operations** (use threads)  
✅ Using **GIL-releasing libraries** (NumPy, Pandas) from async code  
✅ **Migrating** large sync codebase to async gradually  

**Why use asyncio.to_thread():**

1. **Always prevents event loop blocking** → Other coroutines can run
   - Even pure Python CPU work benefits from this (keeps app responsive)
   - The event loop remains free to handle other async tasks
   
2. **Bonus: Actual parallelism if work releases GIL**
   - I/O operations: Threads release GIL while waiting → Parallel I/O
   - NumPy/Pandas: These libraries release GIL → Parallel computation
   - Pure Python CPU: Threads compete for GIL → Sequential (but event loop free)

**Pattern:**
```python
async def hybrid_pipeline():
    # ✅ Async I/O - native async library (perfect!)
    data = await fetch_from_api_async()  # httpx, aiohttp, etc.
    
    # ❌ Blocking I/O - standard file operations block event loop
    # Must use to_thread() or aiofiles
    await asyncio.to_thread(write_to_file, data)  # open(), write() in thread
    # OR: async with aiofiles.open('file.txt', 'w') as f: await f.write(data)
    
    # ❌ NumPy/Pandas - releases GIL but still blocking
    # Must use to_thread() for event loop responsiveness
    processed = await asyncio.to_thread(numpy_computation, data)
    
    # ❌ Pure Python CPU - blocks event loop, competes for GIL in thread
    # to_thread() keeps event loop free, but no CPU speedup
    result = await asyncio.to_thread(pure_python_calculation, processed)
    
    # ✅ Async database - native async driver (perfect!)
    await save_to_db_async(result)  # asyncpg, motor, etc.
```

**Summary:**
- **Async I/O with async libs** (httpx, asyncpg, aiohttp) → Direct await ✅✅
- **Blocking I/O** (file ops, requests, sync DB) → `to_thread()` (keeps loop free) ✅
- **GIL-releasing work** (NumPy, Pandas) → `to_thread()` (parallelism + loop free) ✅✅
- **Pure Python CPU** → `to_thread()` (loop free, but no CPU speedup) ✅
- **For CPU parallelism of pure Python:** Use multiprocessing instead!

⚠️ **Common misconception:** "All I/O works great with async"  
✅ **Reality:** Only **async I/O** works great. Blocking I/O blocks the event loop!

**See:** [21-coroutines/03_async_progress_and_threads.py](21-coroutines/03_async_progress_and_threads.py), [21-coroutines/04_async_vs_threads_discussion.py](21-coroutines/04_async_vs_threads_discussion.py)

---

### Real-World Example: Domain Checking

**Scenario:** Check availability of 1000 domains

**Analysis:**
- I/O-bound operation (network requests)
- High concurrency (1000s of requests)
- May need rate limiting

**Recommendations:**

| Approach | Rating | Why |
|----------|--------|-----|
| **Async** | 🏆 **IDEAL** | Low overhead, handles 1000s efficiently, modern HTTP libraries (httpx, aiohttp) |
| **Threading** | ✅ **ACCEPTABLE** | Works with `requests` library, simpler for teams unfamiliar with async |
| **Multiprocessing** | ❌ **OVERKILL** | Unnecessary overhead for I/O-bound work |

**Verdict:** Async wins for scalability, Threading wins for simplicity.

**See:** [21-coroutines/04_async_vs_threads_discussion.py](21-coroutines/04_async_vs_threads_discussion.py) for performance comparison.

---

## Design Patterns

This repository demonstrates several concurrency design patterns:

### 1. Supervisor Pattern
A main process/thread spins up a secondary process/thread for concurrent work (e.g., progress updates).

**Implementations:**
- Multiprocessing: [examples/spinner_proc.py](examples/spinner_proc.py)
- Threading: [19-21-concurrency-models.ipynb](19-21-concurrency-models.ipynb) (inline example)
- Async: [21-coroutines/spinner_async.py](21-coroutines/spinner_async.py)

---

### 2. Queue-Based Workers
Jobs are sent to a queue and processed by multiple workers.

**Implementations:**
- Multiprocessing: [examples/queue_procs.py](examples/queue_procs.py)
- Threading: [Fluent Python example](https://github.com/fluentpython/example-code-2e/blob/master/19-concurrency/primes/threads.py)
- Pattern: [examples/primes.py](examples/primes.py)

---

### 3. Pool Executors
Jobs are submitted to a pool of executors (abstraction over workers).

**Implementations:**
- Both threading and multiprocessing: [examples/pool_thread_and_proc.py](examples/pool_thread_and_proc.py)

**Two patterns shown:**
- **Simple**: Using `map()` - preserves order, no error handling
- **Advanced**: Using `submit()` + `as_completed()` - error handling, results as ready

**For async equivalent:** [21-coroutines/03_async_progress_and_threads.py](21-coroutines/03_async_progress_and_threads.py)

---

### 4. Async Patterns (In 21-coroutines/)

- **Semaphores for throttling:** [02_async_semaphore_errors.py](21-coroutines/02_async_semaphore_errors.py)
- **Multiple semaphores:** [05_multiple_semaphores.py](21-coroutines/05_multiple_semaphores.py)
- **Time-based rate limiting:** [06_time_based_rate_limiting.py](21-coroutines/06_time_based_rate_limiting.py)
- **Progress tracking:** [03_async_progress_and_threads.py](21-coroutines/03_async_progress_and_threads.py)
- **Hybrid async + threads:** [03_async_progress_and_threads.py](21-coroutines/03_async_progress_and_threads.py)

---

## Learning Path

### For Beginners: Start Here

1. **Read the glossary** in this README (especially Process, Thread, Coroutine, GIL)
2. **Understand the decision guide** (when to use what)
3. **Work through [19-21-concurrency-models.ipynb](19-21-concurrency-models.ipynb)** - Interactive examples of threading/multiprocessing
4. **Follow the async series:** [21-coroutines/README_ASYNC_SERIES.md](21-coroutines/README_ASYNC_SERIES.md)

### For Async Learners

Complete progressive series in [21-coroutines/](21-coroutines/):

1. **[01_async_basics.py](21-coroutines/01_async_basics.py)** - `await` vs `create_task()`, `gather()`
2. **[02_async_semaphore_errors.py](21-coroutines/02_async_semaphore_errors.py)** - Semaphores, error handling
3. **[03_async_progress_and_threads.py](21-coroutines/03_async_progress_and_threads.py)** - Progress tracking, `to_thread()`
4. **[04_async_vs_threads_discussion.py](21-coroutines/04_async_vs_threads_discussion.py)** - Decision guide, GIL deep dive
5. **[05_multiple_semaphores.py](21-coroutines/05_multiple_semaphores.py)** - Multiple resource limits
6. **[06_time_based_rate_limiting.py](21-coroutines/06_time_based_rate_limiting.py)** - Rate limiters (not semaphores!)

### For Threading/Multiprocessing

1. **Read [19-21-concurrency-models.ipynb](19-21-concurrency-models.ipynb)** - Core concepts and examples
2. **Study the examples:**
   - [examples/spinner_proc.py](examples/spinner_proc.py) - Multiprocessing basics
   - [examples/pool_thread_and_proc.py](examples/pool_thread_and_proc.py) - Executor patterns
   - [examples/queue_procs.py](examples/queue_procs.py) - Queue-based workers

### Understanding the GIL

**Essential reading:**
- This README's [GIL section](#the-gil-and-its-impact)
- [21-coroutines/04_async_vs_threads_discussion.py](21-coroutines/04_async_vs_threads_discussion.py) - Comprehensive GIL explanation
- [19-21-concurrency-models.ipynb](19-21-concurrency-models.ipynb) - "How concurrency applies in Python" section

**Key takeaways:**
- Threading ≠ parallelism for pure Python CPU work
- GIL only matters for threading (not async, not multiprocessing)
- I/O operations and some libraries release the GIL

---

## Quick Links

### By Topic

**Threading:**
- [19-21-concurrency-models.ipynb](19-21-concurrency-models.ipynb) - Examples and explanations
- [examples/pool_thread_and_proc.py](examples/pool_thread_and_proc.py) - ThreadPoolExecutor

**Multiprocessing:**
- [examples/spinner_proc.py](examples/spinner_proc.py) - Process basics
- [examples/queue_procs.py](examples/queue_procs.py) - Queue pattern
- [examples/pool_thread_and_proc.py](examples/pool_thread_and_proc.py) - ProcessPoolExecutor

**Async/Await:**
- [21-coroutines/README_ASYNC_SERIES.md](21-coroutines/README_ASYNC_SERIES.md) - Complete learning path
- [21-coroutines/01_async_basics.py](21-coroutines/01_async_basics.py) - Start here
- [21-coroutines/04_async_vs_threads_discussion.py](21-coroutines/04_async_vs_threads_discussion.py) - Decision guide

**The GIL:**
- [21-coroutines/04_async_vs_threads_discussion.py](21-coroutines/04_async_vs_threads_discussion.py) - Comprehensive explanation
- [19-21-concurrency-models.ipynb](19-21-concurrency-models.ipynb) - "How concurrency applies in Python"

**Design Patterns:**
- [examples/](examples/) - Threading/multiprocessing patterns
- [21-coroutines/](21-coroutines/) - Async patterns

---

## Credits

These materials are adapted from:
- **Fluent Python (2nd Edition)** by Luciano Ramalho - Chapters 19, 20, 21
- [Fluent Python Examples Repository](https://github.com/fluentpython/example-code-2e)

---

## Summary

**Remember:**
1. **Async** = Single thread, cooperative, great for **async I/O** with high concurrency
   - ⚠️ Requires async-compatible libraries (httpx, not requests; asyncpg, not psycopg2)
   - ⚠️ Blocking I/O (even if it releases GIL) blocks the event loop!
2. **Threading** = Multiple threads (but only one runs Python at a time), good for I/O with existing code
   - ✅ Works with blocking I/O (file operations, requests, sync databases)
3. **Multiprocessing** = True parallelism, only solution for CPU-bound pure Python
4. **GIL** = Only matters for threading (not async, not multiprocessing)
5. **Threading does NOT speed up pure Python CPU work!** (critical misconception)
6. **Async does NOT speed up blocking I/O!** (must use async libraries or `to_thread()`)

**When in doubt:**
- I/O-bound + async libraries available → **Async**
- I/O-bound + blocking/sync libraries → **Threading**
- CPU-bound → **Multiprocessing**
- Mixed (async I/O + blocking I/O + CPU) → **Hybrid (async + threads)**

For detailed explanations and code examples, explore the linked files and scripts! 🚀
