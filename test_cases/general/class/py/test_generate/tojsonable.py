# File automatically generated by mapry. DO NOT EDIT OR APPEND!


"""serializes to JSONable objects."""


import collections
import typing

import some.graph


def serialize_empty(
        instance: some.graph.Empty,
        ordered: bool = False
) -> typing.MutableMapping[str, typing.Any]:
    """
    serializes an instance of Empty to a JSONable representation.

    :param instance: the instance of Empty to be serialized
    :param ordered:
        If set, represents the instance as a ``collections.OrderedDict``.
        Otherwise, it is represented as a ``dict``.
    :return: a JSONable
    """
    if ordered:
        target = (
            collections.OrderedDict()
        )  # type: typing.MutableMapping[str, typing.Any]
    else:
        target = dict()

    return target


def serialize_with_reference(
        instance: some.graph.WithReference,
        ordered: bool = False
) -> typing.MutableMapping[str, typing.Any]:
    """
    serializes an instance of WithReference to a JSONable representation.

    :param instance: the instance of WithReference to be serialized
    :param ordered:
        If set, represents the instance as a ``collections.OrderedDict``.
        Otherwise, it is represented as a ``dict``.
    :return: a JSONable
    """
    if ordered:
        target = (
            collections.OrderedDict()
        )  # type: typing.MutableMapping[str, typing.Any]
    else:
        target = dict()

    ##
    # Serialize reference_to_an_empty
    ##

    target['reference_to_an_empty'] = instance.reference_to_an_empty.id

    ##
    # Serialize array_of_empties
    ##

    target_0 = [
        item_0.id
        for item_0 in instance.array_of_empties
    ]  # type: typing.List[str]
    target['array_of_empties'] = target_0

    ##
    # Serialize map_of_empties
    ##

    if isinstance(instance.map_of_empties, collections.OrderedDict):
        target_1 = (
            collections.OrderedDict()
        )  # type: typing.MutableMapping[str, str]
    else:
        target_1 = dict()

    for key_1, value_1 in instance.map_of_empties.items():
        target_1[key_1] = value_1.id
    target['map_of_empties'] = target_1

    return target


def serialize_some_graph(
        instance: some.graph.SomeGraph,
        ordered: bool = False
) -> typing.MutableMapping[str, typing.Any]:
    """
    serializes an instance of SomeGraph to a JSONable.

    :param instance: the instance of SomeGraph to be serialized
    :param ordered:
        If set, represents the instance properties and class registries
        as a ``collections.OrderedDict``.
        Otherwise, they are represented as a ``dict``.
    :return: JSONable representation
    """
    if ordered:
        target = (
            collections.OrderedDict()
        )  # type: typing.MutableMapping[str, typing.Any]
    else:
        target = dict()

    ##
    # Serialize global_reference_to_an_empty
    ##

    target['global_reference_to_an_empty'] = instance.global_reference_to_an_empty.id

    ##
    # Serialize instance registry of Empty
    ##

    if len(instance.empties) > 0:
        if ordered:
            target_empties = (
                collections.OrderedDict()
            )  # type: typing.MutableMapping[str, typing.Any]
        else:
            target_empties = dict()

        for id, empty_instance in instance.empties.items():
            if id != empty_instance.id:
                raise ValueError(
                    'Expected ID {!r} of the instance of Empty, but got: {!r}'.format(
                        id, empty_instance.id))

            target_empties[id] = serialize_empty(
                instance=empty_instance,
                ordered=ordered)
        target['empties'] = target_empties

    ##
    # Serialize instance registry of WithReference
    ##

    if len(instance.with_references) > 0:
        if ordered:
            target_with_references = (
                collections.OrderedDict()
            )  # type: typing.MutableMapping[str, typing.Any]
        else:
            target_with_references = dict()

        for id, with_reference_instance in instance.with_references.items():
            if id != with_reference_instance.id:
                raise ValueError(
                    'Expected ID {!r} of the instance of WithReference, but got: {!r}'.format(
                        id, with_reference_instance.id))

            target_with_references[id] = serialize_with_reference(
                instance=with_reference_instance,
                ordered=ordered)
        target['with_references'] = target_with_references

    return target


# File automatically generated by mapry. DO NOT EDIT OR APPEND!
