"""Generate the code that defines the types of the object graph."""
from typing import List, Optional, Set  # pylint: disable=unused-import

from icontract import ensure

import mapry
import mapry.cpp.generate
import mapry.cpp.jinja2_env
import mapry.indention


@ensure(lambda result: not result.endswith('\n'))
def _includes(graph: mapry.Graph, cpp: mapry.Cpp) -> str:
    """
    Generate the include directives.

    :param graph: mapry definition of the object graph
    :param cpp: C++ settings
    :return: generated code
    """
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements
    stl_block = set()  # type: Set[str]
    third_party_block = set()  # type: Set[str]

    if mapry.needs_type(a_type=graph, query=mapry.Integer):
        stl_block.add("#include <cstdint>")

    if mapry.needs_type(a_type=graph, query=mapry.String):
        stl_block.add("#include <string>")

    if mapry.needs_type(a_type=graph, query=mapry.Path):
        if cpp.path_as == 'std::filesystem::path':
            stl_block.add("#include <filesystem>")
        elif cpp.path_as == "boost::filesystem::path":
            third_party_block.add("#include <boost/filesystem/path.hpp>")
        else:
            raise NotImplementedError(
                "Unhandled cpp.path_as: {!r}".format(cpp.path_as))

    date_time_types = [mapry.Date, mapry.Time, mapry.Datetime]
    if cpp.datetime_library == 'ctime':
        for query_type in date_time_types:
            if mapry.needs_type(a_type=graph, query=query_type):
                stl_block.add("#include <ctime>")

        if mapry.needs_type(a_type=graph, query=mapry.TimeZone):
            stl_block.add("#include <string>")

    elif cpp.datetime_library == 'date.h':
        if any(mapry.needs_type(a_type=graph, query=query_type)
               for query_type in [mapry.Date, mapry.Time, mapry.Datetime]):
            third_party_block.add("#include <date/date.h>")

        if mapry.needs_type(a_type=graph, query=mapry.Time):
            stl_block.add("#include <chrono>")

        if mapry.needs_type(a_type=graph, query=mapry.TimeZone):
            third_party_block.add("#include <date/tz.h>")

    else:
        raise NotImplementedError(
            "Unhandled cpp.datetime_library: {!r}".format(cpp.datetime_library))

    if mapry.needs_type(a_type=graph, query=mapry.Duration):
        stl_block.add("#include <chrono>")

    if mapry.needs_type(a_type=graph, query=mapry.Array):
        stl_block.add("#include <vector>")

    if mapry.needs_type(a_type=graph, query=mapry.Map):
        stl_block.add("#include <map>")

    if graph.classes:
        stl_block.add("#include <map>")
        stl_block.add("#include <string>")
        stl_block.add("#include <memory>")

    # Check for optional fields
    # yapf: disable
    has_optional = (
            any(prop.optional for prop in graph.properties.values()) or
            any(prop.optional for cls in graph.classes.values()
                for prop in cls.properties.values()) or
            any(prop.optional for embed in graph.embeds.values()
                for prop in embed.properties.values()))
    # yapf: enable

    if has_optional:
        if cpp.optional_as == "boost::optional":
            third_party_block.add("#include <boost/optional.hpp>")
        elif cpp.optional_as == "std::optional":
            stl_block.add("#include <optional>")
        elif cpp.optional_as == "std::experimental::optional":
            third_party_block.add("#include <optional.hpp>")
        else:
            raise NotImplementedError(
                "Unhandled cpp.optional_as: {!r}".format(cpp.optional_as))

    block_strs = []  # type: List[str]

    if len(third_party_block) > 0:
        block_strs.append('\n'.join(sorted(third_party_block)))

    if len(stl_block) > 0:
        block_strs.append('\n'.join(sorted(stl_block)))

    return '\n\n'.join(block_strs)


_FORWARD_DECLARATIONS_TPL = mapry.cpp.jinja2_env.ENV.from_string(
    '''\
struct {{ graph.name|as_composite }};
{# Classes #}
{% if graph.classes %}

{% for cls in graph.classes.values() %}
class {{ cls.name|as_composite }};
{% endfor %}
{% endif %}
{# Embeds #}
{% if graph.embeds %}

{% for embed in graph.embeds.values() %}
struct {{ embed.name|as_composite }};
{% endfor %}
{% endif %}''')


