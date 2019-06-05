"""Generate the code that defines the types of the object graph."""
from typing import Set  # pylint: disable=unused-import

from icontract import ensure

import mapry
import mapry.go.generate
import mapry.go.jinja2_env
import mapry.indention
import mapry.naming


@ensure(lambda result: not result.endswith('\n'))
def _imports(graph: mapry.Graph) -> str:
    """
    Generate the import declaration(s).

    :param graph: mapry definition of the object graph
    :return: generated code
    """
    import_set = set()  # type: Set[str]

    # yapf: disable
    if any(mapry.needs_type(a_type=graph, query=query)
           for query in (mapry.Date, mapry.Time, mapry.Datetime,
                         mapry.Duration, mapry.TimeZone)):
        # yapf: enable
        import_set.add('time')

    return mapry.go.generate.import_declarations(import_set=import_set)


@ensure(lambda result: not result.endswith('\n'))
def _property_type_repr(a_property: mapry.Property, go: mapry.Go) -> str:
    """
    Generate the Go type representation of a property.

    :param a_property: property of a mapry composite
    :param go: Go settings
    :return: generated code
    """
    type_repr = mapry.go.generate.type_repr(a_type=a_property.type, go=go)
    if a_property.optional:
        if mapry.go.generate.is_pointer_type(a_type=a_property.type):
            return type_repr
        else:
            return "*{}".format(type_repr)

    return type_repr


_DEFINE_CLASS_TPL = mapry.go.jinja2_env.ENV.from_string(
    '''\
{% if cls.description %}
{% set doctext %}
{{ cls.name|ucamel_case }} {{ cls.description }}
{% endset %}{# /set doctext #}
{{ doctext|comment }}
{% endif %}{# /if cls.description #}
type {{ cls.name|ucamel_case }} struct {
    // identifies the instance
    ID string
    {% for prop in cls.properties.values() %}

    {% if prop.description %}
    {{ prop.description|comment|indent }}
    {% endif %}
    {{ prop.name|ucamel_case }} {{ property_type[prop] }}
    {% endfor %}{# /for prop #}
}
''')


@ensure(lambda result: not result.endswith('\n'))
def _define_class(cls: mapry.Class, go: mapry.Go) -> str:
    """
    Generate the code that defines the given class.

    :param cls: mapry definition of the class
    :param go: Go settings
    :return: generated code
    """
    # yapf: disable
    return _DEFINE_CLASS_TPL.render(
        cls=cls,
        property_type={
            prop: _property_type_repr(a_property=prop, go=go)
            for prop in cls.properties.values()
        }).rstrip()
    # yapf: enable


_DEFINE_EMBED_TPL = mapry.go.jinja2_env.ENV.from_string(
    '''\
{% if embed.description %}
{% set doctext %}
{{ embed.name|ucamel_case }} {{ embed.description }}
{% endset %}{# /set doctext #}
{{ doctext|comment }}
{% endif %}{# /if embed.description #}
type {{ embed.name|ucamel_case }} struct {
    {% set newliner = joiner('NEWLINE') %}
    {% for prop in embed.properties.values() %}{#
    #}{% if newliner() %}{{ '\n' }}{% endif %}
    {% if prop.description %}
    {{ prop.description|comment|indent }}
    {% endif %}
    {{ prop.name|ucamel_case }} {{ property_type[prop] }}
    {% endfor %}{# /for prop #}
}
''')


@ensure(lambda result: not result.endswith('\n'))
def _define_embed(embed: mapry.Embed, go: mapry.Go) -> str:
    """
    Generate the code that defines the given embeddable structure.

    :param embed: mapry definition of the embeddable structure
    :param go: Go settings
    :return: generated code
    """
    # yapf: disable
    return _DEFINE_EMBED_TPL.render(
        embed=embed,
        property_type={
            prop: _property_type_repr(a_property=prop, go=go)
            for prop in embed.properties.values()
        }).rstrip()
    # yapf: enable


_DEFINE_GRAPH_TPL = mapry.go.jinja2_env.ENV.from_string(
    '''\
{% if graph.description %}
{% set doctext %}
{{ graph.name|ucamel_case }} {{ graph.description }}
{% endset %}{# /set doctext #}
{{ doctext|comment }}
{% endif %}{# /if graph.description #}
type {{ graph.name|ucamel_case }} struct {
    {% set newliner = joiner('NEWLINE') %}
    {% for cls in graph.classes.values() %}{#
    #}{% if newliner() %}{{ '\n' }}{% endif %}
    // registers instances of {{ cls.name|ucamel_case }}.
    {{ cls.plural|ucamel_case }} map[string]*{{ cls.name|ucamel_case }}
    {% endfor %}
    {% for prop in graph.properties.values() %}{#
    #}{% if newliner() %}{{ '\n' }}{% endif %}
    {% if prop.description %}
    {{ prop.description|comment|indent }}
    {% endif %}
    {{ prop.name|ucamel_case }} {{ property_type[prop] }}
    {% endfor %}{# /for prop #}
}
''')


@ensure(lambda result: not result.endswith('\n'))
def _define_graph(graph: mapry.Graph, go: mapry.Go) -> str:
    """
    Generate the code that defines the object graph.

    :param graph: mapry definition of the object graph
    :param go: Go settings
    :return: generated code
    """
    # yapf: disable
    return _DEFINE_GRAPH_TPL.render(
        graph=graph,
        property_type={
            prop: _property_type_repr(a_property=prop, go=go)
            for prop in graph.properties.values()
        }).rstrip()
    # yapf: enable


@ensure(lambda result: result.endswith('\n'))
def generate(graph: mapry.Graph, go: mapry.Go) -> str:
    """
    Generate the source file that defines the types of the object graph.

    :param graph: definition of the object graph
    :param go: Go settings
    :return: content of the source file
    """
    blocks = ['package {}'.format(go.package), mapry.go.generate.WARNING]

    import_block = _imports(graph=graph)
    if len(import_block) > 0:
        blocks.append(import_block)

    for embed in graph.embeds.values():
        blocks.append(_define_embed(embed=embed, go=go))

    for cls in graph.classes.values():
        blocks.append(_define_class(cls=cls, go=go))

    blocks.append(_define_graph(graph=graph, go=go))

    blocks.append(mapry.go.generate.WARNING)

    return mapry.indention.reindent(
        text='\n\n'.join(blocks) + '\n', indention='\t')
