#!/usr/bin/env python3
"""Generate the code that serializes the object graph to a JSONable."""

import textwrap
from typing import List, Set, Union  # pylint: disable=unused-import

from icontract import ensure

import mapry
import mapry.go.generate
import mapry.go.jinja2_env
import mapry.go.timeformat
import mapry.indention
import mapry.naming
import mapry.strftime


@ensure(lambda result: not result.endswith('\n'))
def _imports(graph: mapry.Graph) -> str:
    """
    Generate the import declaration.

    :param graph: mapry definition of the object graph
    :return: generated code
    """
    import_set = set()  # type: Set[str]

    if graph.classes:
        import_set.add("fmt")

    if mapry.needs_type(a_type=graph, query=mapry.Duration):
        import_set.add("fmt")
        import_set.add("strings")
        import_set.add("time")

    return mapry.go.generate.import_declarations(import_set)


@ensure(lambda result: not result.endswith('\n'))
def _duration_to_string() -> str:
    """
    Generate the code for serializing durations to strings.

    :return: generated code
    """
    return textwrap.dedent(
        '''\
    // durationToString represents the duration as a string in ISO 8601 format.
    //
    // Since time.Duration stores intervals as nanoseconds and excludes longer
    // intervals such as minutes, days or months, durationToString
    // infers the integral number of these longer intervals and
    // produces a compact representation.
    func durationToString(d time.Duration) string {
        parts := make([]string, 0, 7)

        ////
        // Interprete
        ////

        sign := 1
        if d < 0 {
            d = -d
            sign = -1
        }

        days := d / (24 * time.Hour)
        rest := d % (24 * time.Hour)

        hours := rest / time.Hour
        rest = rest % time.Hour

        minutes := rest / time.Minute
        rest = rest % time.Minute

        seconds := rest / time.Second
        rest = rest % time.Second

        nanoseconds := rest

        ////
        // Represent
        ////

        if sign < 0 {
            parts = append(parts, "-")
        }

        parts = append(parts, "P")

        if days > 0 {
            parts = append(
                parts,
                fmt.Sprintf("%dD", days))
        }

        if hours > 0 || minutes > 0 || seconds > 0 || nanoseconds > 0 {
            parts = append(parts, "T")

            if hours > 0 {
                parts = append(
                    parts,
                    fmt.Sprintf("%dH", hours))
            }

            if minutes > 0 {
                parts = append(
                    parts,
                    fmt.Sprintf("%dM", minutes))
            }

            if nanoseconds == 0 {
                if seconds > 0 {
                    parts = append(
                        parts,
                        fmt.Sprintf("%dS", seconds))
                }
            } else {
                parts = append(
                    parts,
                    strings.TrimRight(
                        fmt.Sprintf("%d.%09d", seconds, nanoseconds),
                        "0"))
                parts = append(parts, "S")
            }
        }

        return strings.Join(parts, "")
    }''')


_SERIALIZE_DATE_TIME_TPL = mapry.go.jinja2_env.ENV.from_string(
    '''\
{% if dt_format %}
{{ target_expr }} = {{ value_expr }}.Format(
    {{ dt_format|escaped_str }})
{% else %}
{{ target_expr }} = ""
{% endif %}{# /if dt_format #}
''')


@ensure(lambda result: not result.endswith('\n'))
def _serialize_date_time(
        target_expr: str, value_expr: str,
        a_type: Union[mapry.Date, mapry.Datetime, mapry.Time]) -> str:
    """
    Generate the code to serialize a date or a time.

    The code serializes the ``value_expr`` into the ``target_expr``.

    :param target_expr: Go expression of the JSONable to be set
    :param value_expr: Go expression of the value to be serialized
    :param a_type: the mapry type of the value
    :param cpp: Go settings
    :return: generated serialization code
    """
    return _SERIALIZE_DATE_TIME_TPL.render(
        value_expr=value_expr,
        target_expr=target_expr,
        dt_format=mapry.go.timeformat.convert(a_type.format)).rstrip()


