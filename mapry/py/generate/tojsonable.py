"""Generate the code that serializes the object graph to a JSONable."""

import textwrap
from typing import List, Optional, Union  # pylint: disable=unused-import

from icontract import ensure

import mapry
import mapry.py.generate
import mapry.py.jinja2_env
import mapry.py.naming


@ensure(lambda result: not result.endswith('\n'))
def _imports(graph: mapry.Graph, py: mapry.Py) -> str:
    """
    Generate the import statements.

    :param graph: mapry definition of the object graph
    :param py: Python settings
    :return: generated code
    """
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements
    stdlib_block = {'import collections', 'import typing'}

    if mapry.needs_type(a_type=graph, query=mapry.Duration):
        stdlib_block.add('import datetime')

    if (mapry.needs_type(a_type=graph, query=mapry.Class)
            or mapry.needs_type(a_type=graph, query=mapry.Embed)):
        stdlib_block.add('import collections')

    first_party_block = {'import {}'.format(py.module_name)}

    # yapf: disable
    return '\n\n'.join([
        '\n'.join(sorted(stdlib_block)),
        '\n'.join(sorted(first_party_block))
    ])
    # yapf: enable


@ensure(lambda result: not result.endswith('\n'))
def _duration_to_string() -> str:
    """
    Generate the code for serializing durations to strings.

    :return: generated code
    """
    return textwrap.dedent(
        '''\
    _ZERO_TIMEDELTA = datetime.timedelta(0)


    def _duration_to_string(
            duration: datetime.timedelta) -> str:
        """
        serializes the duration to a string in ISO 8601 format.

        Since ``datetime.timedelta`` stores intervals only up to days and
        excludes longer intervals such as weeks, months and years,
        the serialized representation defines the duration only
        in terms of days and shorter intervals.

        :param duration: duration to be serialized
        :return: text representation

        >>> _duration_to_string(
        ...     datetime.timedelta(days=1, hours=2, minutes=3,
        ...     seconds=4, microseconds=5))
        'P1DT2H3M4.000005S'

        >>> _duration_to_string(
        ...     datetime.timedelta(hours=1, minutes=2, seconds=3))
        'PT1H2M3S'

        >>> _duration_to_string(
        ...     datetime.timedelta(seconds=1))
        'PT1S'

        >>> _duration_to_string(
        ...     datetime.timedelta(days=365.1))
        'P365DT2H24M'

        >>> _duration_to_string(
        ...     -datetime.timedelta(days=1))
        '-P1D'

        >>> _duration_to_string(
        ...     -datetime.timedelta(
        ...         days=1, hours=1, minutes=1,seconds=1,microseconds=1))
        '-P1DT1H1M1.000001S'

        """
        parts = []  # type: typing.List[str]

        absduration = duration
        if duration < _ZERO_TIMEDELTA:
            parts.append('-')
            absduration = -duration

        parts.append('P')
        if absduration.days > 0:
            parts.append('{}D'.format(absduration.days))

        if absduration.seconds > 0 or absduration.microseconds > 0:
            parts.append('T')

            rest = absduration.seconds
            hours = rest // 3600
            rest = rest % 3600

            minutes = rest // 60
            seconds = rest % 60

            if hours > 0:
                parts.append('{}H'.format(hours))

            if minutes > 0:
                parts.append('{}M'.format(minutes))

            if absduration.microseconds > 0:
                microseconds_str = '{:06}'.format(
                    absduration.microseconds).rstrip('0')

                parts.append('{}.{}S'.format(seconds, microseconds_str))
            elif seconds > 0:
                parts.append('{}S'.format(seconds))
            else:
                # No microseconds nor seconds
                pass

        return ''.join(parts)''')


_SERIALIZE_DATE_TIME_TPL = mapry.py.jinja2_env.ENV.from_string(
    '''\
{% if dt_format %}
{{ target_expr }} = {{ value_expr }}.strftime(
    {{ dt_format|repr }})
{% else %}
{{ target_expr }} = ""
{% endif %}{# /if dt_format #}
''')


@ensure(lambda result: not result.endswith('\n'))
def _serialize_date_time(
        target_expr: str, value_expr: str,
        a_type: Union[mapry.Date, mapry.Datetime, mapry.Time]) -> str:
    """
    Generate the code to serialize a date, a datetime or a time.

    The code serializes the ``value_expr`` into the ``target_expr``.

    :param target_expr: Python expression of the JSONable to be set
    :param value_expr: Python expression of the value to be serialized
    :param a_type: the mapry type of the value
    :param cpp: Python settings
    :return: generated serialization code
    """
    return _SERIALIZE_DATE_TIME_TPL.render(
        value_expr=value_expr, target_expr=target_expr,
        dt_format=a_type.format).rstrip()


