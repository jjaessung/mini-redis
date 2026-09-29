import unittest

from doubly_linked_list import DoublyLinkedList
from hash_map import HashMap
from min_heap import MinHeap


class DoublyLinkedListTests(unittest.TestCase):
    def test_insert_move_and_remove(self):
        linked = DoublyLinkedList()
        first = linked.insert_back("first")
        second = linked.insert_back("second")
        linked.move_to_front(second)

        self.assertEqual(linked.remove_front().data, "second")
        self.assertEqual(linked.remove_back().data, "first")
        self.assertEqual(linked.size(), 0)
        self.assertIsNone(linked.remove_front())

    def test_detached_node_cannot_be_removed_twice(self):
        linked = DoublyLinkedList()
        node = linked.insert_front("value")

        self.assertIs(linked.remove_node(node), node)
        self.assertIsNone(linked.remove_node(node))
        self.assertEqual(linked.size(), 0)


class _CollidingHashMap(HashMap):
    def _hash(self, key):
        return 1


class HashMapTests(unittest.TestCase):
    def test_chaining_handles_collisions(self):
        mapping = _CollidingHashMap(initial_capacity=2)
        mapping.put("alpha", 1)
        mapping.put("beta", 2)
        mapping.put("gamma", 3)

        self.assertEqual(mapping.get("alpha"), 1)
        self.assertEqual(mapping.get("beta"), 2)
        self.assertEqual(mapping.remove("beta"), 2)
        self.assertFalse(mapping.contains("beta"))
        self.assertEqual(mapping.size(), 2)

    def test_resize_keeps_every_entry(self):
        mapping = HashMap(initial_capacity=2)
        for number in range(20):
            mapping.put(f"key-{number}", number)

        self.assertGreaterEqual(len(mapping._buckets), 32)
        self.assertEqual(mapping.size(), 20)
        for number in range(20):
            self.assertEqual(mapping.get(f"key-{number}"), number)

    def test_put_replaces_without_growing(self):
        mapping = HashMap()
        self.assertIsNone(mapping.put("key", "old"))
        self.assertEqual(mapping.put("key", "new"), "old")
        self.assertEqual(mapping.get("key"), "new")
        self.assertEqual(mapping.size(), 1)


class MinHeapTests(unittest.TestCase):
    def test_values_are_popped_in_ascending_order(self):
        heap = MinHeap()
        for value in (7, 2, 9, 1, 5, 3):
            heap.push(value)

        popped = []
        while heap.size() > 0:
            popped.append(heap.pop())

        self.assertEqual(popped, [1, 2, 3, 5, 7, 9])
        self.assertIsNone(heap.peek())
        self.assertIsNone(heap.pop())


if __name__ == "__main__":
    unittest.main()

