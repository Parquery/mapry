#!/usr/bin/env python3
"""Parse a mapry schema."""
import collections
import json
import pathlib
import re
from typing import (  # pylint: disable=unused-import
    Any, Mapping, MutableMapping, Optional)

import mapry
import mapry.naming
import mapry.validation


def _cpp_from_mapping(mapping: Mapping[str, Any]) -> mapry.Cpp:
    """
    Parse parameters for generation of C++ code.

    :param mapping: to be parsed
    :return: parsed parameters
    """
    cpp = mapry.Cpp()
    cpp.namespace = mapping['namespace']
    cpp.path_as = mapping['path_as']
    cpp.optional_as = mapping['optional_as']
    cpp.datetime_library = mapping['datetime_library']

    cpp.indention = mapping['indention'] if 'indention' in mapping else ' ' * 2

    return cpp


def _go_from_mapping(mapping: Mapping[str, Any]) -> mapry.Go:
    """
    Parse parameters for generation of Go code.

    :param mapping: to be parsed
    :return: parsed parameters
    """
    go = mapry.Go()  # pylint: disable=invalid-name
    go.package = mapping['package']

    return go


def _py_from_mapping(mapping: Mapping[str, Any]) -> mapry.Py:
    """
    Parse parameters for generation of Python code.

    :param mapping: to be parsed
    :return: parsed parameters
    """
    py = mapry.Py()  # pylint: disable=invalid-name
    py.module_name = mapping['module_name']
    py.path_as = mapping['path_as']
    py.timezone_as = mapping['timezone_as']

    py.indention = mapping['indention'] if 'indention' in mapping else ' ' * 4

    return py


def _class_from_mapping(mapping: Mapping[str, Any], ref: str) -> mapry.Class:
    """
    Parse the class from the mapping.

    All the fields are parsed except the properties, which are parsed
    in a separate step.

    :param mapping: to be parsed
    :param ref: reference to the class in the original mapry schema
    :return: parsed class without properties
    """
    name = mapping['name']

    # yapf: disable
    cls = mapry.Class(
        name=name,
        plural=(mapping['plural'] if 'plural' in mapping
                else mapry.naming.plural(identifier=name)),
        description=mapping['description'],
        ref=ref,
        id_pattern=(re.compile(mapping['id_pattern']) if 'id_pattern' in mapping
                    else None)
    )
    # yapf: enable

    return cls


def _embed_from_mapping(mapping: Mapping[str, Any], ref: str) -> mapry.Embed:
    """
    Parse the embed from the mapping.

    All the fields are parsed except the properties, which are parsed
    in a separate step.

    :param mapping: to be parsed
    :param ref: reference to the embeddable structure in the mapry schema
    :return: embeddable structure without the properties
    """
    return mapry.Embed(
        name=mapping['name'], description=mapping['description'], ref=ref)


def _recurse_type_from_mapping(
        mapping: Mapping[str, Any], classes: Mapping[str, mapry.Class],
        embeds: Mapping[str, mapry.Embed]) -> mapry.Type:
    """
    Parse recursively the type definition from the given mapping.

    :param mapping: to be parsed
    :param classes: pointer table to the classes
    :param embeds: pointer table to the embeddable structures
    :return: parsed type definition
    """
    # pylint: disable=too-many-return-statements
    # pylint: disable=too-many-branches
    type_identifier = mapping['type']

    if type_identifier == 'boolean':
        return mapry.Boolean()

    if type_identifier == 'integer':
        return mapry.Integer(
            minimum=int(mapping['minimum']) if 'minimum' in mapping else None,
            exclusive_minimum=bool(mapping['exclusive_minimum'])
            if 'exclusive_minimum' in mapping else False,
            maximum=int(mapping['maximum']) if 'maximum' in mapping else None,
            exclusive_maximum=bool(mapping['exclusive_maximum'])
            if 'exclusive_maximum' in mapping else False)

    if type_identifier == 'float':
        return mapry.Float(
            minimum=int(mapping['minimum']) if 'minimum' in mapping else None,
            exclusive_minimum=bool(mapping['exclusive_minimum'])
            if 'exclusive_minimum' in mapping else False,
            maximum=int(mapping['maximum']) if 'maximum' in mapping else None,
            exclusive_maximum=bool(mapping['exclusive_maximum'])
            if 'exclusive_maximum' in mapping else False)

    if type_identifier == 'string':
        return mapry.String(
            pattern=re.compile(mapping['pattern']) if 'pattern' in
            mapping else None)

    if type_identifier == 'path':
        return mapry.Path(
            pattern=re.compile(mapping['pattern']) if 'pattern' in
            mapping else None)

    if type_identifier == 'date':
        return mapry.Date(fmt=mapping.get('format', None))

    if type_identifier == 'time':
        return mapry.Time(fmt=mapping.get('format', None))

    if type_identifier == 'datetime':
        return mapry.Datetime(fmt=mapping.get('format', None))

    if type_identifier == 'time_zone':
        return mapry.TimeZone()

    if type_identifier == 'duration':
        return mapry.Duration()

    if type_identifier == 'array':
        return mapry.Array(
            values=_recurse_type_from_mapping(
                mapping=mapping['values'], classes=classes, embeds=embeds),
            minimum_size=int(mapping['minimum_size'])
            if 'minimum_size' in mapping else None,
            maximum_size=int(mapping['maximum_size'])
            if 'maximum_size' in mapping else None)

    if type_identifier == 'map':
        return mapry.Map(
            values=_recurse_type_from_mapping(
                mapping=mapping['values'], classes=classes, embeds=embeds))

    if type_identifier in classes:
        return classes[type_identifier]

    if type_identifier in embeds:
        return embeds[type_identifier]

    raise NotImplementedError(
        "Unhandled type identifier: {!r}".format(type_identifier))


