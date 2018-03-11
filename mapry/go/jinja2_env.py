"""Provide common Jinja2 environment."""
import jinja2

import mapry.go.expr
import mapry.go.generate
import mapry.naming


def _raise(message: str) -> None:
    """Raise an exception in a template."""
    raise Exception(message)


ENV = jinja2.Environment(
    trim_blocks=True, lstrip_blocks=True, loader=jinja2.BaseLoader())
ENV.filters.update({
    'camel_case': mapry.naming.camel_case,
    'ucamel_case': mapry.naming.ucamel_case,
    'comment': mapry.go.generate.comment,
    'escaped_str': mapry.go.generate.escaped_str,
    'ticked_str': mapry.go.generate.ticked_str,
    'json_plural': mapry.naming.json_plural,
    'is_variable': mapry.go.expr.is_variable,
    '_raise': _raise
})
