# File automatically generated by mapry. DO NOT EDIT OR APPEND!


"""serializes to JSONable objects."""


import collections
import typing

import some.graph


def serialize_some_graph(
        instance: some.graph.SomeGraph,
        ordered: bool = False
) -> typing.MutableMapping[str, typing.Any]:
    """
    serializes an instance of SomeGraph to a JSONable.

    :param instance: the instance of SomeGraph to be serialized
    :param ordered:
        If set, represents the instance properties as a ``collections.OrderedDict``.
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
    # Serialize some_bool
    ##

    target['some_bool'] = instance.some_bool

    return target


# File automatically generated by mapry. DO NOT EDIT OR APPEND!
