"""Generate the code that defines the types of the object graph."""
from typing import List  # pylint: disable=unused-import

from icontract import ensure

import mapry
import mapry.indention
import mapry.py.expr
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
    stdlib_block = {'import typing'}

    if mapry.needs_type(a_type=graph, query=mapry.Path):
        if py.path_as == 'str':
            pass
        elif py.path_as == "pathlib.Path":
            stdlib_block.add("import pathlib")
        else:
            raise NotImplementedError(
                "Unhandled path_as: {!r}".format(py.path_as))

    if mapry.needs_type(a_type=graph, query=mapry.TimeZone):
        if py.timezone_as == 'str':
            pass

        elif py.timezone_as == 'pytz.timezone':
            stdlib_block.add('import datetime')

        else:
            raise NotImplementedError(
                'Unhandled timezone_as: {}'.format(py.timezone_as))

    # yapf: disable
    if any(mapry.needs_type(a_type=graph, query=query)
           for query in (mapry.Date, mapry.Time, mapry.Datetime,
                         mapry.Duration)):
        # yapf: enable
        stdlib_block.add('import datetime')

    if len(graph.classes) > 0:
        # Needed for the initialization of class registries
        stdlib_block.add('import collections')

    return '\n'.join(sorted(stdlib_block))


@ensure(lambda result: result == result.strip())
def _type_repr(
        a_type: mapry.Type, py: mapry.Py,
        defined_composites: List[mapry.Composite]) -> str:
    """
    Generate the Python type annotation corresponding to the mapry type.

     Only a subset of composites is assumed to be defined in the preceding code.

    The remainder of the composites will be defined in the code following
    this annotation. Hence, every composite which has not been defined thus far
    needs to be written as a string literal, since Python type annotations
    do not support forward declarations.

    :param a_type: mapry type of the property
    :param py: Python settings
    :param defined_composites: composites defined thus far
    :return: generated type annotation
    """
    if isinstance(a_type, (mapry.Embed, mapry.Class, mapry.Graph)):
        if a_type in defined_composites:
            return mapry.py.naming.as_composite(a_type.name)

        # Python does not support forward declarations thus
        # we need to return a string literal representing the type.
        return repr(mapry.py.naming.as_composite(a_type.name))

    elif isinstance(a_type, mapry.Array):
        return 'typing.List[{}]'.format(
            _type_repr(
                a_type=a_type.values,
                py=py,
                defined_composites=defined_composites))

    elif isinstance(a_type, mapry.Map):
        return 'typing.MutableMapping[str, {}]'.format(
            _type_repr(
                a_type=a_type.values,
                py=py,
                defined_composites=defined_composites))

    else:
        return mapry.py.generate.type_repr(a_type=a_type, py=py)


_DEFINE_CLASS_TPL = mapry.py.jinja2_env.ENV.from_string(
    '''\
class {{ cls.name|as_composite }}:
    {% if cls.description %}
    {{ cls.description|as_docstring|indent }}

    {% endif %}{# /if cls.description #}
    def __init__(
            self,
            id: str{{ ',' if properties else ') -> None:' }}
        {% for prop in properties %}
            {% if not prop.optional %}
            {{ prop.name|as_attribute }}: {{ property_type[prop] }}{{
                ') -> None:' if loop.last else ',' }}
            {% else %}
            {{ prop.name|as_attribute }}: typing.Optional[{{
                property_type[prop] }}] = None{{
                    ') -> None:' if loop.last else ',' }}
            {% endif %}{# /if not prop.optional #}
        {% endfor %}{# /for prop #}
    {% set doctext %}
initializes an instance of {{ cls.name|as_composite }} with the given values.

:param id: identifier of the instance{#
#}{% for prop in properties %}
:param {{ prop.name|as_attribute }}: {{ prop.description }}
{% endfor %}{# /for prop #}
{% endset %}{# /set doctext #}
        {{ doctext|as_docstring|indent|indent }}
        self.id = id
        {% for prop in properties %}
        {% if not prop.optional %}
        self.{{ prop.name|as_attribute }} = {{ prop.name|as_attribute }}
        {% else %}
        self.{{ prop.name|as_attribute }} = {{
            prop.name|as_attribute }} if {{
                prop.name|as_attribute }} is not None else None
        {% endif %}{# /if not prop.optional #}
        {% endfor %}{# /for prop #}
''')

_DEFINE_PROPERTYLESS_STRUCTURE_TPL = mapry.py.jinja2_env.ENV.from_string(
    '''\
class {{ composite.name|as_composite }}:
    {% if composite.description %}
    {{ composite.description|as_docstring|indent }}
    {% else %}
    pass
    {% endif %}{# /if composite.description #}
''')

