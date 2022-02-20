from collections import deque
from typing import Any, Callable, Iterable
from backend.utils.property import Property


class ObservableList:
    def __init__(self, data: Iterable = None) -> None:
        self.items = deque(data) if data is not None else deque()
        self.size_property = Property(0)
        self.on_added_callbacks = []
        self.on_removed_callbacks = []

    def get_size_property(self) -> Property:
        return self.size_property

    def append(self, item: Any):
        self.items.append(item)
        self._append(item)

    def append_front(self, item: Any):
        self.items.appendleft(item)
        self._append(item)

    def remove(self, item: Any):
        self.items.remove(item)
        self.size_property.set(len(self.items))

        for callback in self.on_removed_callbacks:
            callback(item)

    def find(self, predicate: Callable[[Any], bool]) -> Any:
        for item in self.items:
            try:
                if predicate(item):
                    return item
            except:
                pass

        return None

    def _append(self, item: Any):
        self.size_property.set(len(self.items))

        for callback in self.on_added_callbacks:
            callback(item)

    def add_on_changed_observer(self, on_added_cb: Callable[[Any], None] = None,
                                on_removed_cb: Callable[[Any], None] = None):
        if on_added_cb is not None:
            self.on_added_callbacks.append(on_added_cb)

        if on_removed_cb is not None:
            self.on_removed_callbacks.append(on_removed_cb)

    def __iter__(self):
        return self.items.__iter__()

    def __len__(self):
        return len(self.items)

    def __str__(self) -> str:
        return str(list(self.items))


# x = ObservableList()
# x.append(1)
# x.append(2)
# x.append(3)

# for el in x:
#     print(el)


# def print_on_add(y):
#     print(y)


# x.add_on_changed_observer(on_added_cb=print_on_add)

# x.add_on_changed_observer(on_removed_cb=lambda y: print('rm ', y))

# x.append(5)

# print(x)

# x.remove(2)

# x.append_front(10)

# print(x)


# print(x.find(lambda y: y > 2 and y < 5))
