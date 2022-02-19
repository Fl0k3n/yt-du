
from typing import Any, Callable, List, Set
from backend.utils.property_changed_observer import PropertyChangedObserver


class Property:
    def __init__(self, value: Any) -> None:
        self.value = value
        self.property_changed_obss: List[PropertyChangedObserver] = []
        self.callbacks: List[Callable[[Any, Any], None]] = []
        self.one_way_bindings: Set["Property"] = set()
        self.bidirectional_bindings: Set["Property"] = set()

    def add_property_changed_observer(self, obs: PropertyChangedObserver = None, callback: Callable[[Any, Any], None] = None):
        if obs is None and callback is None or obs is not None and callback is not None:
            raise AttributeError("observer xor callback is required")

        if obs is not None:
            self.property_changed_obss.append(obs)
        else:
            self.callbacks.append(callback)

    def remove_property_changed_observer(self, obs: PropertyChangedObserver = None, callback: Callable[[Any, Any], None] = None):
        if obs is None and callback is None or obs is not None and callback is not None:
            raise AttributeError("observer xor callback is required")

        if obs is not None:
            self.property_changed_obss.remove(obs)
        else:
            self.callbacks.remove(callback)

    def set(self, new_val: Any):
        self._set(new_val)

        for prop in self.one_way_bindings:
            prop.set(self.value)

        for prop in self.bidirectional_bindings:
            prop._set(self.value)

    def _set(self, new_val: Any):
        old_val = self.value
        self.value = new_val

        if old_val != new_val:
            for obs in self.property_changed_obss:
                obs.on_changed(old_val, self.value)

            for callback in self.callbacks:
                callback(old_val, self.value)

    def get(self) -> Any:
        return self.value

    def bind(self, other: "Property"):
        """after this call finishes changes of other will trigger this to be updated"""
        if other in self.one_way_bindings:
            raise AttributeError(
                "implicit bidirectional binding, use bidirectional")

        if other in self.bidirectional_bindings:
            raise AttributeError("already bound bidirectional")

        other.one_way_bindings.add(self)
        self._set(other.value)

    def bind_bidirectional(self, other: "Property"):
        """after this call finishes values of both properties will be synchronized, starting with value of other"""
        try:
            other.one_way_bindings.remove(self)
        except KeyError:
            pass

        try:
            self.one_way_bindings.remove(self)
        except KeyError:
            pass

        self.bidirectional_bindings.add(other)
        other.bidirectional_bindings.add(self)
        self._set(other.value)

    def unbind(self, other: "Property"):
        try:
            other.one_way_bindings.remove(self)
        except KeyError:
            pass

    def unbind_bidirectional(self, other: "Property"):
        try:
            self.bidirectional_bindings.remove(other)
            other.bidirectional_bindings.remove(self)
        except KeyError:
            pass

    def __str__(self) -> str:
        return f'Property<{self.value}>'


# a = Property(3)
# b = Property(5)

# a.add_property_changed_observer(
#     callback=lambda old, new: print(f'old={old} | new={new}'))

# a.bind(b)
# a.set(10)
# b.set(1)
