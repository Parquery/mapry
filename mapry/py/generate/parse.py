"""Generate the code that defines general structures required for parsing."""

from icontract import ensure

import mapry
import mapry.py.generate
import mapry.py.jinja2_env
import mapry.py.naming


@ensure(lambda result: not result.endswith('\n'))
def _imports(py: mapry.Py) -> str:
    """
    Generate the import statements.

    :param py: Python settings
    :return: generated code
    """
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements
    stdlib_block = {'import typing'}
    first_party_block = {'import {}'.format(py.module_name)}

    return '\n\n'.join(sorted(stdlib_block) + sorted(first_party_block))


_DEFINE_ERROR_AND_ERRORS = '''\
class Error:
    """represents an error occurred while parsing."""

    def __init__(self, ref: str, message: str) -> None:
        """
        initializes the error with the given values.

        :param ref: references the cause (e.g., a reference path)
        :param message: describes the error
        """
        self.ref = ref
        self.message = message


class Errors:
    """
    collects errors capped at a certain quantity.

    If the capacity is full, the subsequent surplus errors are ignored.
    """

    def __init__(self, cap: int) -> None:
        """
        initializes the error container with the given cap.

        :param cap: maximum number of contained errors
        """
        self.cap = cap
        self._values = []  # type: typing.List[Error]

    def add(self, ref: str, message: str) -> None:
        """
        adds an error to the container.

        :param ref: references the cause (e.g., a reference path)
        :param message: describes the error
        """
        if len(self._values) < self.cap:
            self._values.append(Error(ref=ref, message=message))

    def full(self) -> bool:
        """gives True when there are exactly ``cap`` errors contained."""
        return len(self._values) == self.cap

    def empty(self) -> bool:
        """gives True when there are no errors contained."""
        return len(self._values) == 0

    def count(self) -> int:
        """returns the number of errors."""
        return len(self._values)

    def values(self) -> typing.Iterable[Error]:
        """gives an iterator over the errors."""
        return iter(self._values)'''

_CLASS_PLACEHOLDER_FUNCTION_TPL = mapry.py.jinja2_env.ENV.from_string(
    '''\
def placeholder_{{ cls.name | as_variable }}(
        id: str) -> {{ module_name }}.{{ cls.name|as_composite }}:
{% set doctext %}
creates a placeholder instance of {{ cls.name|as_composite }}.

Placeholders are necessary so that we can pre-allocate class registries
during parsing. All the attribute of the placeholder are set to None.
Consider a placeholder an empty shell to be filled out during parsing.

:param id: identifier of the instance
:return: empty shell{#
#}{% endset %}{# /set doctext #}
    {{ doctext|as_docstring|indent }}
    {% if not required_properties %}
    return {{ module_name }}.{{ cls.name|as_composite }}(
        id=id)
    {% else %}
    return {{ module_name }}.{{ cls.name|as_composite }}(  # type: ignore
        id=id,
        {% for prop in required_properties %}
        {{ prop.name|as_attribute }}=None{{ ')' if loop.last else ',' }}
        {% endfor %}{# /for prop #}
    {% endif %}{# /if not required_properties #}
''')


@ensure(lambda result: not result.endswith('\n'))
def _class_placeholder_function(cls: mapry.Class, py: mapry.Py) -> str:
    """
    Generate a function that creates placeholders of the given class.

    Consider a placeholder an empty shell to be filled out during parsing.

    :param cls: mapry class definition
    :param py: Python settings
    :return: generated code
    """
    return _CLASS_PLACEHOLDER_FUNCTION_TPL.render(
        cls=cls,
        required_properties=[
            prop for prop in cls.properties.values() if not prop.optional
        ],
        module_name=py.module_name).rstrip()


