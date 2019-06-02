#!/usr/bin/env python3
"""Validate the mapry schema."""

import collections
import re
from typing import Any, Dict, List, Mapping, Optional, Set, Tuple

import jsonschema  # type: ignore
import lexery

import mapry.naming
import mapry.schemas
import mapry.strftime

# yapf: enable


class SchemaError(Exception):
    """Define an error in the schema."""

    def __init__(self, message: str, ref: str) -> None:
        """
        Initialize the schema error.

        :param message: of the error
        :param ref: reference to the error (*e.g.*, a reference path)
        """
        self.ref = ref
        super().__init__("{}: {}".format(ref, message))


def _validate_names(mapping: Mapping[str, Any],
                    ref: str) -> Tuple[Set[str], List[SchemaError]]:
    """
    Validate names of classes and embeddable structures.

    :param mapping: representing the mapry schema
    :param ref: reference path to the mapry definition
    :return: set of structure names, list of errors
    """
    errs = []  # type: List[SchemaError]

    names = {mapping['name']}

    if 'classes' in mapping:
        for i, obj in enumerate(mapping['classes']):
            name = obj['name']
            if name in names:
                errs.append(
                    SchemaError(
                        message="Duplicate names: {!r}".format(name),
                        ref="{}/classes/{}/name".format(ref, i)))

            names.add(name)

    if 'embeds' in mapping:
        for i, obj in enumerate(mapping['embeds']):
            name = obj['name']
            if name in names:
                errs.append(
                    SchemaError(
                        message="Duplicate names: {!r}".format(name),
                        ref="{}/embeds/{}/name".format(ref, i)))

            names.add(name)

    return names, errs


def _validate_class(mapping: Mapping[str, Any], ref: str) -> List[SchemaError]:
    """
    Check that the mapping defines correctly a mapry class.

    The ``properties`` are validated in a separate step, since we need to
    construct the list of available classes beforehand.

    :param mapping: of the class to be validated
    :param ref: reference path to the class
    :return: list of errors
    """
    errs = []  # type: List[SchemaError]

    if 'id_pattern' in mapping:
        try:
            re.compile(mapping['id_pattern'])
        except Exception as err:  # pylint: disable=broad-except
            errs.append(
                SchemaError(
                    message='Invalid regular expression: {}'.format(err),
                    ref='{}/id_pattern'.format(ref)))

    if 'properties' in mapping:
        if 'id' in mapping['properties']:
            errs.append(
                SchemaError(
                    message="'id' is a reserved property of the class. "
                    "If you want a pattern for class identifiers, "
                    "use 'id_pattern'.",
                    ref='{}/properties'.format(ref)))

    return errs


_PROPERTY_RE = re.compile(r'^[a-zA-Z]([a-zA-Z0-9_]*[a-zA-Z0-9])?$')
_NONCOMPOSITE_TYPE_SET = {
    'boolean', 'integer', 'float', 'string', 'path', 'date', 'time', 'datetime',
    'duration', 'time_zone', 'array', 'map'
}


def _validate_type_against_schema(
        mapping: Mapping[str, Any], ref: str,
        json_schema: Dict[str, Any]) -> Optional[SchemaError]:
    """
    Validate the type definition against the given json schema.

    :param mapping: to be validated
    :param ref: to the type definition
    :param json_schema: JSON schema to validate against
    :return: error, if any
    """
    try:
        jsonschema.validate(instance=mapping, schema=json_schema)
    except jsonschema.ValidationError as err:
        pth = '/'.join(err.path)
        return SchemaError(
            message="Invalid {} definition: {}".format(
                mapping['type'], err.message),
            ref='{}/{}'.format(ref, pth))

    return None


