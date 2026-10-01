# Python Best Practices Knowledge Base

## Sorting and Mutation

Use `sorted(items)` to return a new sorted list without mutating the input.
Use `list.sort()` only when in-place mutation is intended.
For unique + sorted: `sorted(set(items))` returns a new list with unique items.

Example:
```python
def unique_sorted(items):
    return sorted(set(items))
