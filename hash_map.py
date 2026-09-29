"""A string-keyed hash map implemented with separate chaining."""


class _HashEntry:
    """One entry in a bucket's linked collision chain."""

    def __init__(self, key, value, next_entry=None):
        self.key = key
        self.value = value
        self.next = next_entry


class HashMap:
    """Hash map using FNV-1a hashing and linked-list chaining."""

    _MAX_LOAD_FACTOR = 0.75

    def __init__(self, initial_capacity=8):
        if initial_capacity < 1:
            initial_capacity = 1
        self._buckets = [None] * initial_capacity
        self._size = 0

    def put(self, key, value):
        """Insert or replace a value and return the previous value."""
        index = self._bucket_index(key)
        entry = self._buckets[index]
        while entry is not None:
            if entry.key == key:
                previous = entry.value
                entry.value = value
                return previous
            entry = entry.next

        self._buckets[index] = _HashEntry(key, value, self._buckets[index])
        self._size += 1
        if self._size / len(self._buckets) > self._MAX_LOAD_FACTOR:
            self._resize(len(self._buckets) * 2)
        return None

    def get(self, key, default=None):
        """Return the value for *key*, or *default* when absent."""
        entry = self._find_entry(key)
        return default if entry is None else entry.value

    def remove(self, key):
        """Remove *key* and return its value, or ``None`` when absent."""
        index = self._bucket_index(key)
        previous = None
        entry = self._buckets[index]

        while entry is not None:
            if entry.key == key:
                if previous is None:
                    self._buckets[index] = entry.next
                else:
                    previous.next = entry.next
                self._size -= 1
                return entry.value
            previous = entry
            entry = entry.next
        return None

    def contains(self, key):
        """Return whether *key* is present."""
        return self._find_entry(key) is not None

    def keys(self):
        """Return all keys in unspecified order."""
        result = []
        for bucket in self._buckets:
            entry = bucket
            while entry is not None:
                result.append(entry.key)
                entry = entry.next
        return result

    def size(self):
        """Return the number of entries."""
        return self._size

    def _hash(self, key):
        """Compute a stable 64-bit FNV-1a hash from a string key."""
        hash_value = 14695981039346656037
        for byte in key.encode("utf-8"):
            hash_value ^= byte
            hash_value = (hash_value * 1099511628211) & 0xFFFFFFFFFFFFFFFF
        return hash_value

    def _bucket_index(self, key):
        return self._hash(key) % len(self._buckets)

    def _find_entry(self, key):
        entry = self._buckets[self._bucket_index(key)]
        while entry is not None:
            if entry.key == key:
                return entry
            entry = entry.next
        return None

    def _resize(self, new_capacity):
        old_buckets = self._buckets
        self._buckets = [None] * new_capacity

        for bucket in old_buckets:
            entry = bucket
            while entry is not None:
                next_entry = entry.next
                index = self._bucket_index(entry.key)
                entry.next = self._buckets[index]
                self._buckets[index] = entry
                entry = next_entry