def _validate_integer(mapping: Mapping[str, Any],
                      ref: str) -> Optional[SchemaError]:
    """
    Validate the definition of an integer value.

    :param mapping: representing the type definition to be validated
    :param ref: reference to the type definition
    :return: error, if any
    """
    if 'minimum' in mapping and 'maximum' in mapping:
        minimum = mapping['minimum']
        maximum = mapping['maximum']

        if minimum > maximum:
            return SchemaError(
                message="minimum (== {}) > maximum (== {})".format(
                    minimum, maximum),
                ref=ref)

        excl_min = False if 'exclusive_minimum' not in mapping \
            else bool(mapping['exclusive_minimum'])
        excl_max = False if 'exclusive_maximum' not in mapping \
            else bool(mapping['exclusive_maximum'])

        if excl_min and excl_max:
            if minimum == maximum:
                return SchemaError(
                    message=(
                        "minimum (== {}) == maximum and "
                        "both are set to exclusive").format(minimum),
                    ref=ref)
        elif not excl_min and excl_max:
            if minimum == maximum:
                return SchemaError(
                    message=(
                        "minimum (== {}) == maximum and "
                        "maximum is set to exclusive").format(minimum),
                    ref=ref)
        elif excl_min and not excl_max:
            if minimum == maximum:
                return SchemaError(
                    message=(
                        "minimum (== {}) == maximum and "
                        "maximum is set to exclusive").format(minimum),
                    ref=ref)
        elif not excl_min and not excl_max:
            # If minimum == maximum it is ok to have
            # >= minimum and <= maximum as a constraint.
            pass
        else:
            raise AssertionError("Unexpected code path")

    return None


def _validate_float(mapping: Mapping[str, Any],
                    ref: str) -> Optional[SchemaError]:
    """
    Validate the definition of a float value.

    :param mapping: representing the type definition to be validated
    :param ref: reference to the type definition
    :return: error, if any
    """
    if 'minimum' in mapping and 'maximum' in mapping:
        minimum = mapping['minimum']
        maximum = mapping['maximum']

        if minimum > maximum:
            return SchemaError(
                "minimum (== {}) > maximum".format(minimum), ref=ref)

        excl_min = False if 'exclusive_minimum' not in mapping \
            else bool(mapping['exclusive_minimum'])
        excl_max = False if 'exclusive_maximum' not in mapping \
            else bool(mapping['exclusive_maximum'])

        if excl_min and excl_max:
            if minimum == maximum:
                return SchemaError(
                    message=(
                        "minimum (== {}) == maximum and "
                        "both are set to exclusive").format(minimum),
                    ref=ref)
        elif not excl_min and excl_max:
            if minimum == maximum:
                return SchemaError((
                    "minimum (== {}) == maximum and "
                    "maximum is set to exclusive").format(minimum),
                                   ref=ref)
        elif excl_min and not excl_max:
            if minimum == maximum:
                return SchemaError((
                    "minimum (== {}) == maximum and "
                    "maximum is set to exclusive").format(minimum),
                                   ref=ref)
        elif not excl_min and not excl_max:
            # If minimum == maximum it is ok to have
            # >= minimum and <= maximum as a constraint.
            pass
        else:
            raise AssertionError("Unexpected code path")

    return None


def _validate_string(mapping: Mapping[str, Any],
                     ref: str) -> Optional[SchemaError]:
    """
    Validate the definition of a string value.

    :param mapping: representing the type definition to be validated
    :param ref: reference to the type definition
    :return: error, if any
    """
    if 'pattern' in mapping:
        try:
            _ = re.compile(mapping['pattern'])
        except Exception as err:  # pylint: disable=broad-except
            return SchemaError(str(err), ref='{}/pattern'.format(ref))

    return None


def _validate_path(mapping: Mapping[str, Any],
                   ref: str) -> Optional[SchemaError]:
    """
    Validate the definition of a path value.

    :param mapping: representing the type definition to be validated
    :param ref: reference to the type definition
    :return: error, if any
    """
    if 'pattern' in mapping:
        try:
            _ = re.compile(mapping['pattern'])
        except Exception as err:  # pylint: disable=broad-except
            return SchemaError(str(err), ref='{}/pattern'.format(ref))

    return None


def _validate_date(mapping: Mapping[str, Any],
                   ref: str) -> Optional[SchemaError]:
    """
    Validate the definition of a date value.

    :param mapping: representing the type definition to be validated
    :param ref: reference to the type definition
    :return: error, if any
    """
    if 'format' in mapping:
        token_lines = None  # type: Optional[List[List[lexery.Token]]]
        try:
            token_lines = mapry.strftime.tokenize(format=mapping['format'])
        except (lexery.Error, NotImplementedError) as err:
            return SchemaError(str(err), ref='{}/format'.format(ref))

        valerr = mapry.strftime.validate_date_tokens(token_lines=token_lines)
        if valerr is not None:
            return SchemaError(str(valerr), ref='{}/format'.format(ref))

    return None