_DEFINE_EMBED_TPL = mapry.py.jinja2_env.ENV.from_string(
    '''\
class {{ embed.name|as_composite }}:
    {% if embed.description %}
    {{ embed.description|as_docstring|indent }}

    {% endif %}{# /if embed.description #}
    def __init__(
            self,
        {% for prop in properties %}
            {% if not prop.optional %}
            {{ prop.name|as_attribute }}: {{ property_type[prop] }}{{
                ') -> None:' if loop.last else ',' }}
            {% else %}
            {{ prop.name|as_attribute }}: typing.Optional[{{
                property_type[prop] }}] = None{{
                    ') -> None:' if loop.last else ',' }}
            {% endif %}{# /if not prop.optional #}
        {% endfor %}{# /for prop #}
    {% set doctext %}
initializes an instance of {{ embed.name|as_composite }} with the given values.

{% for prop in properties %}
:param {{ prop.name|as_attribute }}: {{ prop.description }}
{% endfor %}{# /for prop #}
{% endset %}{# /set doctext #}
        {{ doctext|as_docstring|indent|indent }}
        {% for prop in properties %}
        {% if not prop.optional %}
        self.{{ prop.name|as_attribute }} = {{ prop.name|as_attribute }}
        {% else %}
        self.{{ prop.name|as_attribute }} = {{
            prop.name|as_attribute }} if {{
                prop.name|as_attribute }} is not None else None
        {% endif %}{# /if not prop.optional #}
        {% endfor %}{# /for prop #}
''')


@ensure(lambda result: not result.endswith('\n'))
def _define_class(
        cls: mapry.Class, definition_order: List[mapry.Composite],
        py: mapry.Py) -> str:
    """
    Generate the code that defines the given class.

    :param cls: mapry definition of the class
    :param definition_order: order of the class definitions in Python code
    :param py: Python settings
    :return: generated code
    """
    properties = mapry.py.generate.order_by_optional(cls.properties)

    composite_i = definition_order.index(cls)
    assert composite_i != -1, \
        ('Expected to find the composite {} (named {!r}) '
         'in the definition order').format(cls, cls.name)

    defined_composites = definition_order[:composite_i]

    # yapf: disable
    property_type = {
        prop: _type_repr(
            a_type=prop.type, py=py, defined_composites=defined_composites)
        for prop in properties
    }
    # yapf: enable

    return _DEFINE_CLASS_TPL.render(
        cls=cls, properties=properties, property_type=property_type).rstrip()


@ensure(lambda result: not result.endswith('\n'))
def _define_embed(
        embed: mapry.Embed, definition_order: List[mapry.Composite],
        py: mapry.Py) -> str:
    """
    Generate the code that defines the given embeddable structure.

    :param embed: mapry definition of the embeddable structure
    :param definition_order: order of the class definitions in Python code
    :param py: Python settings
    :return: generated code
    """
    if len(embed.properties) == 0:
        return _DEFINE_PROPERTYLESS_STRUCTURE_TPL.render(
            composite=embed).rstrip()

    properties = mapry.py.generate.order_by_optional(embed.properties)

    composite_i = definition_order.index(embed)
    assert composite_i != -1, \
        ('Expected to find the composite {} (named {!r}) '
         'in the definition order').format(embed, embed.name)

    defined_composites = definition_order[:composite_i]

    # yapf: disable
    property_type = {
        prop: _type_repr(
            a_type=prop.type, py=py, defined_composites=defined_composites)
        for prop in properties
    }
    # yapf: enable

    return _DEFINE_EMBED_TPL.render(
        embed=embed, properties=properties,
        property_type=property_type).rstrip()


