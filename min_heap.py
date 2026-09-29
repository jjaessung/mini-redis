"""Array-backed binary minimum heap."""


class MinHeap:
    """Minimum heap for comparable values such as ``(expire_at, key)``."""

    def __init__(self):
        self._items = []

    def push(self, item):
        """Add *item* and restore heap order."""
        self._items.append(item)
        self._heapify_up(len(self._items) - 1)

    def pop(self):
        """Remove and return the smallest item, or ``None`` when empty."""
        if not self._items:
            return None
        if len(self._items) == 1:
            return self._items.pop()

        smallest = self._items[0]
        self._items[0] = self._items.pop()
        self._heapify_down(0)
        return smallest

    def peek(self):
        """Return the smallest item without removing it."""
        return None if not self._items else self._items[0]

    def size(self):
        """Return the number of heap items."""
        return len(self._items)

    def _heapify_up(self, index):
        while index > 0:
            parent = (index - 1) // 2
            if self._items[parent] <= self._items[index]:
                break
            self._items[parent], self._items[index] = (
                self._items[index],
                self._items[parent],
            )
            index = parent

    def _heapify_down(self, index):
        length = len(self._items)
        while True:
            left = index * 2 + 1
            right = left + 1
            smallest = index

            if left < length and self._items[left] < self._items[smallest]:
                smallest = left
            if right < length and self._items[right] < self._items[smallest]:
                smallest = right
            if smallest == index:
                break

            self._items[index], self._items[smallest] = (
                self._items[smallest],
                self._items[index],
            )
            index = smallest

