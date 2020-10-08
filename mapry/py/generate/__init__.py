"""Generate the Python code to parse and serialize a mapry object graph."""

import re
from typing import List, Mapping

import icontract
from icontract import ensure, require

import mapry
import mapry.py.naming

WARNING = "# File automatically generated by mapry. DO NOT EDIT OR APPEND!"


def comment(text: str) -> str:
    """
    Comment out the given the text.

    :param text: of the comment
    :return: non-indented comment
    """
    comment_lines = []  # type: List[str]
    for line in text.splitlines():
        if line.strip():
            comment_lines.append('# {}'.format(line))
        else:
            comment_lines.append('#')

    return '\n'.join(comment_lines)


def type_repr(a_type: mapry.Type, py: mapry.Py) -> str:
    """
    Generate the Python type representation of the given mapry type.

    :param a_type: in mapry
    :param py: Python settings
    :return: Python type as a string
    """
    # pylint: disable=too-many-return-statements
    # pylint: disable=too-many-branches
    if isinstance(a_type, mapry.Boolean):
        return "bool"

    elif isinstance(a_type, mapry.Integer):
        return "int"

    elif isinstance(a_type, mapry.Float):
        return "float"

    elif isinstance(a_type, mapry.String):
        return "str"

    elif isinstance(a_type, mapry.Path):
        if py.path_as == "str":
            return "str"

        elif py.path_as == "pathlib.Path":
            return "pathlib.Path"

        else:
            raise NotImplementedError(
                "Unhandled path_as: {}".format(py.path_as))

    elif isinstance(a_type, mapry.Date):
        return 'datetime.date'

    elif isinstance(a_type, mapry.Time):
        return 'datetime.time'

    elif isinstance(a_type, mapry.Datetime):
        return 'datetime.datetime'

    elif isinstance(a_type, mapry.TimeZone):
        if py.timezone_as == 'str':
            return "str"
        elif py.timezone_as == 'pytz.timezone':
            return "datetime.tzinfo"
        else:
            raise NotImplementedError(
                "Unhandled timezone_as: {}".format(py.timezone_as))

    elif isinstance(a_type, mapry.Duration):
        return "datetime.timedelta"

    elif isinstance(a_type, mapry.Array):
        return "typing.List[{}]".format(type_repr(a_type=a_type.values, py=py))

    elif isinstance(a_type, mapry.Map):
        return "typing.MutableMapping[str, {}]".format(
            type_repr(a_type=a_type.values, py=py))

    elif isinstance(a_type, mapry.Class):
        return '{}.{}'.format(
            py.module_name,
            mapry.py.naming.as_composite(identifier=a_type.name))

    elif isinstance(a_type, mapry.Embed):
        return '{}.{}'.format(
            py.module_name,
            mapry.py.naming.as_composite(identifier=a_type.name))

    else:
        raise NotImplementedError(
            "Unhandled Python represenation of a type: {}".format(type(a_type)))


@require(lambda text: text != '')
@ensure(lambda result: not result.endswith('\n'))
@ensure(lambda result: result.startswith('r"""') or result.startswith('"""'))
@ensure(lambda result: result.endswith('"""'))
def docstring(text: str) -> str:
    """
    Translate the text into a docstring Python string literal.

    :param text: text of the docstring
    :return: Python string literal
    """
    has_backslash = '\\' in text
    has_triple_quote = '"""' in text

    is_raw = False
    content = text

    if has_triple_quote:
        is_raw = False
        content = text.replace('\\', '\\\\').replace('"""', '\\"\\"\\"')
    else:
        if has_backslash:
            is_raw = True

    parts = []  # type: List[str]
    if is_raw:
        parts.append('r')

    lines = text.splitlines()
    if len(lines) > 1:
        parts.append('"""\n')
        parts.append(content)
        parts.append('\n"""')
    elif len(lines) == 1:
        parts.append('"""{}"""'.format(content))

    return ''.join(parts)


def order_by_optional(properties: Mapping[str, mapry.Property]
                      ) -> List[mapry.Property]:
    """
    Stable sort properties of a composite by their ``optional`` attribute.

    :param properties: properties of a composite
    :return: list of properties sorted stable by ``optional`` attribute
    """
    return sorted(properties.values(), key=lambda prop: prop.optional)


class AutoID:
    """Keep track of parsing identifiers."""

    def __init__(self) -> None:
        """Initialize with a zero identifier."""
        self._next_id = 0

    @ensure(
        lambda result: re.match(r'^0|[1-9][0-9]*$', result),
        enabled=icontract.SLOW)
    def next_identifier(self) -> str:
        """
        Generate the next identifier.

        :return: the generated identifier
        """
        result = self._next_id
        self._next_id += 1

        return str(result)
