import unittest

from mini_redis import INTEGER_ERROR, OOM_ERROR, MiniRedis


class FakeClock:
    def __init__(self, current=1000.0):
        self.current = current

    def __call__(self):
        return self.current

    def advance(self, seconds):
        self.current += seconds


class MiniRedisTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.redis = MiniRedis(clock=self.clock)

    def test_string_commands(self):
        self.assertEqual(self.redis.execute('SET user:1 "Alice Smith"'), "OK")
        self.assertEqual(self.redis.execute("GET user:1"), '"Alice Smith"')
        self.assertEqual(self.redis.execute("EXISTS user:1"), "(integer) 1")
        self.assertEqual(self.redis.execute("DBSIZE"), "(integer) 1")
        self.assertIn('"user:1"', self.redis.execute("KEYS"))
        self.assertEqual(self.redis.execute("DEL user:1"), "(integer) 1")
        self.assertEqual(self.redis.execute("GET user:1"), "(nil)")
        self.assertEqual(self.redis.execute("DEL user:1"), "(integer) 0")
        self.assertEqual(self.redis.execute("KEYS"), "(empty array)")

    def test_utf8_memory_accounting_and_overwrite(self):
        self.redis.set("한", "글")
        self.assertEqual(self.redis.used_memory, 6)

        self.redis.set("한", "abc")
        self.assertEqual(self.redis.used_memory, 6)
        self.assertEqual(self.redis.dbsize(), 1)

    def test_get_changes_lru_eviction_order(self):
        self.redis.configure_maxmemory(6)
        self.redis.set("a", "aa")
        self.redis.set("b", "bb")
        self.assertEqual(self.redis.get("a"), "aa")

        self.redis.set("c", "cc")

        self.assertEqual(self.redis.get("a"), "aa")
        self.assertIsNone(self.redis.get("b"))
        self.assertEqual(self.redis.get("c"), "cc")
        self.assertEqual(self.redis.evicted_keys, 1)
        self.assertEqual(self.redis.used_memory, 6)

    def test_oversized_entry_is_rejected_atomically(self):
        self.redis.configure_maxmemory(5)
        self.redis.set("a", "1")
        self.redis.expire("a", 10)

        self.assertEqual(self.redis.set("a", "12345"), OOM_ERROR)
        self.assertEqual(self.redis.get("a"), "1")
        self.assertEqual(self.redis.ttl("a"), 10)
        self.assertEqual(self.redis.used_memory, 2)

    def test_expiration_removes_key_from_all_live_views(self):
        self.redis.set("temporary", "value")
        self.assertEqual(self.redis.expire("temporary", 3), 1)
        self.clock.advance(3)

        self.assertIsNone(self.redis.get("temporary"))
        self.assertEqual(self.redis.ttl("temporary"), -2)
        self.assertEqual(self.redis.exists("temporary"), 0)
        self.assertEqual(self.redis.dbsize(), 0)
        self.assertEqual(self.redis.keys(), [])
        self.assertEqual(self.redis.used_memory, 0)
        self.assertEqual(self.redis.evicted_keys, 0)

    def test_overwrite_clears_ttl(self):
        self.redis.set("key", "old")
        self.redis.expire("key", 2)
        self.redis.set("key", "new")
        self.clock.advance(3)

        self.assertEqual(self.redis.ttl("key"), -1)
        self.assertEqual(self.redis.get("key"), "new")

    def test_expire_uses_lazy_deletion_for_stale_heap_records(self):
        self.redis.set("key", "value")
        self.redis.expire("key", 5)
        self.clock.advance(2)
        self.redis.expire("key", 10)
        self.clock.advance(4)

        self.assertEqual(self.redis.get("key"), "value")
        self.assertEqual(self.redis.ttl("key"), 6)
        self.clock.advance(6)
        self.assertIsNone(self.redis.get("key"))

    def test_deleted_key_can_be_reused_despite_stale_expiry(self):
        self.redis.set("key", "old")
        self.redis.expire("key", 1)
        self.redis.delete("key")
        self.redis.set("key", "new")
        self.clock.advance(2)

        self.assertEqual(self.redis.get("key"), "new")

    def test_non_positive_expire_deletes_immediately(self):
        self.redis.set("key", "value")
        self.assertEqual(self.redis.expire("key", 0), 1)
        self.assertEqual(self.redis.exists("key"), 0)
        self.assertEqual(self.redis.expire("missing", -1), 0)

    def test_cli_errors_and_memory_info(self):
        self.assertEqual(self.redis.execute("GET"), (
            "(error) ERR wrong number of arguments for 'GET' command"
        ))
        self.assertEqual(
            self.redis.execute("CONFIG SET maxmemory nope"), INTEGER_ERROR
        )
        self.assertEqual(
            self.redis.execute("CONFIG SET maxmemory -1"), INTEGER_ERROR
        )
        self.assertEqual(
            self.redis.execute("HELLO"),
            "(error) ERR unknown command 'HELLO'",
        )

        self.assertEqual(self.redis.execute("CONFIG SET maxmemory 30"), "OK")
        info = self.redis.execute("INFO memory")
        self.assertIn("used_memory:0", info)
        self.assertIn("maxmemory:30", info)
        self.assertIn("evicted_keys:0", info)


if __name__ == "__main__":
    unittest.main()

