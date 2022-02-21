
from typing import Any, Callable, List, Set, Generic, TypeVar
from backend.utils.property_changed_observer import PropertyChangedObserver

T = TypeVar("T")


class Property(Generic[T]):
    """Simplified JavaFx property implementation"""

    def __init__(self, value: T) -> None:
        self.value = value
        self.property_changed_obss: List[PropertyChangedObserver] = []
        self.callbacks: List[Callable[[T, T], None]] = []
        self.one_way_bindings: Set["Property[T]"] = set()
        self.bidirectional_bindings: Set["Property[T]"] = set()
        self.bound_with: Set["Property[T]"] = set()

    def add_property_changed_observer(self, obs: PropertyChangedObserver = None, callback: Callable[[T, T], None] = None):
        if obs is None and callback is None or obs is not None and callback is not None:
            raise AttributeError("observer xor callback is required")

        if obs is not None:
            self.property_changed_obss.append(obs)
        else:
            self.callbacks.append(callback)

    def remove_property_changed_observer(self, obs: PropertyChangedObserver = None, callback: Callable[[T, T], None] = None):
        if obs is None and callback is None or obs is not None and callback is not None:
            raise AttributeError("observer xor callback is required")

        if obs is not None:
            self.property_changed_obss.remove(obs)
        else:
            self.callbacks.remove(callback)

    def set(self, new_val: T):
        self._set(new_val)

        for prop in self.one_way_bindings:
            prop.set(self.value)

        for prop in self.bidirectional_bindings:
            prop._set(self.value)

    def _set(self, new_val: T):
        old_val = self.value
        self.value = new_val

        if old_val != new_val:
            for obs in self.property_changed_obss:
                obs.on_changed(old_val, self.value)

            for callback in self.callbacks:
                callback(old_val, self.value)

    def get(self) -> T:
        return self.value

    def bind(self, other: "Property[T]") -> "Property[T]":
        """after this call finishes changes of other will trigger this to be updated"""
        if other in self.one_way_bindings:
            raise AttributeError(
                "implicit bidirectional binding, use bidirectional")

        if other in self.bidirectional_bindings:
            raise AttributeError("already bound bidirectional")

        other.one_way_bindings.add(self)
        self.set(other.value)

        return self

    def bind_bidirectional(self, other: "Property[T]") -> "Property[T]":
        """after this call finishes values of both properties will be synchronized, starting with value of other"""
        self._try_remove(other.one_way_bindings, self)
        self._try_remove(self.one_way_bindings, other)

        self.bidirectional_bindings.add(other)
        other.bidirectional_bindings.add(self)
        self.bound_with.add(other)
        other.bound_with.add(self)
        self._set(other.value)

        return self

    def as_string(self) -> "Property[str]":
        prop = Property(str(self.value))
        self.add_property_changed_observer(
            callback=lambda old, new: prop.set(str(new)))
        return prop

    def mapped_as(self, mapper: Callable[[T], Any]) -> "Property[Any]":
        prop = Property(mapper(self.value))
        self.add_property_changed_observer(
            callback=lambda old, new: prop.set(mapper(new)))
        return prop

    def unbind(self, other: "Property[T]"):
        self._try_remove(other.one_way_bindings, self)
        self._try_remove(self.bound_with, other)

    def unbind_bidirectional(self, other: "Property[T]"):
        self._try_remove(self.bidirectional_bindings, other)
        self._try_remove(other.bidirectional_bindings, self)
        self._try_remove(self.bound_with, other)
        self._try_remove(other.bound_with, self)

    @staticmethod
    def _try_remove(src: Set["Property[T]"], item: "Property[T]"):
        try:
            src.remove(item)
        except KeyError:
            pass

    def unbind_all(self):
        """Reverses all calls to self.bind(other) or self.bind_bidirectional(other)"""
        for binding in self.bound_with:
            self._try_remove(binding.one_way_bindings, self)
            self._try_remove(binding.bidirectional_bindings, self)

        self.bound_with.clear()
        self.one_way_bindings.clear()
        self.bidirectional_bindings.clear()

    def __str__(self) -> str:
        return f'Property<{self.value}>'


# TODO unit test this
# a = Property[int](3)
# b = Property[int](5)

# a.add_property_changed_observer(
#     callback=lambda old, new: print(f'old={old} | new={new}'))

# a.bind(b)
# a.set(10)
# b.set(1)


# class Smth:
#     def __init__(self, v) -> None:
#         self.v = v

#     def __str__(self):
#         return "test " + str(self.v)


# a = Property[str]('empty')
# b = Property[Smth](Smth(5))

# a.bind(b.as_string())

# print(a.get())

# b.set(Smth(8))

# print(a.get())


# a = Property[int](0)
# b = Property[Smth](Smth(5))

# a.bind(b.mapped_as(lambda x: x.v * 2))

# print(a.get())

# b.set(Smth(8))

# print(a.get())


# a = Property[int](1)
# b = Property[int](1)
# c = Property[int](1)

# a.bind(b)
# a.bind(c)

# a.add_property_changed_observer(
#     callback=lambda old, new: print(f'old={old} | new={new}'))

# b.add_property_changed_observer(
#     callback=lambda old, new: print(f'B old={old} | new={new}'))

# b.set(5)
# c.set(3)
# a.set(2)

# a.unbind_all()

# b.set(3)
# c.set(2)

# a.bind(b)

# b.set(112)

# print(a.get())
