# Python native structures


## Words in the problem → what to reach for

| If the problem says...                                           | Reach for                                         |
| ---------------------------------------------------------------- | ------------------------------------------------- |
| "queue", "in order of arrival", "fewest steps", "level by level" | `deque`(BFS)                                    |
| "undo", "nested", "matching brackets", "go deep first"           | `list`as a stack (DFS)                          |
| "have we seen", "unique", "duplicates"                           | `set`                                           |
| "how many times", "frequency", "most common"                     | `Counter`                                       |
| "group by", "for each X, the list of Y"                          | `defaultdict(list)`                             |
| "look up by id", "pair that sums to"                             | `dict`                                          |
| "k largest / smallest", "kth", "top k"                           | `heapq`(size-k heap,`nlargest`,`nsmallest`) |
| "next earliest", "most urgent", "repeatedly take the best"       | `heapq`priority queue                           |
| "merge sorted"                                                   | `heapq.merge`                                   |
| "shortest path" with weights                                     | `heapq`(Dijkstra)                               |
| "in sorted data", "how many ≤ x", "which bucket"                | `bisect`                                        |
| "last k", "window"                                               | `deque(maxlen=k)`                               |

## Use case → what to use

### Queues, stacks and windows

| Use case                             | Use                                         | Snippet                                                                                                                    | Cost            |
| ------------------------------------ | ------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | --------------- |
| FIFO queue, BFS                      | `deque`                                   | `q.append(x)`;`x = q.popleft()`                                                                                        | O(1) each       |
| LIFO stack, DFS, undo                | `list`                                    | `st.append(x)`;`x = st.pop()`                                                                                          | O(1) each       |
| Keep only the last k items           | `deque(maxlen=k)`                         | `last = deque(maxlen=k)`;`last.append(x)`                                                                              | O(1) per append |
| Max (or min) of every sliding window | `deque`of indexes, values kept decreasing | Pop from the right while`nums[q[-1]] <= x`; pop from the left when the index leaves the window; the max is`nums[q[0]]` | O(n) total      |
| Shortest path, unweighted            | `deque`(BFS)                              | Pop left, push neighbours, track`dist`in a dict                                                                          | O(V + E)        |

### Lookups, membership and counting

| Use case                            | Use                    | Snippet                                                                            | Cost                 |
| ----------------------------------- | ---------------------- | ---------------------------------------------------------------------------------- | -------------------- |
| Look up by key / id                 | `dict`               | `d[key]`,`d.get(key, default)`                                                 | O(1)                 |
| "Have I seen this?"                 | `set`                | `if x in seen: ...`;`seen.add(x)`                                              | O(1)                 |
| Remove duplicates, keep order       | `dict.fromkeys`      | `list(dict.fromkeys(items))`                                                     | O(n)                 |
| Remove duplicates, order irrelevant | `set`                | `set(items)`                                                                     | O(n)                 |
| Items in both collections           | `set`                | `set(a) & set(b)`                                                                | O(len a + len b)     |
| Pair summing to a target            | `dict`value → index | `if target - x in idx: ...`;`idx[x] = i`                                       | O(n) total           |
| Count occurrences                   | `Counter`            | `Counter(items)`;`c[x] += 1`                                                   | O(n) to build        |
| k most frequent                     | `Counter`            | `c.most_common(k)`(ties in first-seen order)                                     | O(n log k)           |
| k most frequent, ties by key        | `heapq.nsmallest`    | `nsmallest(k, c.items(), key=lambda kv: (-kv[1], kv[0]))`                        | O(n log k)           |
| Group items by a key                | `defaultdict(list)`  | `groups[key(x)].append(x)`                                                       | O(n)                 |
| Graph adjacency list                | `defaultdict(list)`  | `adj[u].append(v)`                                                               | O(E)                 |
| A grid cell, or a state, as a key   | `tuple`              | `seen.add((row, col))`;`memo[tuple(state)]`                                    | O(1) per lookup      |
| Memoize a recursive function        | `functools.cache`    | `@cache`above the function                                                       | O(1) per cached call |
| LRU cache with a size limit         | `OrderedDict`        | On read:`d.move_to_end(k)`. On write: if over capacity,`d.popitem(last=False)` | O(1) each            |

### Priority, top-k and ordering