_SERIALIZE_ARRAY_TPL = mapry.go.jinja2_env.ENV.from_string(
    '''\
count{{ uid }} := len({{ value_expr }})
slice{{ uid }} := {{ value_expr }}
target{{ uid }} := make([]interface{}, count{{ uid }})
for i{{ uid }} := 0; i{{ uid }} < count{{ uid }}; i{{ uid }}++ {
    {{ item_serialization|indent }}
}
{{ target_expr }} = target{{ uid }}
''')


@ensure(lambda result: not result.endswith('\n'))
def _serialize_array(
        target_expr: str, value_expr: str, a_type: mapry.Array,
        auto_id: mapry.go.generate.AutoID, go: mapry.Go) -> str:
    """
    Generate the code to serialize an array.

    The code serializes the ``value_expr`` into the ``target_expr``.

    :param target_expr: Go expression of the JSONable to be set
    :param value_expr: Go expression of the value to be serialized
    :param a_type: the mapry type of the value
    :param auto_id: generator of unique identifiers
    :param go: Go settings
    :return: generated serialization code
    """
    uid = auto_id.next_identifier()

    item_serialization = _serialize_value(
        target_expr="target{uid}[i{uid}]".format(uid=uid),
        value_expr="slice{uid}[i{uid}]".format(uid=uid),
        a_type=a_type.values,
        auto_id=auto_id,
        go=go)

    return _SERIALIZE_ARRAY_TPL.render(
        uid=uid,
        value_expr=value_expr,
        item_serialization=item_serialization,
        target_expr=target_expr)


_SERIALIZE_MAP_TPL = mapry.go.jinja2_env.ENV.from_string(
    '''\
target{{ uid }} := make(map[string]interface{})
map{{ uid }} := {{ value_expr }}
for k{{ uid }}, v{{ uid }} := range map{{ uid }} {
    {{ item_serialization|indent }}
}
{{ target_expr }} = target{{ uid }}
''')


@ensure(lambda result: not result.endswith('\n'))
def _serialize_map(
        target_expr: str, value_expr: str, a_type: mapry.Map,
        auto_id: mapry.go.generate.AutoID, go: mapry.Go) -> str:
    """
    Generate the code to serialize a map.

    The code serializes the ``value_expr`` into the ``target_expr``.

    :param target_expr: Go expression of the JSONable to be set
    :param value_expr: Go expression of the value to be serialized
    :param a_type: the mapry type of the value
    :param auto_id: generator of unique identifiers
    :param go: Go settings
    :return: generated serialization code
    """
    uid = auto_id.next_identifier()

    item_serialization = _serialize_value(
        target_expr="target{uid}[k{uid}]".format(uid=uid),
        value_expr="v{uid}".format(uid=uid),
        a_type=a_type.values,
        auto_id=auto_id,
        go=go)

    return _SERIALIZE_MAP_TPL.render(
        uid=uid,
        value_expr=value_expr,
        item_serialization=item_serialization,
        target_expr=target_expr)


@ensure(lambda result: not result.endswith('\n'))
def _serialize_value(
        target_expr: str, value_expr: str, a_type: mapry.Type,
        auto_id: mapry.go.generate.AutoID, go: mapry.Go) -> str:
    """
    Generate the code to serialize a value.

    The code serializes the ``value_expr`` into the ``target_expr``.

    :param target_expr: Go expression of the JSONable to be set
    :param value_expr: Go expression of the value to be serialized
    :param a_type: the mapry type of the value
    :param auto_id: generator of unique identifiers
    :param go: Go settings
    :return: generated serialization code
    """
    result = ''

    if isinstance(
            a_type,
        (mapry.Boolean, mapry.Integer, mapry.Float, mapry.String, mapry.Path)):
        result = '{} = {}'.format(target_expr, value_expr)

    elif isinstance(a_type, (mapry.Date, mapry.Datetime, mapry.Time)):
        result = _serialize_date_time(
            target_expr=target_expr, value_expr=value_expr, a_type=a_type)

    elif isinstance(a_type, mapry.TimeZone):
        result = '{} = {}.String()'.format(target_expr, value_expr)

    elif isinstance(a_type, mapry.Duration):
        result = textwrap.dedent(
            '''\
            {} = durationToString(
                {})'''.format(target_expr, value_expr))

    elif isinstance(a_type, mapry.Array):
        result = _serialize_array(
            target_expr=target_expr,
            value_expr=value_expr,
            a_type=a_type,
            auto_id=auto_id,
            go=go)

    elif isinstance(a_type, mapry.Map):
        result = _serialize_map(
            target_expr=target_expr,
            value_expr=value_expr,
            a_type=a_type,
            auto_id=auto_id,
            go=go)

    elif isinstance(a_type, mapry.Class):
        result = "{} = {}.ID".format(target_expr, value_expr)

    elif isinstance(a_type, mapry.Embed):
        result = textwrap.dedent(
            '''\
            {} = {}ToJSONable(
                &{})'''.format(
                target_expr, mapry.naming.ucamel_case(a_type.name), value_expr))

    else:
        raise NotImplementedError(
            "Unhandled serialization of type: {}".format(a_type))

    return result


