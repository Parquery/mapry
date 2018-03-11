"""Provide common Jinja2 environment."""
import jinja2

import mapry.cpp.expr
import mapry.cpp.generate
import mapry.cpp.naming
import mapry.naming


def _raise(message: str) -> None:
    """Raise an exception in a template."""
    raise Exception(message)


ENV = jinja2.Environment(
    trim_blocks=True, lstrip_blocks=True, loader=jinja2.BaseLoader())

ENV.filters.update({
    'as_field': mapry.cpp.naming.as_field,
    'as_variable': mapry.cpp.naming.as_variable,
    'as_composite': mapry.cpp.naming.as_composite,
    'comment': mapry.cpp.generate.comment,
    'escaped_str': mapry.cpp.generate.escaped_str,
    'json_plural': mapry.naming.json_plural,
    'is_variable': mapry.cpp.expr.is_variable,
    'join_strings': mapry.cpp.expr.append_strings,
    '_raise': _raise
})
