# File automatically generated by mapry. DO NOT EDIT OR APPEND!


"""provides general structures and functions for parsing."""


import typing

import some.graph


class Error:
    """represents an error occurred while parsing."""

    def __init__(self, ref: str, message: str) -> None:
        """
        initializes the error with the given values.

        :param ref: references the cause (e.g., a reference path)
        :param message: describes the error
        """
        self.ref = ref
        self.message = message


class Errors:
    """
    collects errors capped at a certain quantity.

    If the capacity is full, the subsequent surplus errors are ignored.
    """

    def __init__(self, cap: int) -> None:
        """
        initializes the error container with the given cap.

        :param cap: maximum number of contained errors
        """
        self.cap = cap
        self._values = []  # type: typing.List[Error]

    def add(self, ref: str, message: str) -> None:
        """
        adds an error to the container.

        :param ref: references the cause (e.g., a reference path)
        :param message: describes the error
        """
        if len(self._values) < self.cap:
            self._values.append(Error(ref=ref, message=message))

    def full(self) -> bool:
        """gives True when there are exactly ``cap`` errors contained."""
        return len(self._values) == self.cap

    def empty(self) -> bool:
        """gives True when there are no errors contained."""
        return len(self._values) == 0

    def count(self) -> int:
        """returns the number of errors."""
        return len(self._values)

    def values(self) -> typing.Iterable[Error]:
        """gives an iterator over the errors."""
        return iter(self._values)


def placeholder_some_graph() -> some.graph.SomeGraph:
    """
    creates a placeholder instance of SomeGraph.

    Placeholders are necessary so that we can pre-allocate class registries
    during parsing. All the attribute of the placeholder are set to None.
    Consider a placeholder an empty shell to be filled out during parsing.

    :return: empty shell
    """
    return some.graph.SomeGraph(  # type: ignore
        some_map=None,
        some_nested_map=None)