def _jsonable_type_repr(a_type: mapry.Type) -> str:
    """
    Generate the string representation of the type corresponding to a JSONable.

    :param a_type: original mapry type of the serialized JSONable value
    :return: type annotation
    """
    if isinstance(a_type, mapry.Boolean):
        result = 'bool'
    elif isinstance(a_type, mapry.Integer):
        result = 'int'
    elif isinstance(a_type, mapry.Float):
        result = 'float'
    elif isinstance(a_type,
                    (mapry.String, mapry.Path, mapry.Date, mapry.Datetime,
                     mapry.Time, mapry.TimeZone, mapry.Duration, mapry.Class)):
        result = 'str'

    elif isinstance(a_type, mapry.Array):
        result = 'typing.List[{}]'.format(
            _jsonable_type_repr(a_type=a_type.values))

    elif isinstance(a_type, mapry.Map):
        result = 'typing.MutableMapping[str, {}]'.format(
            _jsonable_type_repr(a_type=a_type.values))

    elif isinstance(a_type, mapry.Embed):
        result = "typing.MutableMapping[str, typing.Any]"

    else:
        raise NotImplementedError(
            "Unhandled serialization expression of type: {}".format(a_type))

    return result


_SERIALIZE_ARRAY_TPL = mapry.py.jinja2_env.ENV.from_string(
    '''\
{% if direct_copy %}
{{ target_expr }} = (
    {{ value_expr|indent }}[:]
)
{% else %}{# /if direct_copy #}
{% if item_serialization_expr %}
target_{{ uid }} = [
    {{ item_serialization_expr|indent }}
    for item_{{ uid }} in {{ value_expr }}
]  # type: {{ jsonable_type_repr }}
{% else %}
target_{{ uid }} = (
    []
)  # type: {{ jsonable_type_repr }}
for item_{{ uid }} in {{ value_expr }}:
    {{ item_serialization|indent }}
    target_{{ uid }}.append(target_item_{{ uid }})
{% endif %}{# /if item_serialization_expr #}
{{ target_expr }} = target_{{ uid }}
{% endif %}{# /if direct_copy #}
''')


@ensure(lambda result: not result.endswith('\n'))
def _serialize_array(
        target_expr: str, value_expr: str, a_type: mapry.Array,
        auto_id: mapry.py.generate.AutoID, py: mapry.Py) -> str:
    """
    Generate the code to serialize an array.

    The code serializes the ``value_expr`` into the ``target_expr``.

    :param target_expr: Python expression of the JSONable to be set
    :param value_expr: Python expression of the value to be serialized
    :param a_type: the mapry type of the value
    :param auto_id: generator of unique identifiers
    :param py: Python settings
    :return: generated serialization code
    """
    uid = auto_id.next_identifier()

    ##
    # Determine if the serialization amounts to a plain copy of the list
    ##

    direct_copy = isinstance(
        a_type.values,
        (mapry.Boolean, mapry.Integer, mapry.Float, mapry.String))
    if py.path_as == 'str':
        direct_copy = direct_copy or isinstance(a_type.values, mapry.Path)

    if py.timezone_as == 'str':
        direct_copy = direct_copy or isinstance(a_type.values, mapry.TimeZone)

    ##
    # Determine the serialization
    ##
    item_serialization_expr = None  # type: Optional[str]
    item_serialization = None  # type: Optional[str]

    if not direct_copy:
        item_serialization_expr = _serialization_expr(
            value_expr='item_{uid}'.format(uid=uid),
            a_type=a_type.values,
            py=py)

        if item_serialization_expr is None:
            item_serialization = _serialize_value(
                target_expr="target_item_{uid}".format(uid=uid),
                value_expr="item_{uid}".format(uid=uid),
                a_type=a_type.values,
                auto_id=auto_id,
                py=py)

    assert (
        direct_copy ^ (item_serialization_expr is not None) ^
        (item_serialization is not None))

    return _SERIALIZE_ARRAY_TPL.render(
        uid=uid,
        value_expr=value_expr,
        jsonable_type_repr=_jsonable_type_repr(a_type=a_type),
        direct_copy=direct_copy,
        item_serialization_expr=item_serialization_expr,
        item_serialization=item_serialization,
        target_expr=target_expr).rstrip('\n')