_EMBED_PLACEHOLDER_FUNCTION_TPL = mapry.py.jinja2_env.ENV.from_string(
    '''\
def placeholder_{{ embed.name | as_variable }}() -> {{
    module_name }}.{{ embed.name|as_composite }}:
{% set doctext %}
creates a placeholder instance of {{ embed.name|as_composite }}.

Placeholders are necessary so that we can pre-allocate class registries
during parsing. All the attribute of the placeholder are set to None.
Consider a placeholder an empty shell to be filled out during parsing.

:return: empty shell{#
#}{% endset %}{# /set doctext #}
    {{ doctext|as_docstring|indent }}
    {% if not required_properties %}
    return {{ module_name }}.{{ embed.name|as_composite }}()
    {% else %}
    return {{ module_name }}.{{ embed.name|as_composite }}(  # type: ignore
        {% for prop in required_properties %}
        {{ prop.name|as_attribute }}=None{{ ')' if loop.last else ',' }}
        {% endfor %}{# /for prop #}
    {% endif %}{# /if not required_properties #}
''')


@ensure(lambda result: not result.endswith('\n'))
def _embed_placeholder_function(embed: mapry.Embed, py: mapry.Py) -> str:
    """
    Generate a function that creates placeholders of the embeddable structure.

    Consider a placeholder an empty shell to be filled out during parsing.

    :param embed: mapry definition of the embeddable structure
    :param py: Python settings
    :return: generated code
    """
    return _EMBED_PLACEHOLDER_FUNCTION_TPL.render(
        embed=embed,
        required_properties=[
            prop for prop in embed.properties.values() if not prop.optional
        ],
        module_name=py.module_name).rstrip()


_GRAPH_PLACEHOLDER_FUNCTION_TPL = mapry.py.jinja2_env.ENV.from_string(
    '''\
def placeholder_{{ graph.name | as_variable }}() -> {{
    module_name }}.{{ graph.name|as_composite }}:
{% set doctext %}
creates a placeholder instance of {{ graph.name|as_composite }}.

Placeholders are necessary so that we can pre-allocate class registries
during parsing. All the attribute of the placeholder are set to None.
Consider a placeholder an empty shell to be filled out during parsing.

:return: empty shell{#
#}{% endset %}{# /set doctext #}
    {{ doctext|as_docstring|indent }}
    {% if not required_properties %}
    return {{ module_name }}.{{ graph.name|as_composite }}()
    {% else %}
    return {{ module_name }}.{{ graph.name|as_composite }}(  # type: ignore
        {% for prop in required_properties %}
        {{ prop.name|as_attribute }}=None{{ ')' if loop.last else ',' }}
        {% endfor %}{# /for prop #}
    {% endif %}{# /if not required_properties #}
''')


@ensure(lambda result: not result.endswith('\n'))
def _graph_placeholder_function(graph: mapry.Graph, py: mapry.Py) -> str:
    """
    Generate a function that creates a placeholder for the object graph.

    Consider a placeholder an empty shell to be filled out during parsing.

    :param graph: mapry definition of the object graph
    :param py: Python settings
    :return: generated code
    """
    return _GRAPH_PLACEHOLDER_FUNCTION_TPL.render(
        graph=graph,
        module_name=py.module_name,
        required_properties=[
            prop for prop in graph.properties.values() if not prop.optional
        ]).rstrip()


@ensure(lambda result: result.endswith('\n'))
def generate(graph: mapry.Graph, py: mapry.Py) -> str:
    """
    Generate the source file to define general structures required for parsing.

    :param graph: mapry definition of the object graph
    :param py: Python settings
    :return: content of the source file
    """
    blocks = [
        mapry.py.generate.WARNING,
        mapry.py.generate.docstring(
            "provides general structures and functions for parsing."),
        _imports(py=py), _DEFINE_ERROR_AND_ERRORS
    ]

    for embed in graph.embeds.values():
        blocks.append(_embed_placeholder_function(embed=embed, py=py))

    for cls in graph.classes.values():
        blocks.append(_class_placeholder_function(cls=cls, py=py))

    blocks.append(_graph_placeholder_function(graph=graph, py=py))

    return '\n\n\n'.join(blocks) + '\n'
