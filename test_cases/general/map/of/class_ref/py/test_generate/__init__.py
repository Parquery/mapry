# File automatically generated by mapry. DO NOT EDIT OR APPEND!


"""defines some object graph."""


import collections
import typing


class Empty:
    """defines an empty class."""

    def __init__(
            self,
            id: str) -> None:
        """
        initializes an instance of Empty with the given values.

        :param id: identifier of the instance
        """
        self.id = id


class SomeGraph:
    """defines some object graph."""

    def __init__(
            self,
            map_of_class_refs: typing.MutableMapping[str, Empty],
            empties: typing.Optional[typing.MutableMapping[str, Empty]] = None) -> None:
        """
        initializes an instance of SomeGraph with the given values.

        The class registries are initialized with empty ordered dictionaries.
        :param map_of_class_refs: tests a map of class references.
        :param empties:
            registry of instances of Empty;
            if not specified, it is initialized as a ``collections.OrderedDict``.

        """
        self.map_of_class_refs = map_of_class_refs

        if empties is not None:
            self.empties = empties
        else:
            self.empties = collections.OrderedDict()


# File automatically generated by mapry. DO NOT EDIT OR APPEND!