_SERIALIZE_PROPERTY_TPL = mapry.go.jinja2_env.ENV.from_string(
    '''\
////
// Serialize {{ a_property.name|ucamel_case }}
////

{% if a_property.optional %}
if {{ value_expr }} != nil {
    {{ serialization|indent }}
}
{% else %}
{{ serialization }}
{% endif %}{# /if a_property.optional #}
''')


@ensure(lambda result: not result.endswith('\n'))
def _serialize_property(
        target_expr: str, value_expr: str, a_property: mapry.Property,
        auto_id: mapry.go.generate.AutoID, go: mapry.Go) -> str:
    """
    Generate the code to serialize a property of a composite.

    The code serializes the ``value_expr`` into the ``target_expr``.

    :param target_expr: Go expression of the JSONable to be set
    :param value_expr: Go expression of the value to be serialized
    :param a_property: the property definition
    :param auto_id: generator of unique identifiers
    :param go: Go settings
    :return: generated serialization code
    """
    if not a_property.optional:
        serialization = _serialize_value(
            target_expr=target_expr,
            value_expr=value_expr,
            a_type=a_property.type,
            auto_id=auto_id,
            go=go)

    else:
        is_pointer_type = mapry.go.generate.is_pointer_type(
            a_type=a_property.type)

        serialization = _serialize_value(
            target_expr=target_expr,
            value_expr=(
                value_expr if is_pointer_type else "(*{})".format(value_expr)),
            a_type=a_property.type,
            auto_id=auto_id,
            go=go)

    return _SERIALIZE_PROPERTY_TPL.render(
        a_property=a_property,
        value_expr=value_expr,
        serialization=serialization).rstrip('\n')


_SERIALIZE_CLASS_OR_EMBED_TPL = mapry.go.jinja2_env.ENV.from_string(
    '''\
// {{ composite.name|ucamel_case }}ToJSONable converts the instance to
// a JSONable representation.
//
// {{ composite.name|ucamel_case }}ToJSONable requires:
//  * instance != nil
//
// {{ composite.name|ucamel_case }}ToJSONable ensures:
//  * target != nil
func {{ composite.name|ucamel_case }}ToJSONable(
    instance *{{ composite.name|ucamel_case }}) (
    target map[string]interface{}) {

    if instance == nil {
        panic("unexpected nil instance")
    }

    target = make(map[string]interface{})
    {% for serialization in property_serializations %}

    {{ serialization|indent }}
    {% endfor %}{# /for serialization #}

    return
}''')


@ensure(lambda result: not result.endswith('\n'))
def _serialize_class_or_embed(
        class_or_embed: Union[mapry.Class, mapry.Embed], go: mapry.Go) -> str:
    """
    Generate the function that serializes a class or an embeddable structure.

    :param class_or_embed:
        a mapry definition of the class or the embeddable structure
    :param go: Go settings
    :return: generated code
    """
    auto_id = mapry.go.generate.AutoID()

    # yapf: disable
    property_serializations = [
        _serialize_property(
            target_expr="target[{}]".format(
                mapry.go.generate.escaped_str(prop.json)),
            value_expr="instance.{}".format(
                mapry.naming.ucamel_case(prop.name)),
            a_property=prop,
            auto_id=auto_id,
            go=go)
        for prop in class_or_embed.properties.values()
    ]
    # yapf: enable

    return _SERIALIZE_CLASS_OR_EMBED_TPL.render(
        composite=class_or_embed,
        property_serializations=property_serializations)


