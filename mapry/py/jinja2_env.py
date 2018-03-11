"""Provide common Jinja2 environment."""
import jinja2

import mapry.naming
import mapry.py.expr
import mapry.py.generate
import mapry.py.naming


def _raise(message: str) -> None:
    """Raise an exception in a template."""
    raise Exception(message)


ENV = jinja2.Environment(
    trim_blocks=True, lstrip_blocks=True, loader=jinja2.BaseLoader())
ENV.filters.update({
    'as_attribute': mapry.py.naming.as_attribute,
    'as_variable': mapry.py.naming.as_variable,
    'as_composite': mapry.py.naming.as_composite,
    'comment': mapry.py.generate.comment,
    'as_docstring': mapry.py.generate.docstring,
    'repr': repr,
    'json_plural': mapry.naming.json_plural,
    'is_variable': mapry.py.expr.is_variable,
    '_raise': _raise
})