_SERIALIZE_MAP_TPL = mapry.py.jinja2_env.ENV.from_string(
    '''\
if isinstance({{ value_expr }}, collections.OrderedDict):
    target_{{ uid }} = (
        collections.OrderedDict()
    )  # type: {{ jsonable_type_repr }}
else:
    target_{{ uid }} = dict()

for key_{{ uid }}, value_{{ uid }} in {{ value_expr }}.items():
    {% if item_serialization_expr %}
    target_{{ uid }}[key_{{ uid }}] = {{
        item_serialization_expr|indent|indent }}
    {% else %}
    {{ item_serialization|indent }}
    target_{{ uid }}[key_{{ uid }}] = target_value_{{ uid }}
    {% endif %}{# /if item_serialization_expr #}
{{ target_expr }} = target_{{ uid }}
''')


@ensure(lambda result: not result.endswith('\n'))
def _serialize_map(
        target_expr: str, value_expr: str, a_type: mapry.Map,
        auto_id: mapry.py.generate.AutoID, py: mapry.Py) -> str:
    """
    Generate the code to serialize a map.

    The code serializes the ``value_expr`` into the ``target_expr``.

    :param target_expr: Python expression of the JSONable to be set
    :param value_expr: Python expression of the value to be serialized
    :param a_type: the mapry type of the value
    :param auto_id: generator of unique identifiers
    :param cpp: Python settings
    :return: generated serialization code
    """
    uid = auto_id.next_identifier()

    ##
    # Determine the serialization
    ##

    item_serialization_expr = None  # type: Optional[str]
    item_serialization = None  # type: Optional[str]

    item_serialization_expr = _serialization_expr(
        value_expr='value_{uid}'.format(uid=uid), a_type=a_type.values, py=py)

    if item_serialization_expr is None:
        item_serialization = _serialize_value(
            target_expr="target_value_{uid}".format(uid=uid),
            value_expr="value_{uid}".format(uid=uid),
            a_type=a_type.values,
            auto_id=auto_id,
            py=py)

    assert ((item_serialization_expr is not None) ^
            (item_serialization is not None))

    return _SERIALIZE_MAP_TPL.render(
        uid=uid,
        value_expr=value_expr,
        jsonable_type_repr=_jsonable_type_repr(a_type=a_type),
        item_serialization_expr=item_serialization_expr,
        item_serialization=item_serialization,
        target_expr=target_expr).rstrip('\n')


@ensure(lambda result: result is None or not result.endswith('\n'))
def _serialization_expr(value_expr: str, a_type: mapry.Type,
                        py: mapry.Py) -> Optional[str]:
    """
    Generate the expression of the serialization of the given value.

    If no serialization expression can be generated (e.g., in case of nested
    structures such as arrays and maps), None is returned.

    :param value_expr: Python expression of the value to be serialized
    :param a_type: the mapry type of the value
    :param py: Python settings
    :return: generated expression, or None if not possible
    """
    result = None  # type: Optional[str]

    if isinstance(a_type,
                  (mapry.Boolean, mapry.Integer, mapry.Float, mapry.String)):
        result = value_expr

    elif isinstance(a_type, mapry.Path):
        if py.path_as == 'str':
            result = value_expr
        elif py.path_as == 'pathlib.Path':
            result = 'str({})'.format(value_expr)
        else:
            raise NotImplementedError(
                "Unhandled path_as: {}".format(py.path_as))

    elif isinstance(a_type, (mapry.Date, mapry.Datetime, mapry.Time)):
        result = '{value_expr}.strftime({dt_format!r})'.format(
            value_expr=value_expr, dt_format=a_type.format)

    elif isinstance(a_type, mapry.TimeZone):
        if py.timezone_as == 'str':
            result = value_expr
        elif py.timezone_as == 'pytz.timezone':
            result = 'str({})'.format(value_expr)
        else:
            raise NotImplementedError(
                'Unhandled timezone_as: {}'.format(py.timezone_as))

    elif isinstance(a_type, mapry.Duration):
        result = '_duration_to_string({})'.format(value_expr)

    elif isinstance(a_type, mapry.Array):
        result = None

    elif isinstance(a_type, mapry.Map):
        result = None

    elif isinstance(a_type, mapry.Class):
        result = "{}.id".format(value_expr)

    elif isinstance(a_type, mapry.Embed):
        result = "serialize_{}({})".format(
            mapry.py.naming.as_variable(a_type.name), value_expr)

    else:
        raise NotImplementedError(
            "Unhandled serialization expression of type: {}".format(a_type))

    return result