def _property_from_mapping(
        name: str, mapping: Mapping[str, Any],
        classes: Mapping[str, mapry.Class], embeds: Mapping[str, mapry.Embed],
        ref: str, composite: mapry.Composite) -> mapry.Property:
    """
    Parse a property from the mapping.

    :param name: of the property
    :param mapping: to be parsed
    :param classes: pointer table to the classes
    :param embeds: pointer table to the embeddable structures
    :param ref: reference to the property in the original JSONable mapry schema
    :param composite: back-reference to the composite
    :return: parsed property
    """
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-branches
    prop = mapry.Property(
        ref=ref,
        name=name,
        description=mapping['description'],
        json=mapping.get('json', name),
        a_type=_recurse_type_from_mapping(
            mapping=mapping, classes=classes, embeds=embeds),
        optional=mapping.get('optional', False),
        composite=composite)

    prop.ref = ref
    prop.name = name
    prop.description = mapping['description']
    prop.json = mapping.get('json', name)

    prop.type = _recurse_type_from_mapping(
        mapping=mapping, classes=classes, embeds=embeds)

    prop.optional = mapping.get('optional', False)

    return prop


def _properties_from_mapping(
        mapping: Mapping[str, Any], classes: Mapping[str, mapry.Class],
        embeds: Mapping[str, mapry.Embed], ref: str,
        composite: mapry.Composite) -> MutableMapping[str, mapry.Property]:
    """
    Parse properties from the given mapping.

    :param mapping: to be parsed
    :param classes: pointer table to the classes
    :param embeds: pointer table to the embeddable structures
    :param ref: reference to the composite in the mapry schema
    :param composite: back-reference to the composite structure
    :return: parsed properties
    """
    properties = collections.OrderedDict(
    )  # type: MutableMapping[str, mapry.Property]

    if isinstance(mapping, collections.OrderedDict):
        mapping_items = list(mapping.items())
    else:
        # The sorting is necessary to make the unit tests a bit less verbose,
        # since defining OrderedDicts is quite tedious.
        mapping_items = sorted(mapping.items())

    for name, property_mapping in mapping_items:
        properties[name] = mapry.Property(
            ref='{}/{}'.format(ref, name),
            name=name,
            description=property_mapping['description'],
            json=property_mapping.get('json', name),
            a_type=_recurse_type_from_mapping(
                mapping=property_mapping, classes=classes, embeds=embeds),
            optional=property_mapping.get('optional', False),
            composite=composite)

    return properties