def _validate_time(mapping: Mapping[str, Any],
                   ref: str) -> Optional[SchemaError]:
    """
    Validate the definition of a time value.

    :param mapping: representing the type definition to be validated
    :param ref: reference to the type definition
    :return: error, if any
    """
    if 'format' in mapping:
        token_lines = None  # type: Optional[List[List[lexery.Token]]]
        try:
            token_lines = mapry.strftime.tokenize(format=mapping['format'])
        except (lexery.Error, NotImplementedError) as err:
            return SchemaError(str(err), ref='{}/format'.format(ref))

        valerr = mapry.strftime.validate_time_tokens(token_lines=token_lines)
        if valerr is not None:
            return SchemaError(str(valerr), ref='{}/format'.format(ref))

    return None


def _validate_datetime(mapping: Mapping[str, Any],
                       ref: str) -> Optional[SchemaError]:
    """
    Validate the definition of a time value.

    :param mapping: representing the type definition to be validated
    :param ref: reference to the type definition
    :return: error, if any
    """
    if 'format' in mapping:
        try:
            _ = mapry.strftime.tokenize(format=mapping['format'])
        except (lexery.Error, NotImplementedError) as err:
            return SchemaError(str(err), ref='{}/format'.format(ref))

    return None


def _validate_array(
        mapping: Mapping[str, Any], ref: str, types: Set[str],
        depth: int) -> Optional[SchemaError]:
    """
    Validate the definition of an array value.

    :param mapping: representing the type definition to be validated
    :param ref: reference to the type definition
    :param types: set of allowed composable data types
    :param depth: of the recursion, starting with 0
    :return: error, if any
    """
    minimum_size = mapping.get('minimum_size', None)
    maximum_size = mapping.get('maximum_size', None)
    if (minimum_size is not None and maximum_size is not None
            and minimum_size > maximum_size):
        return SchemaError(
            message=(
                "Minimum size is larger than the maximum size: "
                "{} > {}").format(minimum_size, maximum_size),
            ref='{}/minimum_size'.format(ref))

    return _validate_type_recursively(
        mapping=mapping['values'],
        ref='{}/values'.format(ref),
        types=types,
        depth=depth + 1)


def _validate_map(
        mapping: Mapping[str, Any], ref: str, types: Set[str],
        depth: int) -> Optional[SchemaError]:
    """
    Validate the definition of a map value.

    :param mapping: representing the type definition to be validated
    :param ref: reference to the type definition
    :param types: set of allowed composable data types
    :param depth: of the recursion, starting with 0
    :return: error, if any
    """
    return _validate_type_recursively(
        mapping=mapping['values'],
        ref='{}/values'.format(ref),
        types=types,
        depth=depth + 1)


