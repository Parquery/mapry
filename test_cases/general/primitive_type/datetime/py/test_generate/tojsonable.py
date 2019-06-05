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
    # Serialize some_datetime
    ##

    target['some_datetime'] = instance.some_datetime.strftime('%Y/%m/%d %H-%M-%SZ')

    ##
    # Serialize formatless_datetime
    ##

    target['formatless_datetime'] = instance.formatless_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')

    return target


# File automatically generated by mapry. DO NOT EDIT OR APPEND!