@ensure(lambda result: not result.endswith('\n'))
def _forward_declarations(graph: mapry.Graph) -> str:
    """
    Generate the forward declarations of all the graph-specific types.

    :param graph: definition of the object graph
    :return: generated code
    """
    return _FORWARD_DECLARATIONS_TPL.render(graph=graph).strip()


@ensure(lambda result: result is None or not result.endswith('\n'))
def _default_value(a_type: mapry.Type, cpp: mapry.Cpp) -> Optional[str]:
    """
    Generate the default value for the given type of a property.

    :param a_type: a mapry type of a property.
    :param cpp: C++ settings
    :return:
        generated code representing the default value,
        None if no default value available
    """
    # pylint: disable=too-many-return-statements
    # pylint: disable=too-many-branches
    if isinstance(a_type, mapry.Boolean):
        return "false"

    elif isinstance(a_type, mapry.Integer):
        return "0"

    elif isinstance(a_type, mapry.Float):
        return "0.0"

    elif isinstance(a_type, mapry.String):
        return None

    elif isinstance(a_type, mapry.Path):
        return None

    elif isinstance(a_type, mapry.Date):
        if cpp.datetime_library == 'ctime':
            return "tm{0}"
        elif cpp.datetime_library == 'date.h':
            return None
        else:
            raise NotImplementedError(
                "Unhandled datetime library: {}".format(cpp.datetime_library))

    elif isinstance(a_type, mapry.Time):
        if cpp.datetime_library == 'ctime':
            return "tm{0}"
        elif cpp.datetime_library == 'date.h':
            return None
        else:
            raise NotImplementedError(
                "Unhandled datetime library: {}".format(cpp.datetime_library))

    elif isinstance(a_type, mapry.Datetime):
        if cpp.datetime_library == 'ctime':
            return "tm{0}"
        elif cpp.datetime_library == 'date.h':
            return None
        else:
            raise NotImplementedError(
                "Unhandled datetime library: {}".format(cpp.datetime_library))

    elif isinstance(a_type, mapry.TimeZone):
        if cpp.datetime_library == 'ctime':
            return None
        elif cpp.datetime_library == 'date.h':
            return 'nullptr'
        else:
            raise NotImplementedError(
                "Unhandled datetime library: {}".format(cpp.datetime_library))

    elif isinstance(a_type, mapry.Duration):
        return None

    elif isinstance(a_type, mapry.Array):
        return None

    elif isinstance(a_type, mapry.Map):
        return None

    elif isinstance(a_type, mapry.Class):
        return "nullptr"

    elif isinstance(a_type, mapry.Embed):
        return None

    else:
        raise NotImplementedError(
            "Unhandled C++ default value of a type: {}".format(type(a_type)))


@ensure(lambda result: not result.endswith('\n'))
def _property_fields(composite: mapry.Composite, cpp: mapry.Cpp) -> str:
    """
    Generate the code defining the property fields of a composite type.

    :param composite: type definition
    :param cpp: C++ settings
    :return: generated code
    """
    blocks = []  # type: List[str]

    for prop in composite.properties.values():
        block = []  # type: List[str]
        if prop.description:
            block.append(mapry.cpp.generate.comment(text=prop.description))

        def_val = None  # type: Optional[str]
        if prop.optional:
            non_optional_type = mapry.cpp.generate.type_repr(
                a_type=prop.type, cpp=cpp)
            if cpp.optional_as == "boost::optional":
                prop_type = "boost::optional<{}>".format(non_optional_type)
            elif cpp.optional_as == "std::optional":
                prop_type = "std::optional<{}>".format(non_optional_type)
            elif cpp.optional_as == "std::experimental::optional":
                prop_type = "std::experimental::optional<{}>".format(
                    non_optional_type)
            else:
                raise NotImplementedError(
                    "Unhandled cpp.optional_as: {!r}".format(cpp.optional_as))
        else:
            prop_type = mapry.cpp.generate.type_repr(a_type=prop.type, cpp=cpp)
            def_val = _default_value(a_type=prop.type, cpp=cpp)

        if def_val is not None:
            block.append("{} {} = {};".format(prop_type, prop.name, def_val))
        else:
            block.append("{} {};".format(prop_type, prop.name))

        blocks.append('\n'.join(block))

    return '\n\n'.join(blocks)