@ensure(lambda result: not result.endswith('\n'))
def _serialize_value(
        target_expr: str, value_expr: str, a_type: mapry.Type,
        auto_id: mapry.py.generate.AutoID, py: mapry.Py) -> str:
    """
    Generate the code to serialize a value.

    The code serializes the ``value_expr`` into the ``target_expr``.

    :param target_expr: Python expression of the JSONable to be set
    :param value_expr: Python expression of the value to be serialized
    :param a_type: the mapry type of the value
    :param auto_id: generator of unique identifiers
    :param py: Python settings
    :return: generated serialization code
    """
    result = ''

    serialization_expr = _serialization_expr(
        value_expr=value_expr, a_type=a_type, py=py)

    if serialization_expr is not None:
        result = '{} = {}'.format(target_expr, serialization_expr)

    elif isinstance(a_type, mapry.Array):
        result = _serialize_array(
            target_expr=target_expr,
            value_expr=value_expr,
            a_type=a_type,
            auto_id=auto_id,
            py=py)

    elif isinstance(a_type, mapry.Map):
        result = _serialize_map(
            target_expr=target_expr,
            value_expr=value_expr,
            a_type=a_type,
            auto_id=auto_id,
            py=py)

    else:
        raise NotImplementedError(
            "Unhandled serialization of type: {}".format(a_type))

    return result


_SERIALIZE_PROPERTY_TPL = mapry.py.jinja2_env.ENV.from_string(
    '''\
##
# Serialize {{ a_property.name|as_attribute }}
##

{% if a_property.optional %}
if {{ value_expr }} is not None:
    {{ serialization|indent }}
{% else %}
{{ serialization }}
{% endif %}{# /if a_property.optional #}
''')


@ensure(lambda result: not result.endswith('\n'))
def _serialize_property(
        target_expr: str, value_expr: str, a_property: mapry.Property,
        auto_id: mapry.py.generate.AutoID, py: mapry.Py) -> str:
    """
    Generate the code to serialize a property of a composite.

    The code serializes the ``value_expr`` into the ``target_expr``.

    :param target_expr: Python expression of the JSONable to be set
    :param value_expr: Python expression of the value to be serialized
    :param a_property: the property definition
    :param auto_id: generator of unique identifiers
    :param py: Python settings
    :return: generated serialization code
    """
    serialization = _serialize_value(
        target_expr=target_expr,
        value_expr=value_expr,
        a_type=a_property.type,
        auto_id=auto_id,
        py=py)

    return _SERIALIZE_PROPERTY_TPL.render(
        a_property=a_property,
        value_expr=value_expr,
        serialization=serialization).rstrip('\n')


_SERIALIZE_CLASS_OR_EMBED_TPL = mapry.py.jinja2_env.ENV.from_string(
    '''\
def serialize_{{ composite.name|as_variable }}(
        instance: {{ py.module_name }}.{{ composite.name|as_composite }},
        ordered: bool = False
) -> typing.MutableMapping[str, typing.Any]:
{% set doctext %}
serializes an instance of {{
    composite.name|as_composite }} to a JSONable representation.

:param instance: the instance of {{
    composite.name|as_composite }} to be serialized
:param ordered:
    If set, represents the instance as a ``collections.OrderedDict``.
    Otherwise, it is represented as a ``dict``.
:return: a JSONable{#
#}{% endset %}{# /set doctext #}
    {{ doctext|as_docstring|indent }}
    if ordered:
        target = (
            collections.OrderedDict()
        )  # type: typing.MutableMapping[str, typing.Any]
    else:
        target = dict()
    {% for serialization in property_serializations %}

    {{ serialization|indent }}
    {% endfor %}

    return target
''')


@ensure(lambda result: not result.endswith('\n'))
def _serialize_class_or_embed(
        class_or_embed: Union[mapry.Class, mapry.Embed], py: mapry.Py) -> str:
    """
    Generate the function that serializes a class or an embeddable structure.

    :param class_or_embed:
        a mapry definition of the class or the embeddable structure
    :param py: Python settings
    :return: generated code
    """
    auto_id = mapry.py.generate.AutoID()

    # yapf: disable
    property_serializations = [
        _serialize_property(
            target_expr="target[{}]".format(repr(prop.json)),
            value_expr="instance.{}".format(prop.name),
            a_property=prop,
            auto_id=auto_id,
            py=py)
        for prop in class_or_embed.properties.values()
    ]
    # yapf: enable

    return _SERIALIZE_CLASS_OR_EMBED_TPL.render(
        composite=class_or_embed,
        property_serializations=property_serializations,
        py=py)


