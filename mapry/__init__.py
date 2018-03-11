#!/usr/bin/env python3
"""Serialize and deserialize object graphs from/to JSONables."""
import collections
import typing
# yapf: disable
from typing import (
    Iterable, List, Mapping, MutableMapping, Optional, Pattern, Set,
    Tuple, Union)

# yapf: enable


class Type:
    """Represent a type of mapry values."""


class Boolean(Type):
    """Represent booleans."""


class Integer(Type):
    """Represent a type of integer numbers."""

    def __init__(
            self,
            minimum: Optional[int] = None,
            exclusive_minimum: bool = False,
            maximum: Optional[int] = None,
            exclusive_maximum: bool = False) -> None:
        """
        Define a type of integer numbers.

        :param minimum: minimum constraint, if any
        :param exclusive_minimum: if True, minimum constraint is exclusive.
        :param maximum: maximum constraint, if any
        :param exclusive_maximum: if True, maximum constraint is exclusive.
        """
        self.minimum = minimum
        self.exclusive_minimum = exclusive_minimum
        self.maximum = maximum
        self.exclusive_maximum = exclusive_maximum
        super().__init__()


class Float(Type):
    """Represent a type of floating-point numbers."""

    def __init__(
            self,
            minimum: Optional[float] = None,
            exclusive_minimum: bool = False,
            maximum: Optional[float] = None,
            exclusive_maximum: bool = False) -> None:
        """
        Define a type of floating-point numbers.

        :param minimum: minimum constraint, if any
        :param exclusive_minimum: if True, minimum constraint is exclusive.
        :param maximum: maximum constraint, if any
        :param exclusive_maximum: if True, maximum constraint is exclusive.
        """
        self.minimum = minimum
        self.exclusive_minimum = exclusive_minimum
        self.maximum = maximum
        self.exclusive_maximum = exclusive_maximum
        super().__init__()


class String(Type):
    """Represent a type of strings."""

    def __init__(self, pattern: Optional[Pattern[str]] = None) -> None:
        """
        Define a string type.

        :param pattern: pattern constraint of the string
        """
        self.pattern = pattern
        super().__init__()


class Path(Type):
    """Represent a type of paths in the file system."""

    def __init__(self, pattern: Optional[Pattern[str]] = None) -> None:
        """
        Define a path type.

        :param pattern: pattern constraint of the paths
        """
        self.pattern = pattern
        super().__init__()


class Date(Type):
    """Represent a type of dates."""

    def __init__(self, fmt: Optional[str] = None) -> None:
        """
        Define a date type.

        :param fmt:
            format as strftime directives; if None,
            the default ISO 8601 format will be set.
        """
        self.format = fmt if fmt is not None else '%Y-%m-%d'
        super().__init__()


class Time(Type):
    """Represent a type of times of the day."""

    def __init__(self, fmt: Optional[str] = None) -> None:
        """
        Define the type of times of the day.

        :param fmt:
            format as strftime directives;
            if None, the default ISO 8601 format will be set.
        """
        self.format = fmt if fmt is not None else '%H:%M:%S'
        super().__init__()


class Datetime(Type):
    """Represent a type of time points."""

    def __init__(self, fmt: Optional[str] = None) -> None:
        """
        Define the type of the time points.

        :param fmt:
            format as strftime directives; if None,
            the default ISO 8601 format will be set.
        """
        self.format = fmt if fmt is not None else '%Y-%m-%dT%H:%M:%SZ'
        super().__init__()


class TimeZone(Type):
    """Represent a type of time zones (according to the IANA identifier)."""


class Duration(Type):
    """Represent a type of durations (ISO 8601 formatted)."""


class Array(Type):
    """Represent a type of arrays."""

    def __init__(
            self,
            values: Type,
            minimum_size: Optional[int] = None,
            maximum_size: Optional[int] = None) -> None:
        """
        Define an array type.

        :param values: type of the array values
        :param minimum_size: inclusive minimum number of elements
        :param maximum_size: inclusive maximum number of elements
        """
        self.values = values
        self.minimum_size = minimum_size
        self.maximum_size = maximum_size
        super().__init__()


class Map(Type):
    """Represent a type of mappings string -> mapry value."""

    def __init__(self, values: Type) -> None:
        """
        Define the map type.

        :param values: type of the map values (the keys are strings)
        """
        self.values = values
        super().__init__()


