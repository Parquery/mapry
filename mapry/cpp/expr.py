"""Interprete C++ expressions."""
import re
from typing import List

from icontract import ensure, require

_VARIABLE_RE = re.compile(r'^[a-zA-Z_][a-zA-Z_0-9]*$')


def is_variable(expr: str) -> bool:
    """
    Return True if the expression is a valid variable name.

    >>> assert is_variable("a")
    >>> assert is_variable("a_1")
    >>> assert is_variable("A")
    >>> assert is_variable("A_1")
    >>> assert not is_variable("1")
    >>> assert not is_variable("a[i]")
    >>> assert not is_variable('ref + "#"')
    """
    return _VARIABLE_RE.match(expr) is not None


@require(lambda exprs: len(exprs) > 0)
@ensure(lambda result: not result.endswith('\n'))
def append_strings(exprs: List[str]) -> str:
    """
    Generate the concatenation of the given C++ expressions.

    The expressions are concatenated *via* ``std::string::append``.

    :param exprs: C++ expressensions representing the individual parts
    :return: generated C++ expression

    >>> print(append_strings(['ref']))
    ref

    >>> print(append_strings(['ref', '"/some_property"']))
    std::string(ref)
        .append("/some_property")

    """
    if len(exprs) == 1:
        return exprs[0]

    parts = ['std::string({})'.format(exprs[0])]
    for ref_part in exprs[1:]:
        # yapf: disable
        parts.append('\n    .append({})'.format(ref_part))

    return ''.join(parts)
