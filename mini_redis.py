"""Core in-memory key-value store for the Mini Redis project."""

import math
import shlex
import time

from doubly_linked_list import DoublyLinkedList
from hash_map import HashMap
from min_heap import MinHeap


OOM_ERROR = "(error) OOM command not allowed when used_memory > 'maxmemory'"
INTEGER_ERROR = "(error) ERR value is not an integer or out of range"


class _CacheEntry:
    """Stored value plus its node in the LRU linked list."""

    def __init__(self, key, value, lru_node):
        self.key = key
        self.value = value
        self.lru_node = lru_node


class _Expiration:
    """The currently valid expiration record for a key."""

    def __init__(self, expire_at, version):
        self.expire_at = expire_at
        self.version = version


class MiniRedis:
    """A small Redis-like store built from custom data structures."""

    def __init__(self, clock=None):
        self._data = HashMap()
        self._lru = DoublyLinkedList()
        self._expirations = HashMap()
        self._expiration_heap = MinHeap()
        self._clock = clock if clock is not None else time.time
        self._expiration_version = 0

        self.used_memory = 0
        self.maxmemory = 0
        self.evicted_keys = 0

    def set(self, key, value):
        """Store a string value, update LRU, and enforce maxmemory."""
        self._purge_expired()
        entry_size = self._entry_size(key, value)
        if self.maxmemory > 0 and entry_size > self.maxmemory:
            return OOM_ERROR

        entry = self._data.get(key)
        if entry is None:
            node = self._lru.insert_front(key)
            entry = _CacheEntry(key, value, node)
            self._data.put(key, entry)
            self.used_memory += entry_size
        else:
            self.used_memory -= self._entry_size(key, entry.value)
            entry.value = value
            self.used_memory += entry_size
            self._lru.move_to_front(entry.lru_node)

        # Redis SET without an expiry option clears an existing TTL.
        self._expirations.remove(key)
        self._evict_until_within_limit()
        return "OK"

    def get(self, key):
        """Return a value and mark it most recently used, or ``None``."""
        self._purge_expired()
        entry = self._data.get(key)
        if entry is None:
            return None
        self._lru.move_to_front(entry.lru_node)
        return entry.value

    def delete(self, key):
        """Delete a key from data, LRU, and TTL state."""
        self._purge_expired()
        return 1 if self._delete_key(key) else 0

    def exists(self, key):
        """Return 1 when a non-expired key exists, otherwise 0."""
        self._purge_expired()
        return 1 if self._data.contains(key) else 0

    def dbsize(self):
        """Return the number of currently live keys."""
        self._purge_expired()
        return self._data.size()

    def keys(self):
        """Return all currently live keys in unspecified order."""
        self._purge_expired()
        return self._data.keys()

    def configure_maxmemory(self, byte_count):
        """Set the byte limit. Zero means unlimited memory."""
        self.maxmemory = byte_count
        return "OK"

    def memory_info(self):
        """Return the required memory statistics as a display string."""
        self._purge_expired()
        return (
            f"used_memory:{self.used_memory}\n"
            f"maxmemory:{self.maxmemory}\n"
            f"evicted_keys:{self.evicted_keys}"
        )

    def expire(self, key, seconds):
        """Return 1 or 0, or INTEGER_ERROR if the deadline is out of range."""
        self._purge_expired()
        if not self._data.contains(key):
            return 0
        if seconds <= 0:
            self._delete_key(key)
            return 1

        # Validate before replacing the existing TTL or adding a heap record.
        try:
            expire_at = self._clock() + seconds
            if not math.isfinite(expire_at):
                return INTEGER_ERROR
        except OverflowError:
            return INTEGER_ERROR

        self._expiration_version += 1
        expiration = _Expiration(expire_at, self._expiration_version)
        self._expirations.put(key, expiration)
        self._expiration_heap.push((expire_at, expiration.version, key))
        return 1

    def ttl(self, key):
        """Return -2 for missing, -1 for persistent, or seconds remaining."""
        now = self._clock()
        self._purge_expired(now)
        if not self._data.contains(key):
            return -2

        expiration = self._expirations.get(key)
        if expiration is None:
            return -1
        return max(0, int(expiration.expire_at - now))

    def execute(self, line):
        """Parse and execute one CLI command, returning display text."""
        try:
            parts = shlex.split(line)
        except ValueError:
            return "(error) ERR syntax error"

        if not parts:
            return None

        command = parts[0].upper()

        if command == "SET":
            if len(parts) != 3:
                return self._wrong_arguments(command)
            return self.set(parts[1], parts[2])

        if command == "GET":
            if len(parts) != 2:
                return self._wrong_arguments(command)
            value = self.get(parts[1])
            return "(nil)" if value is None else self._quote(value)

        if command == "DEL":
            if len(parts) != 2:
                return self._wrong_arguments(command)
            return self._integer(self.delete(parts[1]))

        if command == "EXISTS":
            if len(parts) != 2:
                return self._wrong_arguments(command)
            return self._integer(self.exists(parts[1]))

        if command == "DBSIZE":
            if len(parts) != 1:
                return self._wrong_arguments(command)
            return self._integer(self.dbsize())

        if command == "KEYS":
            if len(parts) != 1:
                return self._wrong_arguments(command)
            return self._format_keys(self.keys())

        if command == "EXPIRE":
            if len(parts) != 3:
                return self._wrong_arguments(command)
            seconds = self._parse_integer(parts[2])
            if seconds is None:
                return INTEGER_ERROR
            result = self.expire(parts[1], seconds)
            return result if result == INTEGER_ERROR else self._integer(result)

        if command == "TTL":
            if len(parts) != 2:
                return self._wrong_arguments(command)
            return self._integer(self.ttl(parts[1]))

        if command == "CONFIG":
            if len(parts) != 4:
                return self._wrong_arguments(command)
            if parts[1].upper() != "SET" or parts[2].lower() != "maxmemory":
                return "(error) ERR syntax error"
            byte_count = self._parse_integer(parts[3])
            if byte_count is None or byte_count < 0:
                return INTEGER_ERROR
            return self.configure_maxmemory(byte_count)

        if command == "INFO":
            if len(parts) != 2:
                return self._wrong_arguments(command)
            if parts[1].lower() != "memory":
                return "(error) ERR syntax error"
            return self.memory_info()

        return f"(error) ERR unknown command '{parts[0]}'"

    def _purge_expired(self, now=None):
        """Remove all heap entries whose current TTL has elapsed."""
        if now is None:
            now = self._clock()

        next_expiration = self._expiration_heap.peek()
        while next_expiration is not None and next_expiration[0] <= now:
            expire_at, version, key = self._expiration_heap.pop()
            current = self._expirations.get(key)
            if (
                current is not None
                and current.version == version
                and current.expire_at == expire_at
            ):
                self._delete_key(key)
            next_expiration = self._expiration_heap.peek()

    def _delete_key(self, key):
        """Remove one key from every authoritative structure."""
        entry = self._data.remove(key)
        if entry is None:
            self._expirations.remove(key)
            return False

        self.used_memory -= self._entry_size(key, entry.value)
        self._lru.remove_node(entry.lru_node)
        self._expirations.remove(key)
        return True

    def _evict_until_within_limit(self):
        while self.maxmemory > 0 and self.used_memory > self.maxmemory:
            lru_node = self._lru.remove_back()
            if lru_node is None:
                break
            entry = self._data.remove(lru_node.data)
            if entry is None:
                continue
            self.used_memory -= self._entry_size(entry.key, entry.value)
            self._expirations.remove(entry.key)
            self.evicted_keys += 1

    @staticmethod
    def _entry_size(key, value):
        return len(key.encode("utf-8")) + len(value.encode("utf-8"))

    @staticmethod
    def _integer(value):
        return f"(integer) {value}"

    @staticmethod
    def _wrong_arguments(command):
        return (
            "(error) ERR wrong number of arguments for "
            f"'{command}' command"
        )

    @staticmethod
    def _parse_integer(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _quote(value):
        escaped = (
            value.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("\t", "\\t")
        )
        return f'"{escaped}"'

    def _format_keys(self, keys):
        if not keys:
            return "(empty array)"
        lines = []
        for index, key in enumerate(keys, start=1):
            lines.append(f"{index}. {self._quote(key)}")
        return "\n".join(lines)