class Property:
    """Represent a property of a composite structure."""

    def __init__(
            self, ref: str, name: str, a_type: Type, description: str,
            json: str, optional: bool, composite: 'Composite') -> None:
        """
        Initialize the property.

        :param ref: reference path to the property in the schema
        :param name: of the property
        :param a_type: type definition
        :param description: human-readable text
        :param json: identifier of the property in the JSONable structure
        :param optional: True if the property is optional
        :param composite: back-reference to the composite
        """
        # pylint: disable=too-many-arguments
        self.ref = ref
        self.name = name
        self.type = a_type
        self.description = description
        self.json = json
        self.optional = optional
        self.composite = composite


class Embed(Type):
    """Represent an embeddable structure."""

    def __init__(self, name: str, description: str, ref: str) -> None:
        """
        Initialize the embeddable structure with the given values.

        Since properties need to reference the composite they belong to,
        which poses a chicken-and-egg problem,
        they are initialized as an empty ordered dictionary.

        :param name: of the embeddable structure
        :param description: of the embeddable structure
        :param ref: reference path to the embeddable structure in the schema
        """
        self.name = name
        self.description = description
        self.ref = ref

        self.properties = collections.OrderedDict(
        )  # type: MutableMapping[str, Property]

        super().__init__()


class Class(Type):
    """Represent a mapry class."""

    def __init__(
            self,
            name: str,
            plural: str,
            description: str,
            ref: str,
            id_pattern: Optional[Pattern[str]] = None) -> None:
        """
        Initialize the class with the given values.

        Since properties need to reference the composite they belong to,
        which poses a chicken-and-egg problem,
        they are initialized as an empty ordered dictionary.

        :param name: name of the class
        :param plural: plural form of the class
        :param description: description of the class
        :param ref: reference path to the class in the schema
        :param id_pattern:
            if specified, the pattern enforced on the instance identifiers
        """
        self.name = name
        self.plural = plural
        self.description = description
        self.ref = ref

        self.properties = collections.OrderedDict(
        )  # type: MutableMapping[str, Property]

        self.id_pattern = id_pattern

        super().__init__()


class Graph(Type):
    """Represent an object graph."""

    def __init__(self) -> None:
        """Initialize the object graph with default attribute values."""
        # Reference in the original JSONable structure
        self.ref = ''

        self.name = ''
        self.description = ''
        self.embeds = collections.OrderedDict(
        )  # type: MutableMapping[str, Embed]
        self.classes = collections.OrderedDict(
        )  # type: MutableMapping[str, Class]
        self.properties = collections.OrderedDict(
        )  # type: Mapping[str, Property]

        super().__init__()


# Defines a type with properties
Composite = typing.Union[Class, Embed, Graph]  # pylint: disable=invalid-name


class Cpp:
    """List settings for the generation of the C++ code."""

    def __init__(self) -> None:
        """Initialize the C++ settings with default attribute values."""
        self.namespace = ''
        self.path_as = ''
        self.optional_as = ''
        self.datetime_library = ''
        self.indention = ''


class Go:
    """List settings for the generation of the Go code."""

    def __init__(self) -> None:
        """Initialize the Go settings with default attribute values."""
        self.package = ''


class Py:
    """List settings for the generation of the Python code."""

    def __init__(self) -> None:
        """Initialize the Python settings with default attribute values."""
        self.module_name = ''
        self.path_as = ''
        self.timezone_as = ''
        self.indention = ''


class Schema:
    """Represent a schema of an object graph."""

    def __init__(
            self, graph: Graph, cpp: Optional[Cpp], go: Optional[Go],
            py: Optional[Py]) -> None:
        """
        Define a mapry schema.

        :param graph: definition of the object graph
        :param cpp: settings for the generation of C++ code
        :param go: settings for the generation of Go code
        :param py: settings for the generation of Python code
        """
        self.graph = graph
        self.cpp = cpp
        self.go = go  # pylint: disable=invalid-name
        self.py = py  # pylint: disable=invalid-name