def _validate_type_recursively(
        mapping: Mapping[str, Any], ref: str, types: Set[str],
        depth: int) -> Optional[SchemaError]:
    """
    Validate the type definition recursively.

    :param mapping: representing the type definition to be validated
    :param ref: reference to the type definition
    :param types: set of allowed composable data types
    :param depth: of the recursion, starting with 0
    :return: error, if any
    """
    # pylint: disable=too-many-return-statements
    # pylint: disable=too-many-branches

    if depth == 0:
        # Enforce the type identifier and the description
        # at the top of the definition
        if isinstance(mapping, collections.OrderedDict):
            keys = list(mapping.keys())
            if keys[0] != 'type':
                return SchemaError(
                    message=(
                        "Expected 'type' at the top of the definition, "
                        "but got {}").format(keys[0]),
                    ref='{}/type'.format(ref))

            if 'description' in mapping and keys[1] != 'description':
                return SchemaError(
                    message=(
                        "Expected 'description' just after 'type' "
                        "in the definition, but got {}").format(keys[1]),
                    ref='{}/description'.format(ref))

    if mapping['type'] not in types:
        return SchemaError(
            message="Invalid type: {}".format(mapping['type']),
            ref='{}/type'.format(ref))

    # Validate against the type schema
    if mapping['type'] in mapry.schemas.TYPE_TO_SCHEMA:
        type_schema = mapry.schemas.TYPE_TO_SCHEMA[mapping['type']]
        scherr = _validate_type_against_schema(
            mapping=mapping, ref=ref, json_schema=type_schema)
        if scherr is not None:
            return scherr

    # Collect expected mapping keys;
    # the default 'type' and 'description' always apply.
    expected_keys = {"type", "description"}

    # If this is a property type definition (and not a nested type definition)
    # expect all the property keys.
    if depth == 0:
        expected_keys.update(
            mapry.schemas.GRAPH["definitions"]["Property"]  # type: ignore
            ["properties"].keys())

    # If this is a non-composite type, add extra type-specific expected keys.
    if mapping['type'] in mapry.schemas.TYPE_TO_SCHEMA:
        type_schema = mapry.schemas.TYPE_TO_SCHEMA[mapping['type']]
        expected_keys.update(type_schema["properties"].keys())  # type: ignore

    for key in mapping:
        if key not in expected_keys:
            return SchemaError(
                message=(
                    "Additional properties are not allowed "
                    "({!r} was unexpected)").format(key),
                ref=ref)

    # Validate logic
    if mapping['type'] == 'boolean':
        return None  # no logical checks for booleans

    if mapping['type'] == 'integer':
        return _validate_integer(mapping=mapping, ref=ref)

    if mapping['type'] == 'float':
        return _validate_float(mapping=mapping, ref=ref)

    if mapping['type'] == 'string':
        return _validate_string(mapping=mapping, ref=ref)

    if mapping['type'] == 'path':
        return _validate_path(mapping=mapping, ref=ref)

    if mapping['type'] == 'date':
        return _validate_date(mapping=mapping, ref=ref)

    if mapping['type'] == 'time':
        return _validate_time(mapping=mapping, ref=ref)

    if mapping['type'] == 'datetime':
        return _validate_datetime(mapping=mapping, ref=ref)

    if mapping['type'] == 'duration':
        return None  # no logical checks for durations

    if mapping['type'] == 'time_zone':
        return None  # no logical checks for time_zones

    if mapping['type'] == 'array':
        return _validate_array(
            mapping=mapping, ref=ref, types=types, depth=depth)

    if mapping['type'] == 'map':
        return _validate_map(mapping=mapping, ref=ref, types=types, depth=depth)

    if mapping['type'] in _NONCOMPOSITE_TYPE_SET:
        raise AssertionError("Unhandled type: {}".format(mapping['type']))

    # It's a composite; composite types lack "type" property.
    return None


def _validate_property(mapping: Mapping[str, Any], ref: str,
                       types: Set[str]) -> Optional[SchemaError]:
    """
    Check that the mapping correctly defines a property .

    :param mapping: to be validated
    :param ref: reference to the property
    :param types: set of allowed data types
    :return: error, if any
    """
    return _validate_type_recursively(
        mapping=mapping, ref=ref, types=types, depth=0)


def _validate_properties(mapping: Mapping[str, Any], ref: str,
                         types: Set[str]) -> List[SchemaError]:
    """
    Validate the properties given as a mapping.

    :param mapping: to be validated
    :param ref: reference to the properties object
    :param types: set of allowed data types
    :return: list of errors
    """
    errs = []  # type: List[SchemaError]

    if 'properties' not in mapping:
        return []

    for name, property_mapping in mapping['properties'].items():
        if not _PROPERTY_RE.match(name):
            errs.append(
                SchemaError(
                    message=("Property name invalid, expected {}, "
                             "got {}").format(_PROPERTY_RE.pattern, name),
                    ref="{}/properties".format(ref)))

        err = _validate_property(
            mapping=property_mapping,
            ref="{}/properties/{}".format(ref, name),
            types=types)
        if err is not None:
            errs.append(err)

    return errs


