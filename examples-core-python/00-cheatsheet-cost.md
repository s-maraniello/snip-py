
# Python data structures: operations and their cost

Average-case time complexity in CPython. n is the size of the collection, k the size of the other input (or the `k` argument).

**The two questions behind every row:** 

* *Do I know the address, or must I search?*
* *Does this operation make things move?*

| Structure                           | Operation                                                                                | Cost                        | Why / notes                                                     |
| ----------------------------------- | ---------------------------------------------------------------------------------------- | --------------------------- | --------------------------------------------------------------- |
| **list**                      | `lst[i]`,`lst[i] = x`                                                                | O(1)                        | Address arithmetic:`start + i × 8`                           |
|                                     | `lst.append(x)`                                                                        | O(1) amortized              | Spare capacity at the end; an occasional O(n) regrow            |
|                                     | `lst.pop()`                                                                            | O(1)                        | Nothing moves                                                   |
|                                     | `lst.pop(i)`,`del lst[i]`,`lst.insert(i, x)`                                       | O(n − i)                   | Everything after`i`shifts; worst at the front                 |
|                                     | `lst.pop(0)`,`lst.insert(0, x)`                                                      | O(n)                        | Everything shifts. Use a`deque`instead                        |
|                                     | `x in lst`,`lst.index(x)`,`lst.count(x)`,`lst.remove(x)`                         | O(n)                        | Walk and compare                                                |
|                                     | `lst[a:b]`                                                                             | O(b − a)                   | A slice is a new list (copy)                                    |
|                                     | `lst.extend(other)`,`lst + other`                                                    | O(k) / O(n + k)             | `+`builds a new list                                          |
|                                     | `lst.sort()`,`sorted(lst)`                                                           | O(n log n)                  | Timsort; ~O(n) if nearly sorted; stable                         |
|                                     | `min(lst)`,`max(lst)`,`sum(lst)`                                                   | O(n)                        | Full scan                                                       |
|                                     | `lst.reverse()`,`lst.copy()`                                                         | O(n)                        |                                                                 |
|                                     | `len(lst)`                                                                             | O(1)                        | Stored, not counted                                             |
| **deque**                     | `append`,`appendleft`,`pop`,`popleft`                                            | O(1)                        | Moving bookmarks on a chain of 64-slot blocks                   |
|                                     | `dq[i]`                                                                                | O(min(i, n − i))           | Walks blocks from the nearer end                                |
|                                     | `x in dq`                                                                              | O(n)                        | Walk and compare                                                |
|                                     | `dq.extend(it)`,`dq.extendleft(it)`                                                  | O(k)                        |                                                                 |
|                                     | `dq.rotate(r)`                                                                         | O(r)                        |                                                                 |
|                                     | `deque(maxlen=k)`                                                                      | O(1) per append             | Drops from the other end when full                              |
| **dict**                      | `d[key]`,`d[key] = v`,`key in d`,`d.get(key)`                                    | O(1) average                | Hash, then jump to the slot                                     |
|                                     | `del d[key]`,`d.pop(key)`                                                            | O(1) average                |                                                                 |
|                                     | `d.popitem()`                                                                          | O(1)                        | Removes the last inserted item                                  |
|                                     | Iterate`d`,`d.items()`,`d.values()`                                                | O(n)                        | Insertion order (Python 3.7+)                                   |
|                                     | `d.copy()`,`dict(sorted(d.items()))`                                                 | O(n) / O(n log n)           |                                                                 |
|                                     | Key with the max value                                                                   | O(n)                        | No ordering by value:`max(d, key=d.get)`                      |
| **set**                       | `s.add(x)`,`x in s`,`s.remove(x)`,`s.discard(x)`                                 | O(1) average                | Same hash table as dict, keys only                              |
|                                     | `s & t`(intersection)                                                                  | O(min(len s, len t))        |                                                                 |
|                                     | `s.union(t)`,`s - t`                                                                 | O(len s + len t) / O(len s) |                                                                 |
|                                     | `set(lst)`                                                                             | O(n)                        | Pay once; then every membership test is O(1)                    |
| **Counter**                   | `Counter(items)`                                                                       | O(n)                        | A dict of counts                                                |
|                                     | `c[x]`,`c[x] += 1`                                                                   | O(1)                        | Missing keys read as 0                                          |
|                                     | `c.most_common(k)`                                                                     | O(n log k)                  | Heap internally; ties in first-seen order                       |
|                                     | `c.most_common()`                                                                      | O(n log n)                  | Full sort                                                       |
| **defaultdict**               | `dd[key]`(missing key)                                                                 | O(1)                        | Creates the default (`list()`,`int()`…) on first touch     |
| **heapq**(min-heap on a list) | `h[0]`                                                                                 | O(1)                        | Peek at the smallest                                            |
|                                     | `heapq.heappush(h, x)`                                                                 | O(log n)                    | Append, then bubble up one path                                 |
|                                     | `heapq.heappop(h)`                                                                     | O(log n)                    | Last item to the root, then sink down one path                  |
|                                     | `heapq.heapify(lst)`                                                                   | O(n)                        | In place; most nodes sit near the bottom and sink a short way   |
|                                     | `heapq.heappushpop(h, x)`                                                              | O(log n)                    | Push, then pop: returns`x`itself if it's smaller than the min |
|                                     | `heapq.heapreplace(h, x)`                                                              | O(log n)                    | Pop, then push: always returns the old min                      |
|                                     | `heapq.nlargest(k, it, key=)`,`heapq.nsmallest(k, it, key=)`                         | O(n log k)                  | Uses`min`/`max`when k = 1 and`sorted`when k ≥ n          |
|                                     | `heapq.merge(*sorted_its, key=, reverse=)`                                             | O(N log k)                  | Lazy; k inputs, N items in total                                |
|                                     | `heapify_max`,`heappush_max`,`heappop_max`,`heappushpop_max`,`heapreplace_max` | O(n) / O(log n)             | Python 3.14+. Otherwise negate values (`-x`)                  |
|                                     | Find or remove an arbitrary item                                                         | O(n)                        | Avoid: use lazy deletion (push a new entry, skip stale ones)    |
| **bisect**(on a sorted list)  | `bisect_left`,`bisect_right`,`bisect`                                              | O(log n)                    | Binary search                                                   |
|                                     | `insort(lst, x)`                                                                       | O(n)                        | O(log n) to find + O(n) to shift                                |
| **str**                       | `"".join(parts)`                                                                       | O(total length)             | Build strings this way                                          |
|                                     | `s + t`,`s += t`in a loop                                                            | O(len s + len t) each       | Strings are immutable: a loop can become O(n²)                 |
|                                     | `s[a:b]`                                                                               | O(b − a)                   | Copy                                                            |
|                                     | `sub in s`                                                                             | O(n) typical                |                                                                 |
| **tuple**                     | `t[i]`                                                                                 | O(1)                        | Like a list, but immutable and hashable: usable as a dict key   |
