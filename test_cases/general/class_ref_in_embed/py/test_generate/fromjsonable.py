# File automatically generated by mapry. DO NOT EDIT OR APPEND!


"""parses JSONable objects."""


import collections
import typing

import some.graph
import some.graph.parse


def _empty_from(
        value: typing.Any,
        ref: str,
        target: some.graph.Empty,
        errors: some.graph.parse.Errors
) -> None:
    """
    parses Empty from a JSONable value.

    If ``errors``, the attributes of ``target`` have undefined values.

    :param value: JSONable value
    :param ref:
        reference to the value (e.g., a reference path)
    :param target: parsed ``value`` as Empty
    :param errors: errors encountered during parsing
    :return:

    """
    if not isinstance(value, dict):
        errors.add(
            ref,
            "Expected a dictionary, but got: {}".format(
                type(value)))
        return


def empty_from(
        value: typing.Any,
        id: str,
        ref: str,
        errors: some.graph.parse.Errors
) -> typing.Optional[some.graph.Empty]:
    """
    parses Empty from a JSONable value.

    :param value: JSONable value
    :param id: identifier of the instance
    :param ref:
        reference to the value (e.g., a reference path)
    :param errors: errors encountered during parsing
    :return: parsed instance, or None if ``errors``

    """
    target = some.graph.parse.placeholder_empty(id=id)

    _empty_from(
        value=value,
        ref=ref,
        target=target,
        errors=errors)

    if not errors.empty():
       return None

    return target


def _embed_with_ref_from(
        value: typing.Any,
        empties_registry: typing.Mapping[
            str,
            some.graph.Empty],
        ref: str,
        target: some.graph.EmbedWithRef,
        errors: some.graph.parse.Errors
) -> None:
    """
    parses EmbedWithRef from a JSONable value.

    If ``errors``, the attributes of ``target`` have undefined values.

    :param value: JSONable value
    :param empties_registry: registry of the Empty instances
    :param ref:
        reference to the value (e.g., a reference path)
    :param target: parsed ``value`` as EmbedWithRef
    :param errors: errors encountered during parsing
    :return:

    """
    if not isinstance(value, dict):
        errors.add(
            ref,
            "Expected a dictionary, but got: {}".format(
                type(value)))
        return

    ##
    # Parse reference_to_empty
    ##

    value_0 = value.get(
        'reference_to_empty',
        None)

    if value_0 is None:
        errors.add(
            ref,
            'Property is missing: reference_to_empty')
    else:
        if not isinstance(value_0, str):
            errors.add(
                '/'.join((
                    ref, 'reference_to_empty')),
                "Expected a str, but got: {}".format(
                    type(value_0)))
        else:
            target_1 = empties_registry.get(
                value_0,
                None)
            if target_1 is None:
                errors.add(
                    '/'.join((
                        ref, 'reference_to_empty')),
                    'Reference to an instance of class Empty not found: {}'.format(
                        value_0))
            else:
                target.reference_to_empty = target_1
    if errors.full():
        return


def embed_with_ref_from(
        value: typing.Any,
        empties_registry: typing.Mapping[
            str,
            some.graph.Empty],
        ref: str,
        errors: some.graph.parse.Errors
) -> typing.Optional[some.graph.EmbedWithRef]:
    """
    parses EmbedWithRef from a JSONable value.

    :param value: JSONable value
    :param id: identifier of the instance
    :param empties_registry:
        registry of the Empty instances
    :param ref:
        reference to the value (e.g., a reference path)
    :param errors: errors encountered during parsing
    :return: parsed instance, or None if ``errors``

    """
    target = some.graph.parse.placeholder_embed_with_ref()

    _embed_with_ref_from(
        value=value,
        empties_registry=empties_registry,
        ref=ref,
        target=target,
        errors=errors)

    if not errors.empty():
       return None

    return target


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
    # Pre-allocate empties
    ##

    registry_value = value.get('empties', None)

    if registry_value is not None:
        if not isinstance(registry_value, dict):
            errors.add(
                '/'.join((
                    ref, 'empties')),
                "Expected a dictionary, but got: {}".format(
                    type(registry_value)))
        else:
            if isinstance(registry_value, collections.OrderedDict):
                graph.empties = collections.OrderedDict()
            else:
                graph.empties = dict()

            empties_registry = graph.empties
            for id in registry_value:
                empties_registry[id] = some.graph.parse.placeholder_empty(id=id)

    if errors.full():
        return None

    # Errors from pre-allocation are considered critical.
    if not errors.empty():
        return None

    ##
    # Parse empties
    ##

    if 'empties' in value:
        registry_value = value['empties']
        for id, instance_value in registry_value.items():
            target_empty = graph.empties[id]
            target_empty.id = id

            _empty_from(
                instance_value,
                '/'.join((
                    ref, 'empties', repr(id))),
                target_empty,
                errors)

            if errors.full():
                return None

    ##
    # Parse some_embed
    ##

    value_0 = value.get(
        'some_embed',
        None)

    if value_0 is None:
        errors.add(
            ref,
            'Property is missing: some_embed')
    else:
        target_1 = (
            some.graph.parse.placeholder_embed_with_ref()
        )
        _embed_with_ref_from(
            value_0,
            graph.empties,
            '/'.join((
                ref, 'some_embed')),
            target_1,
            errors)
        graph.some_embed = target_1

    if errors.full():
        return None

    if not errors.empty():
        return None

    return graph