_SERIALIZE_GRAPH_TPL = mapry.py.jinja2_env.ENV.from_string(
    '''\
def serialize_{{ graph.name|as_variable }}(
        instance: {{ py.module_name }}.{{ graph.name|as_composite }},
        ordered: bool = False
) -> typing.MutableMapping[str, typing.Any]:
{% set doctext %}
serializes an instance of {{ graph.name|as_composite }} to a JSONable.

:param instance: the instance of {{ graph.name|as_composite }} to be serialized
:param ordered:
    {% if graph.classes %}
    If set, represents the instance properties and class registries
    as a ``collections.OrderedDict``.
    {% else %}
    If set, represents the instance properties as a ``collections.OrderedDict``.
    {% endif %}{# /if graph.classes #}
    Otherwise, they are represented as a ``dict``.
:return: JSONable representation{#
#}{% endset %}{# /set doctext #}
    {{ doctext|as_docstring|indent }}
    if ordered:
        target = (
            collections.OrderedDict()
        )  # type: typing.MutableMapping[str, typing.Any]
    else:
        target = dict()
    {% for serialization in property_serializations %}{##

        Serialize graph properties

    ##}

    {{ serialization|indent }}
    {% endfor %}{# /for serialization #}
    {% for cls in graph.classes.values() %}{##

        Serialize class registries

    ##}

    ##
    # Serialize instance registry of {{ cls.name|as_composite }}
    ##

    if len(instance.{{ cls.plural|as_variable }}) > 0:
        if ordered:
            target_{{ cls.plural|as_variable }} = (
                collections.OrderedDict()
            )  # type: typing.MutableMapping[str, typing.Any]
        else:
            target_{{ cls.plural|as_variable }} = dict()

        for id, {{ cls.name|as_variable }}_instance in instance.{{
            cls.plural|as_attribute }}.items():
            if id != {{ cls.name|as_variable }}_instance.id:
                raise ValueError(
                    {{ "Expected ID {!r} of the instance of %s, but got: {!r}"|
                        format(cls.name|as_composite)|repr }}.format(
                        id, {{ cls.name|as_variable }}_instance.id))

            target_{{ cls.plural|as_variable }}[id] = serialize_{{
                cls.name|as_variable }}(
                instance={{ cls.name|as_variable }}_instance,
                ordered=ordered)
        target[{{ cls.plural|json_plural|repr }}] = target_{{
            cls.plural|as_variable }}
    {% endfor %}{# /for cls #}

    return target
''')


@ensure(lambda result: not result.endswith('\n'))
def _serialize_graph(graph: mapry.Graph, py: mapry.Py) -> str:
    """
    Generate the implementation of the function that serializes a mapry graph.

    :param graph: mapry definition of the object graph
    :param py: Python settings
    :return: generated code
    """
    auto_id = mapry.py.generate.AutoID()

    # yapf: disable
    property_serializations = [
        _serialize_property(
            target_expr="target[{}]".format(repr(prop.json)),
            value_expr="instance.{}".format(
                mapry.py.naming.as_attribute(prop.name)),
            a_property=prop,
            auto_id=auto_id,
            py=py)
        for prop in graph.properties.values()
    ]
    # yapf: enable

    return _SERIALIZE_GRAPH_TPL.render(
        graph=graph, property_serializations=property_serializations,
        py=py).rstrip('\n')


@ensure(lambda result: result.endswith('\n'))
def generate(graph: mapry.Graph, py: mapry.Py) -> str:
    """
    Generate the source file to parse an object graph from a JSONable object.

    :param graph: mapry definition of the object graph
    :param py: Python settings
    :return: content of the source file
    """
    blocks = [
        mapry.py.generate.WARNING,
        mapry.py.generate.docstring("serializes to JSONable objects."),
        _imports(graph=graph, py=py)
    ]

    if mapry.needs_type(a_type=graph, query=mapry.Duration):
        blocks.append(_duration_to_string())

    nongraph_composites = []  # type: List[Union[mapry.Class, mapry.Embed]]
    nongraph_composites.extend(graph.classes.values())
    nongraph_composites.extend(graph.embeds.values())

    for class_or_embed in nongraph_composites:
        blocks.append(
            _serialize_class_or_embed(class_or_embed=class_or_embed, py=py))

    blocks.append(_serialize_graph(graph=graph, py=py))

    blocks.append(mapry.py.generate.WARNING)

    return '\n\n\n'.join(blocks) + '\n'
