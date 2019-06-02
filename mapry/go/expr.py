"""Interpret Python expressions."""
import re

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
