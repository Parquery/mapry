"""Generate the header for de/serialization from/to Jsoncpp values."""

from typing import List, Sequence, Set, Union  # pylint: disable=unused-import

from icontract import ensure

import mapry
import mapry.cpp.generate
import mapry.cpp.jinja2_env
import mapry.cpp.naming
import mapry.indention


@ensure(lambda result: not result.endswith('\n'))
def _includes(
        graph: mapry.Graph, cpp: mapry.Cpp, types_header_path: str,
        parse_header_path: str) -> str:
    """
    Generate the include directives of the header file.

    :param graph: definition of the object graph
    :param cpp: C++ settings
    :param types_header_path:
        path to the header file that defines the types of the object graph
    :param parse_header_path:
        path to the header file that defines the general parsing structures
    :return: generated code
    """
    # pylint: disable=too-many-branches
    stl_block = set()  # type: Set[str]

    third_party_block = {"#include <json/json.h>  // jsoncpp"}

    # yapf: disable
    first_party_block = {
        '#include "{}"'.format(pth)
        for pth in [types_header_path, parse_header_path]}
    # yapf: enable

    if mapry.needs_type(a_type=graph, query=mapry.String):
        stl_block.add("#include <string>")

    if mapry.needs_type(a_type=graph, query=mapry.Path):
        if cpp.path_as == 'std::filesystem::path':
            stl_block.add("#include <filesystem>")
        elif cpp.path_as == "boost::filesystem::path":
            third_party_block.add("#include <boost/filesystem/path.hpp>")
        else:
            raise NotImplementedError(
                "Unhandled schema.cpp.path_as: {!r}".format(cpp.path_as))

    if graph.classes:
        stl_block.add("#include <map>")
        stl_block.add("#include <string>")

    # Check for optional fields
    has_optional = False
    for prop in graph.properties.values():
        if prop.optional:
            has_optional = True
            break

    if not has_optional:
        for cls in graph.classes.values():
            for prop in cls.properties.values():
                if prop.optional:
                    has_optional = True
                    break

    if not has_optional:
        for embed in graph.embeds.values():
            for prop in embed.properties.values():
                if prop.optional:
                    has_optional = True
                    break

    if has_optional:
        if cpp.optional_as == "boost::optional":
            third_party_block.add("#include <boost/optional.hpp>")
        elif cpp.optional_as == "std::optional":
            stl_block.add("#include <optional>")
        elif cpp.optional_as == "std::experimental::optional":
            third_party_block.add("#include <optional.hpp>")
        else:
            raise NotImplementedError(
                "Unhandled schema.cpp.optional_as: {!r}".format(
                    cpp.optional_as))

    block_strs = [
        '\n'.join(sorted(third_party_block)), '\n'.join(sorted(stl_block)),
        '\n'.join(sorted(first_party_block))
    ]

    assert all(block_str == block_str.strip() for block_str in block_strs), \
        "No empty blocks in include blocks."

    return '\n\n'.join(block_strs)


_PARSE_JSONCPP_TPL = mapry.cpp.jinja2_env.ENV.from_string(
    '''\
/**
 * parses {{graph.name|as_composite}} from a JSON value.
 *
 * @param [in] value to be parsed
 * @param [in] ref reference to the value (e.g., a reference path)
 * @param [out] target parsed {{ graph.name|as_composite }}
 * @param [out] errors encountered during parsing
 */
void {{graph.name|as_variable}}_from(
    const Json::Value& value,
    std::string ref,
    {{ graph.name|as_composite }}* target,
    parse::Errors* errors);
{% if nongraph_composites %}
{% for composite in nongraph_composites %}

/**
 * parses {{ composite.name|as_composite }} from a JSON value.
 *
 * @param [in] value to be parsed
{% for ref_cls in references[composite] %}
 * @param {{
    ref_cls.plural|as_variable }}_registry registry of the {{
        ref_cls.name|as_composite }} instances
{% endfor %}
 * @param ref reference to the value (e.g., a reference path)
 * @param [out] target parsed data
 * @param [out] errors encountered during parsing
 */
void {{ composite.name|as_variable }}_from(
    const Json::Value& value,
{% for ref_cls in references[composite] %}
    const std::map<std::string, std::unique_ptr<{{
        ref_cls.name|as_composite }}>>& {{
            ref_cls.plural|as_variable }}_registry,
{% endfor %}
    std::string ref,
    {{ composite.name|as_composite }}* target,
    parse::Errors* errors);
{% endfor %}
{% endif %}''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_definitions(graph: mapry.Graph) -> str:
    """
    Generate the code that defines the parsing functions of Jsoncpp.

    :param graph: mapry definition of the object graph
    :return: generated code
    """
    nongraph_composites = []  # type: List[Union[mapry.Embed, mapry.Class]]
    nongraph_composites.extend(graph.embeds.values())
    nongraph_composites.extend(graph.classes.values())

    # yapf: disable
    references = {
        composite: mapry.references(a_type=composite)
        for composite in nongraph_composites}
    # yapf: enable

    return _PARSE_JSONCPP_TPL.render(
        graph=graph,
        nongraph_composites=nongraph_composites,
        references=references).rstrip()


_SERIALIZE_DEFINITIONS_TPL = mapry.cpp.jinja2_env.ENV.from_string(
    '''\
{% for composite in composites %}

/**
 * serializes {{ composite.name|as_composite }} to a JSON value.
 *
 * @param {{ composite.name|as_variable }} to be serialized
 * @return JSON value
 */
Json::Value serialize_{{ composite.name|as_variable }}(
    const {{ composite.name|as_composite }}& {{ composite.name|as_variable }});
{% endfor %}''')


@ensure(lambda result: not result.endswith('\n'))
def _serialize_definitions(composites: Sequence[mapry.Composite]) -> str:
    """
    Generate the definitions of functions that serialize the composite object.

    :param composites:
        all composites (graph, classes and embeds) defined in the graph
    :return: generated code
    """
    return _SERIALIZE_DEFINITIONS_TPL.render(composites=composites).rstrip()


@ensure(lambda result: result.endswith('\n'))
def generate(
        graph: mapry.Graph, cpp: mapry.Cpp, types_header_path: str,
        parse_header_path: str) -> str:
    """
    Generate the header file for de/serialization from/to Jsoncpp.

    :param graph: definition of the object graph
    :param cpp: C++ settings
    :param types_header_path:
        path to the header file that defines the types of the object graph
    :param parse_header_path:
        path to the header file that defines the general parsing structures
    :return: content of the header file
    """
    blocks = [
        "#pragma once", mapry.cpp.generate.WARNING,
        _includes(
            graph=graph,
            cpp=cpp,
            types_header_path=types_header_path,
            parse_header_path=parse_header_path)
    ]

    namespace_parts = cpp.namespace.split('::')
    if namespace_parts:
        # yapf: disable
        namespace_opening = '\n'.join(
            ['namespace {} {{'.format(namespace_part)
             for namespace_part in namespace_parts])
        # yapf: enable
        blocks.append(namespace_opening)

    blocks.append('namespace jsoncpp {')
    blocks.append(_parse_definitions(graph=graph))

    composites = []  # type: List[mapry.Composite]
    composites.append(graph)
    composites.extend(graph.classes.values())
    composites.extend(graph.embeds.values())

    blocks.append(_serialize_definitions(composites=composites))
    blocks.append('}  // namespace jsoncpp')

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