_DEFINE_GRAPH_TPL = mapry.py.jinja2_env.ENV.from_string(
    r'''class {{ graph.name|as_composite }}:
    {% if graph.description %}
    {{ graph.description|as_docstring|indent }}

    {% endif %}{# /if graph.description #}
    def __init__(
            self,
            {% for arg in arguments %}
            {{ arg }}{{ ') -> None:' if loop.last else ',' }}
            {% endfor %}{# /for prop #}
    {% set doctext %}
initializes an instance of {{ graph.name|as_composite }} with the given values.

{% if graph.classes %}
The class registries are initialized with empty ordered dictionaries.
{% endif %}
{% for prop in properties %}
:param {{ prop.name|as_attribute }}: {{ prop.description }}
{% endfor %}{# /for prop #}
{% for cls in graph.classes.values() %}
:param {{ cls.plural|as_attribute }}:
    registry of instances of {{ cls.name|as_composite }};
    if not specified, it is initialized as a ``collections.OrderedDict``.
{% endfor %}{# /for cls #}
{% endset %}{# /set doctext #}
        {{ doctext|as_docstring|indent|indent }}
        {% set newliner = joiner('XXX') %}
        {% for prop in properties %}
        {% set _ = newliner() %}
        {% if not prop.optional %}
        self.{{ prop.name|as_attribute }} = {{ prop.name|as_attribute }}
        {% else %}
        self.{{ prop.name|as_attribute }} = {{
            prop.name|as_attribute }} if {{
                prop.name|as_attribute }} is not None else None
        {% endif %}{# /if not prop.optional #}
        {% endfor %}{# /for prop #}
        {% for cls in graph.classes.values() %}
        {% if newliner() %}{{ '\n' }}{% endif %}
        if {{ cls.plural|as_attribute }} is not None:
            self.{{ cls.plural|as_attribute }} = {{ cls.plural|as_attribute }}
        else:
            self.{{ cls.plural|as_attribute }} = collections.OrderedDict()
        {% endfor %}{# /for cls in graph.classes.values() #}
''')


@ensure(lambda result: not result.endswith('\n'))
def _define_graph(
        graph: mapry.Graph, definition_order: List[mapry.Composite],
        py: mapry.Py) -> str:
    """
    Generate the code that defines the object graph.

    :param graph: mapry definition of the object graph
    :param definition_order: order of the class definitions in Python code
    :param py: Python settings
    :return: generated code
    """
    if len(graph.properties) == 0 and len(graph.classes) == 0:
        return _DEFINE_PROPERTYLESS_STRUCTURE_TPL.render(
            composite=graph).rstrip()

    composite_i = definition_order.index(graph)
    assert composite_i != -1, \
        ('Expected to find the graph {} (named {!r}) '
         'in the definition order').format(graph, graph.name)

    defined_composites = definition_order[:composite_i]

    properties = mapry.py.generate.order_by_optional(
        properties=graph.properties)

    ##
    # Define arguments of the constructor.
    # This is too complex to define in a jinja2 template, so pre-render in code.
    ##

    arguments = []  # type: List[str]
    for prop in properties:
        argname = mapry.py.naming.as_attribute(identifier=prop.name)
        type_annotation = _type_repr(
            a_type=prop.type, py=py, defined_composites=defined_composites)

        if not prop.optional:
            arguments.append("{}: {}".format(argname, type_annotation))
        else:
            arguments.append(
                "{}: typing.Optional[{}] = None".format(
                    argname, type_annotation))

    for cls in graph.classes.values():
        argname = mapry.py.naming.as_attribute(identifier=cls.plural)
        type_annotation = _type_repr(
            a_type=cls, py=py, defined_composites=defined_composites)

        arguments.append(
            "{}: typing.Optional[typing.MutableMapping[str, {}]] = None".format(
                argname, type_annotation))

    ##
    # Render the template
    ##

    return _DEFINE_GRAPH_TPL.render(
        graph=graph, arguments=arguments, properties=properties).rstrip()


@ensure(lambda result: result.endswith('\n'))
def generate(graph: mapry.Graph, py: mapry.Py) -> str:
    """
    Generate the source file that defines the types of the object graph.

    :param graph: definition of the object graph
    :param py: Python settings
    :return: content of the source file
    """
    blocks = [mapry.py.generate.WARNING]

    if graph.description:
        blocks.append(mapry.py.generate.docstring(graph.description))

    blocks.append(_imports(graph=graph, py=py))

    definition_order = []  # type: List[mapry.Composite]
    definition_order.extend(graph.classes.values())
    definition_order.extend(graph.embeds.values())
    definition_order.append(graph)

    for composite in definition_order:
        if isinstance(composite, mapry.Class):
            blocks.append(
                _define_class(
                    cls=composite, definition_order=definition_order, py=py))

        elif isinstance(composite, mapry.Embed):
            blocks.append(
                _define_embed(
                    embed=composite, definition_order=definition_order, py=py))

        elif isinstance(composite, mapry.Graph):
            blocks.append(
                _define_graph(
                    graph=graph, definition_order=definition_order, py=py))

        else:
            raise NotImplementedError(
                "Unhandled composite: {}".format(composite))

    blocks.append(mapry.py.generate.WARNING)

    return mapry.indention.reindent(
        text='\n\n\n'.join(blocks) + '\n', indention=py.indention)