_EMBED_DEFINITION_TPL = mapry.cpp.jinja2_env.ENV.from_string(
    '''\
{% if embed.description %}
{{ embed.description|comment }}
{% endif %}
struct {{embed.name|as_composite}} {
    {% if property_fields %}
    {{ property_fields|indent }}
    {% endif %}
};
''')


@ensure(lambda result: not result.endswith('\n'))
def _embed_definition(embed: mapry.Embed, cpp: mapry.Cpp) -> str:
    """
    Generate the code that defines the embeddable structure.

    :param embed: embeddable structure
    :param cpp: C++ settings
    :return: generated code
    """
    return _EMBED_DEFINITION_TPL.render(
        embed=embed, property_fields=_property_fields(composite=embed,
                                                      cpp=cpp)).strip()


_CLASS_DEFINITION_TPL = mapry.cpp.jinja2_env.ENV.from_string(
    '''\
{% if cls.description %}
{{ cls.description|comment }}
{% endif %}
class {{ cls.name|as_composite }} {
public:
    // identifies the instance.
    std::string id;
    {% if property_fields %}

    {{ property_fields|indent }}
    {% endif %}
};
''')


@ensure(lambda result: not result.endswith('\n'))
def _class_definition(cls: mapry.Class, cpp: mapry.Cpp) -> str:
    """
    Generate the code that defines the class.

    :param cls: class
    :param cpp: C++ settings
    :return: generated code
    """
    return _CLASS_DEFINITION_TPL.render(
        cls=cls, property_fields=_property_fields(composite=cls,
                                                  cpp=cpp)).strip()


_GRAPH_DEFINITION_TPL = mapry.cpp.jinja2_env.ENV.from_string(
    '''\
{% if graph.description %}
{{ graph.description|comment }}
{% endif %}
struct {{ graph.name|as_composite }} {
{% if property_fields %}
    {{ property_fields|indent }}
{% endif %}
{% if graph.classes %}
{% if property_fields %}

{% endif %}
{% for cls in graph.classes.values() %}
    {% if loop.index > 1 %}

    {% endif %}
    // registers {{ cls.name|as_composite }} instances.
    std::map<std::string, std::unique_ptr<{{ cls.name|as_composite }}>> {{
        cls.plural|as_field }};
{% endfor %}
{% endif %}
};
''')


@ensure(lambda result: not result.endswith('\n'))
def _graph_definition(graph: mapry.Graph, cpp: mapry.Cpp) -> str:
    """
    Generate the code that defines the object graph.

    :param graph: mapry definition of the object graph
    :param cpp: C++ settings
    :return: generated code
    """
    return _GRAPH_DEFINITION_TPL.render(
        graph=graph, property_fields=_property_fields(composite=graph,
                                                      cpp=cpp)).strip()


@ensure(lambda result: result.endswith('\n'))
def generate(graph: mapry.Graph, cpp: mapry.Cpp) -> str:
    """
    Generate the header file that defines the types of the object graph.

    :param graph: definition of the object graph
    :param cpp: C++ settings
    :return: content of the header file
    """
    blocks = [
        "#pragma once", mapry.cpp.generate.WARNING,
        _includes(graph=graph, cpp=cpp)
    ]

    namespace_parts = cpp.namespace.split('::')
    if namespace_parts:
        # yapf: disable
        namespace_opening = '\n'.join(
            ['namespace {} {{'.format(namespace_part)
             for namespace_part in namespace_parts])
        # yapf: enable
        blocks.append(namespace_opening)

    blocks.append(_forward_declarations(graph=graph))

    for embed in graph.embeds.values():
        blocks.append(_embed_definition(embed=embed, cpp=cpp))

    for cls in graph.classes.values():
        blocks.append(_class_definition(cls=cls, cpp=cpp))

    blocks.append(_graph_definition(graph=graph, cpp=cpp))

    if namespace_parts:
        # yapf: disable
        namespace_closing = '\n'.join(
            ['}}  // namespace {}'.format(namespace_part)
             for namespace_part in reversed(namespace_parts)])
        # yapf: enable
        blocks.append(namespace_closing)

    blocks.append(mapry.cpp.generate.WARNING)

    return mapry.indention.reindent(
        text='\n\n'.join(blocks) + '\n', indention=cpp.indention)