| Use case                             | Use                                          | Snippet                                                                                             | Cost                               |
| ------------------------------------ | -------------------------------------------- | --------------------------------------------------------------------------------------------------- | ---------------------------------- |
| Repeatedly take the smallest         | `heapq`                                    | `heappush(h, x)`;`heappop(h)`; peek`h[0]`                                                     | O(log n); peek O(1)                |
| Repeatedly take the largest          | `heapq`with negation (or`*_max`in 3.14+) | `heappush(h, -x)`;`-heappop(h)`                                                                 | O(log n)                           |
| Priority queue with payloads         | `heapq`+ tie-break counter                 | `heappush(h, (prio, next(counter), item))`                                                        | O(log n)                           |
| Turn a whole list into a heap        | `heapq.heapify`                            | `heapify(lst)`(in place)                                                                          | O(n)                               |
| k largest / smallest of a list       | `heapq.nlargest`/`nsmallest`             | `nlargest(k, nums, key=...)`                                                                      | O(n log k)                         |
| Top k of a stream (bounded memory)   | Size-k min-heap                              | Push until full; then`heapreplace(h, x)`if`x > h[0]`                                            | O(n log k), O(k) memory            |
| kth largest                          | Size-k min-heap                              | After the stream, the answer is`h[0]`                                                             | O(n log k)                         |
| Running median                       | Two heaps                                    | Max-heap (negated) of the lower half, min-heap of the upper half; rebalance so sizes differ by ≤ 1 | O(log n) per add, O(1) median      |
| Top k when counts keep changing      | `dict`+ compute at query time (default)    | `counts[pid] += 1`;`nsmallest(k, counts.items(), key=...)`                                      | O(1) update, O(n log k) query      |
| ↳ updates and queries both frequent | `dict`+ lazy heap                          | Push`(-count, pid)`per update; on query skip entries whose count doesn't match the dict           | O(log m) update, ~O(k log m) query |
| ↳ queries constant, updates rare    | `dict`+ sorted list (`bisect`)           | Remove the old`(-count, pid)`,`insort`the new one; top k is`ranked[:k]`                       | O(n) update, O(k) query            |
| Merge k sorted lists                 | `heapq.merge`                              | `list(merge(*lists))`                                                                             | O(N log k)                         |
| Scheduling, minimum meeting rooms    | Sort + min-heap of end times                 | For each meeting by start: pop if`h[0] <= start`; push its end; answer = max heap size            | O(n log n)                         |
| Shortest path, weighted (Dijkstra)   | `heapq`+ lazy deletion                     | Pop`(d, u)`; skip if`d > dist[u]`; push improved`(nd, v)`                                     | O((V + E) log V)                   |

### Sorting and searching

| Use case                                 | Use                                                                            | Snippet                                                   | Cost            |
| ---------------------------------------- | ------------------------------------------------------------------------------ | --------------------------------------------------------- | --------------- |
| Sort a dict by value                     | `sorted`on items                                                             | `sorted(d.items(), key=lambda kv: kv[1], reverse=True)` | O(n log n)      |
| Sorted dict to keep                      | `dict(sorted(...))`                                                          | `dict(sorted(d.items(), key=lambda kv: kv[1]))`         | O(n log n)      |
| Sort by several keys, mixed directions   | Key tuple with negation                                                        | `sorted(rows, key=lambda r: (-r.score, r.name))`        | O(n log n)      |
| ↳ key that can't be negated (strings)   | Two stable passes                                                              | Sort by the secondary key, then by the primary key        | O(n log n)      |
| Key with the largest value               | `max`with a key                                                              | `max(d, key=d.get)`                                     | O(n)            |
| Find a position in sorted data           | `bisect`                                                                     | `bisect_left(arr, x)`                                   | O(log n)        |
| Count values ≤ x in sorted data         | `bisect_right`                                                               | `bisect_right(arr, x)`                                  | O(log n)        |
| Count values in [lo, hi]                 | `bisect`twice                                                                | `bisect_right(arr, hi) - bisect_left(arr, lo)`          | O(log n)        |
| Map a value to a bucket (score → grade) | `bisect`on breakpoints                                                       | `grades[bisect(breakpoints, score)]`                    | O(log n)        |
| Keep a list sorted, few inserts          | `bisect.insort`                                                              | `insort(arr, x)`                                        | O(n) per insert |
| Keep a list sorted, many inserts         | Heap (if you only need the min) or`sortedcontainers.SortedList`(third-party) |                                                           | O(log n)        |

### Strings

| Use case                         | Use         | Snippet                                     | Cost            |
| -------------------------------- | ----------- | ------------------------------------------- | --------------- |
| Build a string from many pieces  | `"".join` | `parts.append(p)`; then`"".join(parts)` | O(total length) |
| Count characters, check anagrams | `Counter` | `Counter(a) == Counter(b)`                | O(n)            |
| Character set membership         | `set`     | `vowels = set("aeiou")`;`ch in vowels`  | O(1)            |
