# File automatically generated by mapry. DO NOT EDIT OR APPEND!


"""parses JSONable objects."""


import collections
import re
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


def _with_reference_from(
        value: typing.Any,
        empties_registry: typing.Mapping[
            str,
            some.graph.Empty],
        ref: str,
        target: some.graph.WithReference,
        errors: some.graph.parse.Errors
) -> None:
    """
    parses WithReference from a JSONable value.

    If ``errors``, the attributes of ``target`` have undefined values.

    :param value: JSONable value
    :param empties_registry: registry of the Empty instances
    :param ref:
        reference to the value (e.g., a reference path)
    :param target: parsed ``value`` as WithReference
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
    # Parse reference_to_an_empty
    ##

    value_0 = value.get(
        'reference_to_an_empty',
        None)

    if value_0 is None:
        errors.add(
            ref,
            'Property is missing: reference_to_an_empty')
    else:
        if not isinstance(value_0, str):
            errors.add(
                '/'.join((
                    ref, 'reference_to_an_empty')),
                "Expected a str, but got: {}".format(
                    type(value_0)))
        else:
            target_1 = empties_registry.get(
                value_0,
                None)
            if target_1 is None:
                errors.add(
                    '/'.join((
                        ref, 'reference_to_an_empty')),
                    'Reference to an instance of class Empty not found: {}'.format(
                        value_0))
            else:
                target.reference_to_an_empty = target_1
    if errors.full():
        return

    ##
    # Parse array_of_empties
    ##

    value_2 = value.get(
        'array_of_empties',
        None)

    if value_2 is None:
        errors.add(
            ref,
            'Property is missing: array_of_empties')
    else:
        if not isinstance(value_2, list):
            errors.add(
                '/'.join((
                    ref, 'array_of_empties')),
                "Expected a list, but got: {}".format(
                    type(value_2)))
        else:
            target_3 = (
                []
            )  # type: typing.List[some.graph.Empty]
            for i_3, item_3 in enumerate(
                    value_2):
                target_item_3 = (
                    None
                )  # type: typing.Optional[some.graph.Empty]
                if not isinstance(item_3, str):
                    errors.add(
                        '/'.join((
                            ref, 'array_of_empties', str(i_3))),
                        "Expected a str, but got: {}".format(
                            type(item_3)))
                else:
                    target_4 = empties_registry.get(
                        item_3,
                        None)
                    if target_4 is None:
                        errors.add(
                            '/'.join((
                                ref, 'array_of_empties', str(i_3))),
                            'Reference to an instance of class Empty not found: {}'.format(
                                item_3))
                    else:
                        target_item_3 = target_4

                if target_item_3 is not None:
                    target_3.append(
                        target_item_3)

                if errors.full():
                    break

            target.array_of_empties = target_3
    if errors.full():
        return

    ##
    # Parse map_of_empties
    ##

    value_5 = value.get(
        'map_of_empties',
        None)

    if value_5 is None:
        errors.add(
            ref,
            'Property is missing: map_of_empties')
    else:
        if not isinstance(value_5, dict):
            errors.add(
                '/'.join((
                    ref, 'map_of_empties')),
                "Expected a dict, but got: {}".format(
                    type(value_5)))
        else:
            if isinstance(value_5, collections.OrderedDict):
                target_6 = (
                    collections.OrderedDict()
                )  # type: typing.MutableMapping[str, some.graph.Empty]
            else:
                target_6 = (
                    dict()
                )

            for key_6, value_6 in value_5.items():
                if not isinstance(key_6, str):
                    errors.add(
                        '/'.join((
                            ref, 'map_of_empties')),
                        "Expected the key to be a str, but got: {}".format(
                            type(key_6)))

                    if errors.full():
                        break
                    else:
                        continue

                target_item_6 = (
                    None
                )  # type: typing.Optional[some.graph.Empty]
                if not isinstance(value_6, str):
                    errors.add(
                        '/'.join((
                            ref, 'map_of_empties', repr(key_6))),
                        "Expected a str, but got: {}".format(
                            type(value_6)))
                else:
                    target_7 = empties_registry.get(
                        value_6,
                        None)
                    if target_7 is None:
                        errors.add(
                            '/'.join((
                                ref, 'map_of_empties', repr(key_6))),
                            'Reference to an instance of class Empty not found: {}'.format(
                                value_6))
                    else:
                        target_item_6 = target_7

                if target_item_6 is not None:
                    target_6[key_6] = target_item_6

                if errors.full():
                    break

            if target_6 is not None:
                target.map_of_empties = target_6
    if errors.full():
        return


def with_reference_from(
        value: typing.Any,
        id: str,
        empties_registry: typing.Mapping[
            str,
            some.graph.Empty],
        ref: str,
        errors: some.graph.parse.Errors
) -> typing.Optional[some.graph.WithReference]:
    """
    parses WithReference from a JSONable value.

    :param value: JSONable value
    :param id: identifier of the instance
    :param empties_registry:
        registry of the Empty instances
    :param ref:
        reference to the value (e.g., a reference path)
    :param errors: errors encountered during parsing
    :return: parsed instance, or None if ``errors``

    """
    target = some.graph.parse.placeholder_with_reference(id=id)

    _with_reference_from(
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
                if not re.match(
                        r'^[a-zA-Z_\-][a-zA-Z_0-9\-]*$',
                        id):
                    errors.add(
                        '/'.join((
                            ref, 'empties')),
                        'Expected ID to match ^[a-zA-Z_\\-][a-zA-Z_0-9\\-]*$, but got: ' + id)

                    if errors.full():
                        break

                empties_registry[id] = some.graph.parse.placeholder_empty(id=id)

    if errors.full():
        return None

    ##
    # Pre-allocate with_references
    ##

    registry_value = value.get('with_references', None)

    if registry_value is not None:
        if not isinstance(registry_value, dict):
            errors.add(
                '/'.join((
                    ref, 'with_references')),
                "Expected a dictionary, but got: {}".format(
                    type(registry_value)))
        else:
            if isinstance(registry_value, collections.OrderedDict):
                graph.with_references = collections.OrderedDict()
            else:
                graph.with_references = dict()

            with_references_registry = graph.with_references
            for id in registry_value:
                with_references_registry[id] = some.graph.parse.placeholder_with_reference(id=id)

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
    # Parse with_references
    ##

    if 'with_references' in value:
        registry_value = value['with_references']
        for id, instance_value in registry_value.items():
            target_with_reference = graph.with_references[id]
            target_with_reference.id = id

            _with_reference_from(
                instance_value,
                graph.empties,
                '/'.join((
                    ref, 'with_references', repr(id))),
                target_with_reference,
                errors)

            if errors.full():
                return None

    ##
    # Parse global_reference_to_an_empty
    ##

    value_0 = value.get(
        'global_reference_to_an_empty',
        None)

    if value_0 is None:
        errors.add(
            ref,
            'Property is missing: global_reference_to_an_empty')
    else:
        if not isinstance(value_0, str):
            errors.add(
                '/'.join((
                    ref, 'global_reference_to_an_empty')),
                "Expected a str, but got: {}".format(
                    type(value_0)))
        else:
            target_1 = graph.empties.get(
                value_0,
                None)
            if target_1 is None:
                errors.add(
                    '/'.join((
                        ref, 'global_reference_to_an_empty')),
                    'Reference to an instance of class Empty not found: {}'.format(
                        value_0))
            else:
                graph.global_reference_to_an_empty = target_1

    if errors.full():
        return None

    if not errors.empty():
        return None

    return graph
