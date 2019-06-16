# File automatically generated by mapry. DO NOT EDIT OR APPEND!


"""parses JSONable objects."""


import typing

import some.graph
import some.graph.parse


def some_graph_from(
        value: typing.Any,
        ref: str,
        errors: some.graph.parse.Errors
) -> typing.Optional[some.graph.SomeGraph]:
    """
    parses SomeGraph from a JSONable value.

    :param value: JSONable value
    :param ref: reference to the value (e.g., a reference path)
    :param errors: errors encountered during parsing
    :return: parsed SomeGraph, or None if ``errors``
    """
    if errors.full():
        return None

    if not isinstance(value, dict):
        errors.add(
            ref,
            "Expected a dictionary, but got: {}".format(type(value)))
        return None

    graph = some.graph.parse.placeholder_some_graph()

    ##
    # Parse some_bool
    ##

    value_0 = value.get(
        'SOME-BOOL',
        None)

    if value_0 is None:
        errors.add(
            ref,
            'Property is missing: SOME-BOOL')
    else:
        if not isinstance(value_0, bool):
            errors.add(
                '/'.join((
                    ref, 'SOME-BOOL')),
                "Expected a bool, but got: {}".format(
                    type(value_0)))
        else:
            graph.some_bool = value_0

    if errors.full():
        return None

    if not errors.empty():
        return None

    return graph