_SERIALIZE_GRAPH_TPL = mapry.go.jinja2_env.ENV.from_string(
    '''\
// {{
    graph.name|ucamel_case
    }} converts the instance to a JSONable representation.
//
// {{ graph.name|ucamel_case }} requires:
//  * instance != nil
//
// {{ graph.name|ucamel_case }} ensures:
//  * (err == nil && target != nil) || (err != nil && target == nil)
func {{ graph.name|ucamel_case }}ToJSONable(
    instance *{{ graph.name|ucamel_case }}) (
    target map[string]interface{}, err error) {

    if instance == nil {
        panic("unexpected nil instance")
    }

    target = make(map[string]interface{})
    defer func() {
        if err != nil {
            target = nil
        }
    }(){##

        Serialize graph properties

    ##}{% for serialization in property_serializations %}

    {{ serialization|indent }}
    {% endfor %}{# /for serialization #}{##

        Serialize class registries

    ##}{% for cls in graph.classes.values() %}

    ////
    // Serialize instance registry of {{ cls.name|ucamel_case }}
    ////

    if len(instance.{{ cls.plural|ucamel_case }}) > 0 {
        target{{ cls.plural|ucamel_case }} := make(map[string]interface{})
        for id := range instance.{{ cls.plural|ucamel_case }} {
            {{
                cls.name|camel_case }}Instance := instance.{{
                    cls.plural|ucamel_case }}[id]

            if id != {{ cls.name|camel_case }}Instance.ID {
                err = fmt.Errorf(
                    {{ "expected the instance of %s to have the ID %%s "
                        "according to the registry, but got: %%s"
                        |format(cls.name|ucamel_case)|escaped_str }},
                    id, {{ cls.name|camel_case }}Instance.ID)
                return
            }

            target{{
                cls.plural|ucamel_case }}[id] = {{
                    cls.name|ucamel_case }}ToJSONable(
                {{ cls.name|camel_case }}Instance)
        }

        target[{{
            cls.plural|json_plural|escaped_str }}] = target{{
                cls.plural|ucamel_case }}
    }
    {% endfor %}{# /for cls #}

    return
}
''')


@ensure(lambda result: not result.endswith('\n'))
def _serialize_graph(graph: mapry.Graph, go: mapry.Go) -> str:
    """
    Generate the function that serializes the object graph.

    :param graph: mapry definition of the object graph
    :param go: Go settings
    :return: generated code
    """
    auto_id = mapry.go.generate.AutoID()

    # yapf: disable
    property_serializations = [
        _serialize_property(
            target_expr="target[{}]".format(
                    mapry.go.generate.escaped_str(prop.json)),
            value_expr="instance.{}".format(
                    mapry.naming.ucamel_case(prop.name)),
            a_property=prop,
            auto_id=auto_id,
            go=go)
        for prop in graph.properties.values()
    ]
    # yapf: enable

    return _SERIALIZE_GRAPH_TPL.render(
        graph=graph,
        property_serializations=property_serializations,
        package=go.package).rstrip('\n')


@ensure(lambda result: result.endswith('\n'))
def generate(graph: mapry.Graph, go: mapry.Go) -> str:
    """
    Generate the source file to serialize an object graph to a JSONable object.

    :param graph: mapry definition of the object graph
    :param go: Go settings
    :return: content of the source file
    """
    blocks = [
        'package {}'.format(go.package),
        mapry.go.generate.WARNING,
    ]

    import_block = _imports(graph=graph)
    if len(import_block) > 0:
        blocks.append(import_block)

    if mapry.needs_type(a_type=graph, query=mapry.Duration):
        blocks.append(_duration_to_string())

    nongraph_composites = []  # type: List[Union[mapry.Class, mapry.Embed]]
    nongraph_composites.extend(graph.classes.values())
    nongraph_composites.extend(graph.embeds.values())

    for class_or_embed in nongraph_composites:
        blocks.append(
            _serialize_class_or_embed(class_or_embed=class_or_embed, go=go))

    blocks.append(_serialize_graph(graph=graph, go=go))

    blocks.append(mapry.go.generate.WARNING)

    return mapry.indention.reindent(
        text='\n\n'.join(blocks) + '\n', indention='\t')