def schema_from_mapping(mapping: Mapping[str, Any], ref: str) -> mapry.Schema:
    """
    Parse mapry schema from the given mapping.

    :param mapping: to be parsed
    :param ref: reference path to the schema
    :return: parsed schema
    """
    # pylint: disable=too-many-branches
    errs = mapry.validation.validate(mapping=mapping, ref=ref)

    if errs:
        if len(errs) == 1:
            raise errs[0]
        else:
            raise mapry.validation.SchemaError(
                message="\n".join([str(err) for err in errs]), ref=ref)

    # Parse the definition of the object graph (except the properties which
    # are parsed at a later point once the classes and embeds are pre-allocated)
    graph = mapry.Graph()

    graph.ref = ref
    graph.name = mapping['name']
    graph.description = mapping['description']

    # Pre-allocate classes and embeds
    if 'classes' in mapping:
        for i, cls_mapping in enumerate(mapping['classes']):
            name = cls_mapping['name']
            graph.classes[name] = _class_from_mapping(
                mapping=cls_mapping, ref='{}/classes/{}'.format(ref, i))

    if 'embeds' in mapping:
        for i, embed_mapping in enumerate(mapping['embeds']):
            name = embed_mapping['name']
            graph.embeds[name] = _embed_from_mapping(
                mapping=embed_mapping, ref='{}/embeds/{}'.format(ref, i))

    # Parse the properties of the object graph
    if 'properties' in mapping:
        graph.properties = _properties_from_mapping(
            mapping=mapping['properties'],
            classes=graph.classes,
            embeds=graph.embeds,
            ref=ref,
            composite=graph)

        # Pack-reference properties
        for prop in graph.properties.values():
            prop.composite = graph

    # Parse class properties
    if 'classes' in mapping:
        for i, cls_mapping in enumerate(mapping['classes']):
            name = cls_mapping['name']
            cls = graph.classes[name]

            if 'properties' in cls_mapping:
                cls.properties = _properties_from_mapping(
                    mapping=cls_mapping['properties'],
                    classes=graph.classes,
                    embeds=graph.embeds,
                    ref='{}/classes/{}'.format(ref, i),
                    composite=cls)

                # Back-reference properties
                for prop in cls.properties.values():
                    prop.composite = cls

    # Parse embed properties
    if 'embeds' in mapping:
        for i, embed_mapping in enumerate(mapping['embeds']):
            name = embed_mapping['name']
            embed = graph.embeds[name]

            if 'properties' in embed_mapping:
                embed.properties = _properties_from_mapping(
                    mapping=embed_mapping['properties'],
                    classes=graph.classes,
                    embeds=graph.embeds,
                    ref='{}/embeds/{}'.format(ref, i),
                    composite=embed)

                # Back-reference properties
                for prop in embed.properties.values():
                    prop.composite = embed

    schema = mapry.Schema(
        graph=graph,
        cpp=_cpp_from_mapping(
            mapping=mapping['cpp']) if 'cpp' in mapping else None,
        go=_go_from_mapping(mapping=mapping['go']) if 'go' in mapping else None,
        py=_py_from_mapping(mapping=mapping['py']) if 'py' in mapping else None)

    return schema


class _OrderedDictPP(collections.OrderedDict):  # type: ignore
    """Pretty-print ordered dictionaries as JSON objects."""

    def __repr__(self) -> str:
        return "{{{}}}".format(
            ", ".join(
                ("{!r}: {!r}".format(key, val) for key, val in self.items())))


def schema_from_json_file(path: pathlib.Path) -> mapry.Schema:
    """
    Parse and validate the given JSON-encoded schema from a file.

    :param path: to the JSON-encoded mapry schema.
    :return: parsed schema
    """
    with path.open('rt') as fid:
        jsonerr = None  # type: Optional[json.JSONDecodeError]

        try:
            obj = json.load(fp=fid, object_pairs_hook=_OrderedDictPP)
            return schema_from_mapping(
                mapping=obj, ref='{}#'.format(path.as_posix()))
        except json.JSONDecodeError as err:
            jsonerr = err

        if jsonerr is not None:
            lines = path.read_text().splitlines()
            line = lines[jsonerr.lineno - 1]

            if len(line) <= 120:
                cursor = []
                for char in line[:jsonerr.colno - 1]:
                    if char not in [' ', '\t']:
                        cursor.append(' ')
                    else:
                        cursor.append(char)

                cursor.append('^')

                raise RuntimeError(
                    "Failed to json-decode {}:\n{}\n{}\n{}".format(
                        path, line, ''.join(cursor), jsonerr))
            else:
                raise RuntimeError(
                    "Failed to json-decode {}: {}".format(path, jsonerr))

        raise AssertionError("Expected an exception to be raised before.")