def _validate_plurals(mapping: Mapping[str, Any],
                      ref: str) -> List[SchemaError]:
    """
    Check that no graph field conflicts with a instance registry field.

     The instance registry field is identified with a plural of the class.

    :param mapping: schema mapping to be validated
    :param ref: reference to the schema
    :return: list of schema errors or an empty list, if no errors
    """
    if 'classes' not in mapping:
        return []

    if 'properties' not in mapping:
        return []

    registry_property_to_class_name = dict()  # type: Dict[str, str]

    for cls_mapping in mapping['classes']:
        if 'plural' in cls_mapping:
            plural = cls_mapping['plural']
        else:
            # Ignore a class that does not have a valid name.
            # Assume that this error will be caught by
            # the JSON schema validation.
            if 'name' not in cls_mapping:
                continue

            plural = mapry.naming.plural(identifier=cls_mapping['name'])

        plural_as_property = mapry.naming.json_plural(a_plural=plural)
        registry_property_to_class_name[plural_as_property] = (
            cls_mapping['name'])

    errs = []  # type: List[SchemaError]

    if isinstance(mapping['properties'], collections.OrderedDict):
        property_names = list(mapping['properties'].keys())
    else:
        property_names = sorted(mapping['properties'].keys())

    for property_name in property_names:
        if property_name in registry_property_to_class_name:
            errs.append(
                SchemaError(
                    message=(
                        'Graph property {!r} conflicts with the plural '
                        'necessary for the registry of class {!r}').format(
                            property_name,
                            registry_property_to_class_name[property_name]),
                    ref='{}/{}'.format(ref, property_name)))

    return errs


def validate(mapping: Mapping[str, Any], ref: str) -> List[SchemaError]:
    """
    Validate the given mapping as a mapry schema.

    :param mapping: defines a mapry schema.
    :param ref:
        reference to the source of the mapry schema (*e.g.*, a path or URL)
    :return: list of schema errors or an empty list, if no errors
    """
    # pylint: disable=too-many-branches

    valid_err = None  # type: Optional[jsonschema.ValidationError]
    try:
        jsonschema.validate(instance=mapping, schema=mapry.schemas.GRAPH)
    except jsonschema.ValidationError as err:
        valid_err = err

    if valid_err is not None:
        return [
            SchemaError(
                message="Does not follow json schema: {}".format(
                    valid_err.message),
                ref='/'.join([ref] + [str(part) for part in valid_err.path]))
        ]

    errors = []  # type: List[SchemaError]

    # Enforce name and description to be at the top of the schema
    if isinstance(mapping, collections.OrderedDict):
        mapping_keys = list(mapping.keys())

        if mapping_keys[0] != 'name':
            errors.append(
                SchemaError(
                    message=(
                        "Expected name to be the first property of the schema, "
                        "but got {}").format(mapping_keys[0]),
                    ref='{}/name'.format(ref)))

        if mapping_keys[1] != 'description':
            errors.append(
                SchemaError(
                    message=(
                        "Expected description to be the second property "
                        "of the schema, but got {}").format(mapping_keys[1]),
                    ref='{}/description'.format(ref)))

    # Register classes and embeds and
    # check that there are no duplicate class or embed names.
    name_set, name_errs = _validate_names(mapping=mapping, ref=ref)
    errors.extend(name_errs)

    # Validate class fields except properties
    if 'classes' in mapping:
        for i, cls_mapping in enumerate(mapping['classes']):
            errors.extend(
                _validate_class(
                    mapping=cls_mapping, ref='{}/classes/{}'.format(ref, i)))

    # Validate properties of the classes and embeds
    types = _NONCOMPOSITE_TYPE_SET.copy()
    types.update(name_set)

    # Check that the graph properties are valid
    errors.extend(_validate_properties(mapping=mapping, ref=ref, types=types))

    # Check that the properties of the classes are valid
    if 'classes' in mapping:
        for i, cls_mapping in enumerate(mapping['classes']):
            errors.extend(
                _validate_properties(
                    mapping=cls_mapping,
                    ref='{}/classes/{}'.format(ref, i),
                    types=types))

    # Check that the properties of the embeds are valid
    if 'embeds' in mapping:
        for i, embed_mapping in enumerate(mapping['embeds']):
            errors.extend(
                _validate_properties(
                    mapping=embed_mapping,
                    ref='{}/embeds/{}'.format(ref, i),
                    types=types))

    # Check that all the plurals of the classes
    # do not conflict any of the graph properties
    errors.extend(_validate_plurals(mapping=mapping, ref=ref))

    return errors
