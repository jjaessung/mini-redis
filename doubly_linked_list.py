"""O(1) insertion, removal, and movement doubly linked list."""


class Node:
    """A node owned by :class:`DoublyLinkedList`."""

    def __init__(self, data=None):
        self.prev = None
        self.next = None
        self.data = data


class DoublyLinkedList:
    """Doubly linked list with sentinel nodes at both ends."""

    def __init__(self):
        self._head = Node()
        self._tail = Node()
        self._head.next = self._tail
        self._tail.prev = self._head
        self._size = 0

    def insert_front(self, data):
        """Insert *data* at the front and return its node in O(1)."""
        node = Node(data)
        self._insert_between(node, self._head, self._head.next)
        return node

    def insert_back(self, data):
        """Insert *data* at the back and return its node in O(1)."""
        node = Node(data)
        self._insert_between(node, self._tail.prev, self._tail)
        return node

    def remove_front(self):
        """Remove and return the first node, or ``None`` when empty."""
        if self._size == 0:
            return None
        return self.remove_node(self._head.next)

    def remove_back(self):
        """Remove and return the last node, or ``None`` when empty."""
        if self._size == 0:
            return None
        return self.remove_node(self._tail.prev)

    def remove_node(self, node):
        """Detach *node* and return it in O(1)."""
        if (
            node is None
            or node is self._head
            or node is self._tail
            or node.prev is None
            or node.next is None
        ):
            return None

        node.prev.next = node.next
        node.next.prev = node.prev
        node.prev = None
        node.next = None
        self._size -= 1
        return node

    def move_to_front(self, node):
        """Move an existing node to the front in O(1)."""
        if (
            node is None
            or node is self._head
            or node is self._tail
            or node.prev is None
            or node.next is None
            or node.prev is self._head
        ):
            return node

        node.prev.next = node.next
        node.next.prev = node.prev
        self._insert_between(node, self._head, self._head.next, is_new=False)
        return node

    def size(self):
        """Return the number of data nodes."""
        return self._size

    def _insert_between(self, node, previous, following, is_new=True):
        node.prev = previous
        node.next = following
        previous.next = node
        following.prev = node
        if is_new:
            self._size += 1