def _needs_type(
        a_type: Type, query: typing.Type[Type],
        visited_types: Set[Type]) -> bool:
    """
    Search ``query`` recursively starting with ``a_type``.

    The search first checks if ``a_type`` is equal ``query``. Otherwise,
    the search continues through value types, if it is an aggregated type (such
    as array or map) or through types of its properties, if it is a composite
    type (such as graph, embeddable structure or class).

    :param a_type: type to inspect
    :param query: type to search for
    :param visited_types: marks visited types to prevent endless recursion
    :return:
        True if ``query`` found recursively in ``a_type``
    """
    # pylint: disable=too-many-return-statements
    # pylint: disable=too-many-branches
    if isinstance(a_type, query):
        return True

    # Give an immediate answer if no recursion is possible.
    if not isinstance(a_type, (Graph, Class, Embed, Array, Map)):
        return False

    if isinstance(a_type, Graph):
        for cls in a_type.classes.values():
            if cls not in visited_types:
                visited_types.add(a_type)
                if _needs_type(a_type=cls, query=query,
                               visited_types=visited_types):
                    return True

        for embed in a_type.embeds.values():
            if embed not in visited_types:
                visited_types.add(a_type)
                if _needs_type(a_type=embed, query=query,
                               visited_types=visited_types):
                    return True

    if isinstance(a_type, (Graph, Class, Embed)):
        for prop in a_type.properties.values():
            if prop.type not in visited_types:
                visited_types.add(a_type)
                if _needs_type(a_type=prop.type, query=query,
                               visited_types=visited_types):
                    return True

    if isinstance(a_type, Array):
        if a_type.values not in visited_types:
            visited_types.add(a_type)
            if _needs_type(a_type=a_type.values, query=query,
                           visited_types=visited_types):
                return True

    if isinstance(a_type, Map):
        if a_type.values not in visited_types:
            visited_types.add(a_type)
            if _needs_type(a_type=a_type.values, query=query,
                           visited_types=visited_types):
                return True

    return False


def needs_type(a_type: Type, query: typing.Type[Type]) -> bool:
    """
    Search ``query`` recursively starting with ``a_type``.

    The search first checks if ``a_type`` is equal ``query``. Otherwise,
    the search continues through value types, if it is an aggregated type (such
    as array or map) or through types of its properties, if it is a composite
    type (such as graph, embeddable structure or class).

    :param a_type: type to inspect
    :param query: type to search for
    :return: True if ``query`` found recursively in ``a_type``
    """
    return _needs_type(a_type=a_type, query=query, visited_types=set())


def _references(a_type: Type, visited_types: Set[Type]) -> Set[Class]:
    """
    Inspect recursively which classes are referenced by 'a_type'.

    :param a_type: class or embeddable structure to inspect
    :param visited_types: set of visited types to prevent endless recursion
    :return: set of referenced classes
    """
    # Prevent endless recursion
    if a_type in visited_types:
        return set()
    visited_types.add(a_type)

    result = set()  # type: Set[Class]
    if isinstance(a_type, Class):
        result.add(a_type)

    # Follow recursion
    if isinstance(a_type, (Class, Embed)):
        for prop in a_type.properties.values():
            result.update(
                _references(a_type=prop.type, visited_types=visited_types))

    elif isinstance(a_type, (Array, Map)):
        result.update(
            _references(a_type=a_type.values, visited_types=visited_types))

    else:
        # Recursion stops here since the type is neither a composite nor an
        # aggregated type.
        pass

    return result


def references(a_type: Union[Class, Embed]) -> List[Class]:
    """
    Inspect recursively which classes are referenced by ``a_type``.

    :param a_type: class or embeddable structure to inspect
    :return: list of referenced classes
    """
    result = set()  # type: Set[Class]

    for prop in a_type.properties.values():
        result.update(_references(a_type=prop.type, visited_types=set()))

    lst = list(result)
    lst.sort(key=lambda cls: cls.name)

    return lst


def _iterate_over_types_recursively(a_type: Type,
                                    ref: str) -> Iterable[Tuple[Type, str]]:
    """
    Recursively iterate over the type and its nested types.

    :param a_type: mapry type definition
    :param ref: reference path to the type definition in the schema
    :return: iteration over the mapry type definitions and their reference paths
    """
    yield a_type, ref
    if isinstance(a_type, (Array, Map)):
        yield from _iterate_over_types_recursively(
            a_type=a_type.values, ref='{}/values'.format(ref))


def _iterate_over_composite_types(composite: Composite
                                  ) -> Iterable[Tuple[Type, str]]:
    """
    Iterate over the property types of the composite recursively.

    :param composite: mapry definition of a composite
    :return: iteration over the mapry type definitions and their reference paths
    """
    for prop in composite.properties.values():
        yield from _iterate_over_types_recursively(
            a_type=prop.type, ref='{}/{}'.format(composite.ref, prop.name))


def iterate_over_types(graph: Graph) -> Iterable[Tuple[Type, str]]:
    """
    Iterate over all the value types defined in a graph.

    This includes the value types of arrays and maps as well as
    types of properties of classes and embeddable structures.

    :param graph: mapry definition of the object graph
    :return: iteration over the mapry type definitions and their reference paths
    """
    for cls in graph.classes.values():
        yield from _iterate_over_composite_types(composite=cls)

    for embed in graph.embeds.values():
        yield from _iterate_over_composite_types(composite=embed)

    yield from _iterate_over_composite_types(composite=graph)
