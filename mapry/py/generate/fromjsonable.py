"""Generate the code that parses the object graph from a JSONable structure."""
import textwrap
from typing import (  # pylint: disable=unused-import
    Dict, List, Mapping, MutableMapping, Set, Union)

from icontract import ensure

import mapry
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

    third_party_block = set()  # type: Set[str]

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
            third_party_block.update(
                ('import pytz', 'import pytz.exceptions  # type: ignore'))

        else:
            raise NotImplementedError(
                'Unhandled timezone_as: {}'.format(py.timezone_as))

    # yapf: disable
    if any(mapry.needs_type(a_type=graph, query=query)
           for query in
           (mapry.Date, mapry.Time, mapry.Datetime, mapry.Duration)):
        # yapf: enable
        stdlib_block.add('import datetime')

    if mapry.needs_type(a_type=graph, query=mapry.Map):
        stdlib_block.add("import collections")

    if len(graph.classes) > 0:
        stdlib_block.add(
            'import collections'
        )  # needed for the initialization of class registries

    ##
    # Needs regex?
    ##

    import_re = False
    for a_type, _ in mapry.iterate_over_types(graph=graph):
        if isinstance(a_type, (mapry.String, mapry.Path)) and a_type.pattern:
            import_re = True
            break

        if isinstance(a_type, mapry.Duration):
            import_re = True
            break

    for cls in graph.classes.values():
        if cls.id_pattern is not None:
            import_re = True
            break

    if import_re:
        stdlib_block.add("import re")

    ##
    # First party
    ##

    first_party_block = {
        'import {}'.format(py.module_name),
        'import {}.parse'.format(py.module_name)
    }

    block_strs = []  # type: List[str]
    if len(stdlib_block) > 0:
        block_strs.append('\n'.join(sorted(stdlib_block)))

    if len(third_party_block) > 0:
        block_strs.append('\n'.join(sorted(third_party_block)))

    if len(first_party_block) > 0:
        block_strs.append('\n'.join(sorted(first_party_block)))

    return '\n\n'.join(block_strs)


@ensure(lambda result: not result.endswith('\n'))
def _duration_from_string() -> str:
    """
    Generate the code for parsing durations from strings.

    :return: generated code
    """
    return textwrap.dedent(
        '''\
    _DURATION_RE = re.compile(
        r'^(?P<sign>\\+|-)?P'
        r'((?P<years>(0|[1-9][0-9]*)(\.[0-9]+)?)Y)?'
        r'((?P<months>(0|[1-9][0-9]*)(\.[0-9]+)?)M)?'
        r'((?P<weeks>(0|[1-9][0-9]*)(\.[0-9]+)?)W)?'
        r'((?P<days>(0|[1-9][0-9]*)(\.[0-9]+)?)D)?'
        r'(T'
        r'((?P<hours>(0|[1-9][0-9]*)(\.[0-9]+)?)H)?'
        r'((?P<minutes>(0|[1-9][0-9]*)(\.[0-9]+)?)M)?'
        r'(((?P<seconds>0|[1-9][0-9]*)(\.(?P<fraction>[0-9]+))?)S)?'
        r')?$')


    def _duration_from_string(text: str) -> datetime.timedelta:
        """
        parses the duration from the string in ISO 8601 format.

        Following C++ chrono library, the following units are counted as:

        * years as 365.2425 days (the average length of a Gregorian year),
        * months as 30.436875 days (exactly 1/12 of years) and
        * weeks as 7 days.

        :param text: string to be parsed
        :return: duration
        :raise:
            ValueError if the string could not be parsed,
            ValueError if the fraction precision is higher than microseconds
            OverflowError if the duration does not fit into datetime.timedelta


        >>> _duration_from_string('P10Y')
        datetime.timedelta(3652, 36720)

        >>> _duration_from_string('P1M')
        datetime.timedelta(30, 37746)

        >>> _duration_from_string('P1W')
        datetime.timedelta(7)

        >>> _duration_from_string('P1D')
        datetime.timedelta(1)

        >>> _duration_from_string('PT1H1M1S')
        datetime.timedelta(0, 3661)

        >>> _duration_from_string('PT1H1M1.1S')
        datetime.timedelta(0, 3661, 100000)

        >>> _duration_from_string('PT')
        datetime.timedelta(0)

        >>> _duration_from_string('P1.1Y1.1M1.1W1.1DT1.1H1.1M1.1S')
        datetime.timedelta(444, 8114, 900000)

        >>> _duration_from_string('PT0.000001S')
        datetime.timedelta(0, 0, 1)

        >>> _duration_from_string('PT1.000S')
        datetime.timedelta(0, 1)

        >>> _duration_from_string('-P1D')
        datetime.timedelta(-1)

        """
        match = _DURATION_RE.match(text)

        if not match:
            raise ValueError(
                'Failed to match the duration: {!r}'.format(
                    text))

        sign_grp = match.group('sign')
        if not sign_grp or sign_grp == '+':
            sign = 1
        else:
            sign = -1

        years_grp = match.group('years')
        years = float(years_grp) if years_grp else 0.0

        months_grp = match.group('months')
        months = float(months_grp) if months_grp else 0.0

        weeks_grp = match.group('weeks')
        weeks = float(weeks_grp) if weeks_grp else 0.0

        days_grp = match.group('days')
        days = float(days_grp) if days_grp else 0.0

        hours_grp = match.group('hours')
        hours = float(hours_grp) if hours_grp else 0.0

        minutes_grp = match.group('minutes')
        minutes = float(minutes_grp) if minutes_grp else 0.0

        seconds_grp = match.group('seconds')
        seconds = int(seconds_grp) if seconds_grp else 0

        fraction_grp = match.group('fraction')
        if not fraction_grp:
            microseconds = 0

        elif len(fraction_grp) > 6:
            raise ValueError(
                ('Precision only up to microseconds supported, '
                 'but got: {}').format(text))

        else:
            stripped = fraction_grp.lstrip('0')
            if stripped:
                count = int(stripped)
                order = 6 - len(fraction_grp)
                microseconds = count * (10 ** order)
            else:
                microseconds = 0
        try:
            return sign * datetime.timedelta(
                days=years * 365.2425 + months * 30.436875 + weeks * 7 + days,
                seconds=seconds,
                minutes=minutes,
                hours=hours,
                microseconds=microseconds)

        except OverflowError as err:
            raise OverflowError(
                'Creating a timedelta overflowed from: {!r}'.format(
                    text)) from err''')


_PARSE_BOOLEAN_TPL = mapry.py.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{% if value_expr|is_variable %}
{# short-circuit value as value expression if it is a variable so that
we don't end up with an unnecessary variable1 = variable2 statement.#}
{% set value = value_expr %}
{% else %}
{% set value = "value_%s"|format(uid) %}
value_{{ uid }} = {{ value_expr }}
{% endif %}
if not isinstance({{ value }}, bool):
    errors.add(
        '/'.join((
            {{ ref_parts|join(', ') }})),
        "Expected a bool, but got: {}".format(
            type({{ value }})))
else:
    {{ target_expr }} = {{ value }}''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_boolean(
        value_expr: str, target_expr: str, ref_parts: List[str],
        auto_id: mapry.py.generate.AutoID) -> str:
    """
    Generate the code to parse a boolean.

    The code parses the JSONable ``value_expr`` into the ``target_expr``.

    :param value_expr: Python expression of the JSONable value
    :param target_expr: Python expression of where to store the parsed value
    :param ref_parts: Python expression of reference path segments to the value
    :param auto_id: generator of unique identifiers
    :return: Python code
    """
    uid = auto_id.next_identifier()

    return _PARSE_BOOLEAN_TPL.render(
        uid=uid,
        value_expr=value_expr,
        ref_parts=ref_parts,
        target_expr=target_expr)


_PARSE_INTEGER_TPL = mapry.py.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{% if value_expr|is_variable %}
{# Short-circuit value as value expression if it is a variable so that
we don't end up with an unnecessary variable1 = variable2 statement.#}
{% set value = value_expr %}
{% else %}
{% set value = "value_%s"|format(uid) %}
value_{{ uid }} = {{ value_expr }}
{% endif %}{# /value_expr|is_variable #}
if not isinstance({{ value }}, int):
    errors.add(
        '/'.join((
            {{ ref_parts|join(', ') }})),
        "Expected an integer, but got: {}".format(
            type({{ value }})))
else:
    {% if a_type.minimum is none and a_type.maximum is none %}
    {{ target_expr }} = {{ value }}
    {% else %}
    {% set got_cond_before = False %}
    {% if a_type.minimum is not none %}
    {% set op = ">" if a_type.exclusive_minimum else ">="  %}
    if not ({{ value }} {{ op }} {{ a_type.minimum }}):
        errors.add(
            '/'.join((
                {{ ref_parts|join(', ') }})),
            {{ "Expected %s %d, but got: {}"|
                format(op, a_type.minimum)|repr }}.format(
                {{ value }}))
    {% set got_cond_before = True %}
    {% endif %}{# /if a_type.minimum is not none #}
    {% if a_type.maximum is not none %}
    {% set op = "<" if a_type.exclusive_maximum else "<=" %}
    {{
        'elif' if get_cond_before else 'if'
    }} not ({{ value }} {{ op }} {{ a_type.maximum }}):
        errors.add(
            '/'.join((
                {{ ref_parts|join(', ') }})),
            {{ "Expected %s %d, but got: {}"|
                format(op, a_type.maximum)|repr }}.format(
                {{ value }}))
    {% set got_cond_before = True %}
    {% endif %}{# /if a_type.maximum is not none #}
    else:
        {{ target_expr }} = {{ value }}
    {% endif %}{# /if a_type.minimum is none and a_type.maximum is none #}
''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_integer(
        value_expr: str, target_expr: str, ref_parts: List[str],
        a_type: mapry.Integer, auto_id: mapry.py.generate.AutoID) -> str:
    """
    Generate the code to parse an integer.

    The code parses the JSONable ``value_expr`` into the ``target_expr``.

    :param value_expr: Python expression of the JSONable value
    :param target_expr: Python expression of where to store the parsed value
    :param ref_parts: Python expression of reference path segments to the value
    :param a_type: mapry definition of the value type
    :param auto_id: generator of unique identifiers
    :return: generated code
    """
    uid = auto_id.next_identifier()

    return _PARSE_INTEGER_TPL.render(
        uid=uid,
        value_expr=value_expr,
        ref_parts=ref_parts,
        target_expr=target_expr,
        a_type=a_type).rstrip("\n")


_PARSE_FLOAT_TPL = mapry.py.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{% if value_expr|is_variable %}
{# Short-circuit value as value expression if it is a variable so that
we don't end up with an unnecessary variable1 = variable2 statement.#}
{% set value = value_expr %}
{% else %}
{% set value = "value_%s"|format(uid) %}
value_{{ uid }} = {{ value_expr }}
{% endif %}
if not isinstance({{ value }}, (int, float)):
    errors.add(
        '/'.join((
            {{ ref_parts|join(', ') }})),
        'Expected a number, but got: {}'.format(
            type({{ value }})))
else:
    {% if a_type.minimum is none and a_type.maximum is none %}
    {{ target_expr }} = float({{ value }})
    {% else %}
    {% set got_cond_before = False %}
    {% if a_type.minimum is not none %}
    {% set op = ">" if a_type.exclusive_minimum else ">="  %}
    if not ({{ value }} {{ op }} {{ a_type.minimum }}):
        errors.add(
            '/'.join((
                {{ ref_parts|join(', ') }})),
            {{ "Expected %s %d, but got: {}"|
                format(op, a_type.minimum)|repr }}.format(
                {{ value }}))
    {% set got_cond_before = True %}
    {% endif %}{# /if a_type.minimum is not none #}
    {% if a_type.maximum is not none %}
    {% set op = "<" if a_type.exclusive_maximum else "<=" %}
    {{ 'elif' if get_cond_before else 'if'
        }} not ({{ value }} {{ op }} {{ a_type.maximum }}):
        errors.add(
            '/'.join((
                {{ ref_parts|join(', ') }})),
            {{ "Expected %s %d, but got: {}"|
                format(op, a_type.maximum)|repr }}.format(
                {{ value }}))
    {% set got_cond_before = True %}
    {% endif %}{# /if a_type.maximum is not none #}
    else:
        {{ target_expr }} = float({{ value }})
    {% endif %}{# /if a_type.minimum is none and a_type.maximum is none #}''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_float(
        value_expr: str, target_expr: str, ref_parts: List[str],
        a_type: mapry.Float, auto_id: mapry.py.generate.AutoID) -> str:
    """
    Generate the code to parse a float.

    The code parses the JSONable ``value_expr`` into the ``target_expr``.

    :param value_expr: Python expression of the JSONable value
    :param target_expr: Python expression of where to store the parsed value
    :param ref_parts: Python expression of reference path segments to the value
    :param a_type: mapry definition of the value type
    :param auto_id: generator of unique identifiers
    :return: generated code
    """
    uid = auto_id.next_identifier()

    return _PARSE_FLOAT_TPL.render(
        uid=uid,
        value_expr=value_expr,
        ref_parts=ref_parts,
        target_expr=target_expr,
        a_type=a_type).rstrip("\n")


_PARSE_STRING_TPL = mapry.py.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{% if value_expr|is_variable %}
{# Short-circuit value as value expression if it is a variable so that
we don't end up with an unnecessary variable1 = variable2 statement.#}
{% set value = value_expr %}
{% else %}
{% set value = "value_%s"|format(uid) %}
value_{{ uid }} = {{ value_expr }}
{% endif %}
if not isinstance({{ value }}, str):
    errors.add(
        '/'.join((
            {{ ref_parts|join(', ') }})),
        "Expected a string, but got: {}".format(
            type({{ value }})))
else:
    {% if a_type.pattern is none %}
    {{ target_expr }} = {{ value }}
    {% else %}
    if not re.match(
            r'{{ a_type.pattern.pattern }}',
            {{ value }}):
        errors.add(
            '/'.join((
                {{ ref_parts|join(', ') }})),
            {{ "Expected to match %s, but got: {}"|
                format(a_type.pattern.pattern)|repr }}.format(
                {{ value }}))
    else:
        {{ target_expr }} = {{ value }}
    {% endif %}{# /if a_type.pattern is none #}
''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_string(
        value_expr: str, target_expr: str, ref_parts: List[str],
        a_type: mapry.String, auto_id: mapry.py.generate.AutoID) -> str:
    """
    Generate the code to parse a string.

    The code parses the JSONable ``value_expr`` into the ``target_expr``.

    :param value_expr: Python expression of the JSONable value
    :param target_expr: Python expression of where to store the parsed value
    :param ref_parts: Python expression of reference path segments to the value
    :param a_type: mapry definition of the value type
    :param auto_id: generator of unique identifiers
    :return: generated code
    """
    uid = auto_id.next_identifier()

    return _PARSE_STRING_TPL.render(
        uid=uid,
        value_expr=value_expr,
        ref_parts=ref_parts,
        target_expr=target_expr,
        a_type=a_type).rstrip("\n")


_PARSE_PATH_TPL = mapry.py.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{% if value_expr|is_variable %}
{# Short-circuit value as value expression if it is a variable so that
we don't end up with an unnecessary variable1 = variable2 statement.#}
{% set value = value_expr %}
{% else %}
{% set value = "value_%s"|format(uid) %}
value_{{ uid }} = {{ value_expr }}
{% endif %}
if not isinstance({{ value }}, str):
    errors.add(
        '/'.join((
            {{ ref_parts|join(', ') }})),
        "Expected a string, but got: {}".format(
            type({{ value }})))
else:
    {% set set_target %}
{% if py.path_as == "str" %}
{{ target_expr }} = {{ value }}
{% elif py.path_as == "pathlib.Path" %}
{{ target_expr }} = pathlib.Path(
    {{ value }})
{% else %}
{{ _raise("Unhandled path_as: %s"|format(py.path_as)) }}
{% endif %}{# /if py.path_as #}
    {% endset %}{#

    #}
    {% if a_type.pattern is none %}
    {{ set_target|indent }}
    {% else %}
    if not re.match(
            r'{{ a_type.pattern.pattern }}',
            {{ value }}):
        errors.add(
            '/'.join((
                {{ ref_parts|join(', ') }})),
            {{ "Expected to match %s, but got: {}"|
                format(a_type.pattern.pattern)|repr }}.format(
                {{ value }}))
    else:
        {{ set_target|indent|indent }}
    {% endif %}{# /if a_type.pattern is none #}
''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_path(
        value_expr: str, target_expr: str, ref_parts: List[str],
        a_type: mapry.Path, auto_id: mapry.py.generate.AutoID,
        py: mapry.Py) -> str:
    """
    Generate the code to parse a path.

    The code parses the JSONable ``value_expr`` into the ``target_expr``.

    :param value_expr: Python expression of the JSONable value
    :param target_expr: Python expression of where to store the parsed value
    :param ref_parts: Python expression of reference path segments to the value
    :param a_type: mapry definition of the value type
    :param auto_id: generator of unique identifiers
    :param py: Python settings
    :return: generated code
    """
    uid = auto_id.next_identifier()

    return _PARSE_PATH_TPL.render(
        uid=uid,
        value_expr=value_expr,
        ref_parts=ref_parts,
        target_expr=target_expr,
        a_type=a_type,
        py=py).rstrip("\n")


_PARSE_DATE_TPL = mapry.py.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{% if value_expr|is_variable %}
{# Short-circuit value as value expression if it is a variable so that
we don't end up with an unnecessary variable1 = variable2 statement.#}
{% set value = value_expr %}
{% else %}
{% set value = "value_%s"|format(uid) %}
value_{{ uid }} = {{ value_expr }}
{% endif %}
if not isinstance({{ value }}, str):
    errors.add(
        '/'.join((
            {{ ref_parts|join(', ') }})),
        "Expected a string, but got: {}".format(
            type({{ value }})))
else:
    try:
        {{ target_expr }} = datetime.datetime.strptime(
            {{ value }},
            {{ a_type.format|repr }}
        ).date()
    except ValueError:
        errors.add(
            '/'.join((
                {{ ref_parts|join(', ') }})),
            {{ "Expected to strptime %s, but got: {}"|
                format(a_type.format)|repr }}.format(
                {{ value }}))
''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_date(
        value_expr: str, target_expr: str, ref_parts: List[str],
        a_type: mapry.Date, auto_id: mapry.py.generate.AutoID) -> str:
    """
    Generate the code to parse a date.

    The code parses the JSONable ``value_expr`` into the ``target_expr``.

    :param value_expr: Python expression of the JSONable value
    :param target_expr: Python expression of where to store the parsed value
    :param ref_parts: Python expression of reference path segments to the value
    :param a_type: mapry definition of the value type
    :param auto_id: generator of unique identifiers
    :return: generated code
    """
    uid = auto_id.next_identifier()

    return _PARSE_DATE_TPL.render(
        uid=uid,
        value_expr=value_expr,
        ref_parts=ref_parts,
        target_expr=target_expr,
        a_type=a_type).rstrip("\n")


_PARSE_DATE_TIME_TPL = mapry.py.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{% if value_expr|is_variable %}
{# Short-circuit value as value expression if it is a variable so that
we don't end up with an unnecessary variable1 = variable2 statement.#}
{% set value = value_expr %}
{% else %}
{% set value = "value_%s"|format(uid) %}
value_{{ uid }} = {{ value_expr }}
{% endif %}
if not isinstance({{ value }}, str):
    errors.add(
        '/'.join((
            {{ ref_parts|join(', ') }})),
        "Expected a string, but got: {}".format(
            type({{ value }})))
else:
    try:
        {{ target_expr }} = datetime.datetime.strptime(
            {{ value }},
            {{ a_type.format|repr }})
    except ValueError:
        errors.add(
            '/'.join((
                {{ ref_parts|join(', ') }})),
            {{ "Expected to strptime %s, but got: {}"|
                format(a_type.format)|repr }}.format(
                {{ value }}))
''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_date_time(
        value_expr: str, target_expr: str, ref_parts: List[str],
        a_type: mapry.Datetime, auto_id: mapry.py.generate.AutoID) -> str:
    """
    Generate the code to parse a datetime.

    The code parses the JSONable ``value_expr`` into the ``target_expr``.

    :param value_expr: Python expression of the JSONable value
    :param target_expr: Python expression of where to store the parsed value
    :param ref_parts: Python expression of reference path segments to the value
    :param a_type: mapry definition of the value type
    :param auto_id: generator of unique identifiers
    :return: generated code
    """
    uid = auto_id.next_identifier()

    return _PARSE_DATE_TIME_TPL.render(
        uid=uid,
        value_expr=value_expr,
        ref_parts=ref_parts,
        target_expr=target_expr,
        a_type=a_type).rstrip("\n")


_PARSE_TIME_TPL = mapry.py.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{% if value_expr|is_variable %}
{# Short-circuit value as value expression if it is a variable so that
we don't end up with an unnecessary variable1 = variable2 statement.#}
{% set value = value_expr %}
{% else %}
{% set value = "value_%s"|format(uid) %}
value_{{ uid }} = {{ value_expr }}
{% endif %}
if not isinstance({{ value }}, str):
    errors.add(
        '/'.join((
            {{ ref_parts|join(', ') }})),
        "Expected a string, but got: {}".format(
            type({{ value }})))
else:
    try:
        {{ target_expr }} = datetime.datetime.strptime(
            {{ value }},
            {{ a_type.format|repr }}
        ).time()
    except ValueError:
        errors.add(
            '/'.join((
                {{ ref_parts|join(', ') }})),
            {{ "Expected to strptime %s, but got: {}"|
                format(a_type.format)|repr }}.format(
                {{ value }}))
''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_time(
        value_expr: str, target_expr: str, ref_parts: List[str],
        a_type: mapry.Time, auto_id: mapry.py.generate.AutoID) -> str:
    """
    Generate the code to parse a time.

    The code parses the JSONable ``value_expr`` into the ``target_expr``.

    :param value_expr: Python expression of the JSONable value
    :param target_expr: Python expression of where to store the parsed value
    :param ref_parts: Python expression of reference path segments to the value
    :param a_type: mapry definition of the value type
    :param auto_id: generator of unique identifiers
    :return: generated code
    """
    uid = auto_id.next_identifier()

    return _PARSE_TIME_TPL.render(
        uid=uid,
        value_expr=value_expr,
        ref_parts=ref_parts,
        target_expr=target_expr,
        a_type=a_type).rstrip("\n")


_PARSE_TIME_ZONE_AS_STR_TPL = mapry.py.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{% if value_expr|is_variable %}
{# Short-circuit value as value expression if it is a variable so that
we don't end up with an unnecessary variable1 = variable2 statement.#}
{% set value = value_expr %}
{% else %}
{% set value = "value_%s"|format(uid) %}
value_{{ uid }} = {{ value_expr }}
{% endif %}
if not isinstance({{ value }}, str):
    errors.add(
        '/'.join((
            {{ ref_parts|join(', ') }})),
        "Expected a string, but got: {}".format(
            type({{ value }})))
else:
    {{ target_expr }} = {{ value }}''')

_PARSE_TIME_ZONE_PYTZ_TPL = mapry.py.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{% if value_expr|is_variable %}
{# Short-circuit value as value expression if it is a variable so that
we don't end up with an unnecessary variable1 = variable2 statement.#}
{% set value = value_expr %}
{% else %}
{% set value = "value_%s"|format(uid) %}
value_{{ uid }} = {{ value_expr }}
{% endif %}
if not isinstance({{ value }}, str):
    errors.add(
        '/'.join((
            {{ ref_parts|join(', ') }})),
        "Expected a string, but got: {}".format(
            type({{ value }})))
else:
    try:
        {{ target_expr }} = pytz.timezone(
            {{ value }})
    except pytz.exceptions.UnknownTimeZoneError:
        errors.add(
            '/'.join((
                {{ ref_parts|join(', ') }})),
            "Expected a valid IANA time zone, but got: {}".format(
                {{ value }}))
''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_time_zone(
        value_expr: str, target_expr: str, ref_parts: List[str],
        a_type: mapry.TimeZone, auto_id: mapry.py.generate.AutoID,
        py: mapry.Py) -> str:
    """
    Generate the code to parse a time zone.

    The code parses the JSONable ``value_expr`` into the ``target_expr``.

    :param value_expr: Python expression of the JSONable value
    :param target_expr: Python expression of where to store the parsed value
    :param ref_parts: Python expression of reference path segments to the value
    :param a_type: mapry definition of the value type
    :param auto_id: generator of unique identifiers
    :param py: Python settings
    :return: generated code
    """
    uid = auto_id.next_identifier()

    if py.timezone_as == 'str':
        return _PARSE_TIME_ZONE_AS_STR_TPL.render(
            uid=uid,
            value_expr=value_expr,
            ref_parts=ref_parts,
            target_expr=target_expr,
            a_type=a_type).rstrip("\n")

    if py.timezone_as == 'pytz.timezone':
        return _PARSE_TIME_ZONE_PYTZ_TPL.render(
            uid=uid,
            value_expr=value_expr,
            ref_parts=ref_parts,
            target_expr=target_expr,
            a_type=a_type).rstrip("\n")

    raise NotImplementedError(
        "Unhandled timezone_as: {}".format(py.timezone_as))


_PARSE_DURATION_TPL = mapry.py.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{% if value_expr|is_variable %}
{# Short-circuit value as value expression if it is a variable so that
we don't end up with an unnecessary variable1 = variable2 statement.#}
{% set value = value_expr %}
{% else %}
{% set value = "value_%s"|format(uid) %}
value_{{ uid }} = {{ value_expr }}
{% endif %}
if not isinstance({{ value }}, str):
    errors.add(
        '/'.join((
            {{ ref_parts|join(', ') }})),
        "Expected a string, but got: {}".format(
            type({{ value }})))
else:
    try:
        {{ target_expr }} = _duration_from_string(
            {{ value }})
    except (ValueError, OverflowError) as err:
        errors.add(
            '/'.join((
                {{ ref_parts|join(', ') }})),
            str(err))
''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_duration(
        value_expr: str, target_expr: str, ref_parts: List[str],
        a_type: mapry.Duration, auto_id: mapry.py.generate.AutoID) -> str:
    """
    Generate the code to parse a duration.

    The code parses the JSONable ``value_expr`` into the ``target_expr``.

    :param value_expr: Python expression of the JSONable value
    :param target_expr: Python expression of where to store the parsed value
    :param ref_parts: Python expression of reference path segments to the value
    :param a_type: mapry definition of the value type
    :param auto_id: generator of unique identifiers
    :return: generated code
    """
    uid = auto_id.next_identifier()

    return _PARSE_DURATION_TPL.render(
        uid=uid,
        value_expr=value_expr,
        ref_parts=ref_parts,
        target_expr=target_expr,
        a_type=a_type).rstrip("\n")


_PARSE_ARRAY_TPL = mapry.py.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{% if value_expr|is_variable %}{## set value expression ##}
{# Short-circuit value as value expression if it is a variable so that
we don't end up with an unnecessary variable1 = variable2 statement.#}
{% set value = value_expr %}
{% else %}
{% set value = "value_%s"|format(uid) %}
value_{{ uid }} = {{ value_expr }}
{% endif %}
{% set set_target %}{## set target block ##}
target_{{ uid }} = (
    []
)  # type: typing.List[{{ value_py_type }}]
for i_{{ uid }}, item_{{ uid }} in enumerate(
        {{ value }}):
    target_item_{{ uid }} = (
        None
    )  # type: typing.Optional[{{ value_py_type }}]
    {{ item_parsing|indent }}

    if target_item_{{ uid }} is not None:
        target_{{ uid }}.append(
            target_item_{{ uid }})

    if errors.full():
        break

{{ target_expr }} = target_{{ uid }}
{% endset %}
if not isinstance({{ value}}, list):
    errors.add(
        '/'.join((
            {{ ref_parts|join(', ') }})),
        "Expected a list, but got: {}".format(
            type({{ value }})))
{% if minimum_size is not none %}
elif len({{ value }}) < {{ minimum_size }}:
    errors.add(
        '/'.join((
            {{ ref_parts|join(', ') }})),
        "Expected a list of minimum size {{
            minimum_size }}, but got size: {}".format(
            len({{ value }})))
{% endif %}{# /if minimum_size is not none #}
{% if maximum_size is not none %}
elif len({{ value }}) > {{ maximum_size }}:
    errors.add(
        '/'.join((
            {{ ref_parts|join(', ') }})),
        "Expected a list of maximum size {{
            maximum_size }}, but got size: {}".format(
            len({{ value }})))
{% endif %}{# /if maximum_size is not none #}
else:
    {{ set_target|indent }}
''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_array(
        value_expr: str, target_expr: str, ref_parts: List[str],
        a_type: mapry.Array, registry_exprs: Mapping[mapry.Class, str],
        auto_id: mapry.py.generate.AutoID, py: mapry.Py) -> str:
    """
    Generate the code to parse an array.

    The code parses the JSONable ``value_expr`` into the ``target_expr``.

    :param value_expr: Python expression of the JSONable value
    :param target_expr: Python expression of where to store the parsed value
    :param ref_parts: Python expression of reference path segments to the value
    :param a_type: mapry definition of the value type
    :param registry_exprs:
        map class to Python expression of the registry of the class instances
    :param auto_id: generator of unique identifiers
    :param py: Python settings
    :return: generated code
    """
    uid = auto_id.next_identifier()

    item_parsing = _parse_value(
        value_expr="item_{uid}".format(uid=uid),
        target_expr="target_item_{uid}".format(uid=uid),
        ref_parts=ref_parts + ["str(i_{uid})".format(uid=uid)],
        a_type=a_type.values,
        registry_exprs=registry_exprs,
        auto_id=auto_id,
        py=py)

    return _PARSE_ARRAY_TPL.render(
        value_expr=value_expr,
        target_expr=target_expr,
        ref_parts=ref_parts,
        uid=uid,
        minimum_size=a_type.minimum_size,
        maximum_size=a_type.maximum_size,
        value_py_type=mapry.py.generate.type_repr(a_type=a_type.values, py=py),
        item_parsing=item_parsing).rstrip('\n')


_PARSE_MAP_TPL = mapry.py.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{% if value_expr|is_variable %}
{# Short-circuit value as value expression if it is a variable so that
we don't end up with an unnecessary variable1 = variable2 statement.#}
{% set value = value_expr %}
{% else %}
{% set value = "value_%s"|format(uid) %}
value_{{ uid }} = {{ value_expr }}
{% endif %}
if not isinstance({{ value }}, dict):
    errors.add(
        '/'.join((
            {{ ref_parts|join(', ') }})),
        "Expected a dict, but got: {}".format(
            type({{ value }})))
else:
    if isinstance({{ value }}, collections.OrderedDict):
        target_{{ uid }} = (
            collections.OrderedDict()
        )  # type: typing.MutableMapping[str, {{ value_py_type }}]
    else:
        target_{{ uid }} = (
            dict()
        )

    for key_{{ uid }}, value_{{ uid }} in {{ value }}.items():
        if not isinstance(key_{{ uid }}, str):
            errors.add(
                '/'.join((
                    {{ ref_parts|join(', ') }})),
                "Expected the key to be a str, but got: {}".format(
                    type(key_{{ uid }})))

            if errors.full():
                break
            else:
                continue

        target_item_{{ uid }} = (
            None
        )  # type: typing.Optional[{{ value_py_type }}]
        {{ item_parsing|indent|indent }}

        if target_item_{{ uid }} is not None:
            target_{{ uid }}[key_{{ uid }}] = target_item_{{ uid }}

        if errors.full():
            break

    if target_{{ uid }} is not None:
        {{ target_expr }} = target_{{ uid }}''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_map(
        value_expr: str, target_expr: str, ref_parts: List[str],
        a_type: mapry.Map, registry_exprs: Mapping[mapry.Class, str],
        auto_id: mapry.py.generate.AutoID, py: mapry.Py) -> str:
    """
    Generate the code to parse a map.

    The code parses the ``value_expr`` into the ``target_expr``.

    :param value_expr: Python expression of the JSONable value
    :param target_expr: Python expression of where to store the parsed value
    :param ref_parts: Python expression of reference path segments to the value
    :param a_type: mapry definition of the value type
    :param registry_exprs:
        map class to Python expression of the registry of the class instances
    :param auto_id: generator of unique identifiers
    :param py: Python settings
    :return: generated code
    """
    uid = auto_id.next_identifier()

    item_parsing = _parse_value(
        value_expr="value_{uid}".format(uid=uid),
        target_expr="target_item_{uid}".format(uid=uid),
        ref_parts=ref_parts + ["repr(key_{uid})".format(uid=uid)],
        a_type=a_type.values,
        registry_exprs=registry_exprs,
        auto_id=auto_id,
        py=py)

    return _PARSE_MAP_TPL.render(
        value_expr=value_expr,
        target_expr=target_expr,
        ref_parts=ref_parts,
        uid=uid,
        value_py_type=mapry.py.generate.type_repr(a_type=a_type.values, py=py),
        item_parsing=item_parsing)


@ensure(lambda result: not result.endswith('\n'))
def _parse_value(
        value_expr: str, target_expr: str, ref_parts: List[str],
        a_type: mapry.Type, registry_exprs: Mapping[mapry.Class, str],
        auto_id: mapry.py.generate.AutoID, py: mapry.Py) -> str:
    """
    Generate the code to parse a JSONable value.

    The code parses the ``value_expr`` into the ``target_expr``.

    :param value_expr: Python expression of the JSONable value
    :param target_expr: Python expression of where to store the parsed value
    :param ref_parts: Python expression of reference path segments to the value
    :param a_type: mapry type of the value
    :param registry_exprs:
        map class to Python expression of the registry of the class instances
    :param auto_id: generator of unique identifiers
    :param py: Python settings
    :return: generated code
    """
    # pylint: disable=too-many-branches
    if isinstance(a_type, mapry.Boolean):
        body = _parse_boolean(
            value_expr=value_expr,
            target_expr=target_expr,
            ref_parts=ref_parts,
            auto_id=auto_id)

    elif isinstance(a_type, mapry.Integer):
        body = _parse_integer(
            value_expr=value_expr,
            target_expr=target_expr,
            ref_parts=ref_parts,
            a_type=a_type,
            auto_id=auto_id)

    elif isinstance(a_type, mapry.Float):
        body = _parse_float(
            value_expr=value_expr,
            target_expr=target_expr,
            ref_parts=ref_parts,
            a_type=a_type,
            auto_id=auto_id)

    elif isinstance(a_type, mapry.String):
        body = _parse_string(
            value_expr=value_expr,
            target_expr=target_expr,
            ref_parts=ref_parts,
            a_type=a_type,
            auto_id=auto_id)

    elif isinstance(a_type, mapry.Path):
        body = _parse_path(
            value_expr=value_expr,
            target_expr=target_expr,
            ref_parts=ref_parts,
            a_type=a_type,
            auto_id=auto_id,
            py=py)

    elif isinstance(a_type, mapry.Date):
        body = _parse_date(
            value_expr=value_expr,
            target_expr=target_expr,
            ref_parts=ref_parts,
            a_type=a_type,
            auto_id=auto_id)

    elif isinstance(a_type, mapry.Datetime):
        body = _parse_date_time(
            value_expr=value_expr,
            target_expr=target_expr,
            ref_parts=ref_parts,
            a_type=a_type,
            auto_id=auto_id)

    elif isinstance(a_type, mapry.Time):
        body = _parse_time(
            value_expr=value_expr,
            target_expr=target_expr,
            ref_parts=ref_parts,
            a_type=a_type,
            auto_id=auto_id)

    elif isinstance(a_type, mapry.TimeZone):
        body = _parse_time_zone(
            value_expr=value_expr,
            target_expr=target_expr,
            ref_parts=ref_parts,
            a_type=a_type,
            auto_id=auto_id,
            py=py)

    elif isinstance(a_type, mapry.Duration):
        body = _parse_duration(
            value_expr=value_expr,
            target_expr=target_expr,
            ref_parts=ref_parts,
            a_type=a_type,
            auto_id=auto_id)

    elif isinstance(a_type, mapry.Array):
        body = _parse_array(
            value_expr=value_expr,
            target_expr=target_expr,
            ref_parts=ref_parts,
            a_type=a_type,
            registry_exprs=registry_exprs,
            auto_id=auto_id,
            py=py)

    elif isinstance(a_type, mapry.Map):
        body = _parse_map(
            value_expr=value_expr,
            target_expr=target_expr,
            ref_parts=ref_parts,
            a_type=a_type,
            registry_exprs=registry_exprs,
            auto_id=auto_id,
            py=py)

    elif isinstance(a_type, mapry.Class):
        body = _parse_instance_reference(
            value_expr=value_expr,
            target_expr=target_expr,
            ref_parts=ref_parts,
            a_type=a_type,
            registry_expr=registry_exprs[a_type],
            auto_id=auto_id)

    elif isinstance(a_type, mapry.Embed):
        body = _parse_embed(
            target_expr=target_expr,
            value_expr=value_expr,
            ref_parts=ref_parts,
            a_type=a_type,
            registry_exprs=registry_exprs,
            auto_id=auto_id,
            py=py)

    else:
        raise NotImplementedError(
            "Unhandled parsing of type: {}".format(a_type))

    return body


_PARSE_PROPERTY_TPL = mapry.py.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
##
# Parse {{ a_property.name|as_attribute }}
##

value_{{ uid }} = {{ value_obj_expr }}.get(
    {{ a_property.json|repr }},
    None)

{% if not a_property.optional %}
if value_{{ uid }} is None:
    errors.add(
        {% if ref_obj_parts|length > 1 %}
        '/'.join((
            {{ ref_obj_parts|join(', ') }})),
        {% elif ref_obj_parts|length == 1 %}
        {{ ref_obj_parts[0] }},
        {% else %}
        {{ _raise('Expected ref_obj_parts to be non-empty') }}
        {% endif %}{# /if ref_obj_parts|length > 1 #}
        {{ "Property is missing: %s"|format(a_property.json)|repr }})
else:
    {{ parsing|indent }}
{% else %}
if value_{{ uid }} is not None:
    {{ parsing|indent }}
{% endif %}{# /if not a_property.optional #}''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_property(
        target_obj_expr: str, value_obj_expr: str, ref_obj_parts: List[str],
        a_property: mapry.Property, registry_exprs: Mapping[mapry.Class, str],
        auto_id: mapry.py.generate.AutoID, py: mapry.Py) -> str:
    """
    Generate the code to parse a composite property from a JSONable object.

    :param target_obj_expr:
        Python expression of the object to store the properties
    :param value_obj_expr: Python expression of the JSONable object
    :param ref_obj_parts:
        Python expressions of reference path segments to the object
    :param a_property: mapry definition of the property
    :param registry_exprs:
        map class to Python expression of the registry of the class instances
    :param auto_id: generator of unique identifiers
    :param py: Python settings
    :return: generated code
    """
    uid = auto_id.next_identifier()

    attribute = mapry.py.naming.as_attribute(identifier=a_property.name)
    property_target_expr = '{}.{}'.format(target_obj_expr, attribute)
    property_ref_parts = ref_obj_parts + [repr(a_property.json)]

    # yapf: disable
    parsing = _parse_value(
        value_expr="value_{uid}".format(uid=uid),
        target_expr=property_target_expr,
        ref_parts=property_ref_parts,
        a_type=a_property.type,
        registry_exprs=registry_exprs,
        auto_id=auto_id,
        py=py)
    # yapf: enable

    text = _PARSE_PROPERTY_TPL.render(
        a_property=a_property,
        value_obj_expr=value_obj_expr,
        ref_obj_parts=ref_obj_parts,
        uid=uid,
        parsing=parsing,
        property_target_expr=property_target_expr)

    return text.rstrip("\n")


_PARSE_CLASS_REF_TPL = mapry.py.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{% if value_expr|is_variable %}
{# Short-circuit value as value expression if it is a variable so that
we don't end up with an unnecessary variable1 = variable2 statement.#}
{% set value = value_expr %}
{% else %}
{% set value = "value_%s"|format(uid) %}
value_{{ uid }} = {{ value_expr }}
{% endif %}
if not isinstance({{ value }}, str):
    errors.add(
        '/'.join((
            {{ ref_parts|join(', ') }})),
        "Expected a str, but got: {}".format(
            type({{ value }})))
else:
    target_{{ uid }} = {{ registry_expr }}.get(
        {{ value }},
        None)
    if target_{{ uid }} is None:
        errors.add(
            '/'.join((
                {{ ref_parts|join(', ') }})),
            {{ "Reference to an instance of class %s not found: {}"|
                format(class_name)|repr }}.format(
                {{ value }}))
    else:
        {{ target_expr }} = target_{{ uid }}''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_instance_reference(
        value_expr: str, target_expr: str, ref_parts: List[str],
        a_type: mapry.Class, registry_expr: str,
        auto_id: mapry.py.generate.AutoID) -> str:
    """
    Generate the code to parse a reference to an instance.

    The code parses the ``value_expr`` into the ``target_expr``.

    :param value_expr: Python expression of the JSONable value
    :param target_expr: Python expression of where to store the parsed value
    :param ref_parts: Python expression of reference path segments to the value
    :param a_type: mapry definition of the value type
    :param registry_expr:
        Python expression of the registry of the class instances
    :param auto_id: generator of unique identifiers
    :return: generated code
    """
    uid = auto_id.next_identifier()

    return _PARSE_CLASS_REF_TPL.render(
        value_expr=value_expr,
        target_expr=target_expr,
        ref_parts=ref_parts,
        uid=uid,
        class_name=a_type.name,
        registry_expr=registry_expr)


_PARSE_EMBED_TPL = mapry.py.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{% if value_expr|is_variable %}
{# Short-circuit value as value expression if it is a variable so that
we don't end up with an unnecessary variable1 = variable2 statement.#}
{% set value = value_expr %}
{% else %}
{% set value = "value_%s"|format(uid) %}
value_{{ uid }} = {{ value_expr }}
{% endif %}
target_{{ uid }} = (
    {{ py.module_name }}.parse.placeholder_{{ embed_name|as_variable }}()
)
_{{ embed_name|as_variable }}_from(
    {{ value }},
    {% for registry_expr in selected_registry_exprs %}
    {{ registry_expr }},
    {% endfor %}
    '/'.join((
        {{ ref_parts|join(', ') }})),
    target_{{ uid }},
    errors)
{{ target_expr }} = target_{{ uid }}
''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_embed(
        value_expr: str, target_expr: str, ref_parts: List[str],
        a_type: mapry.Embed, registry_exprs: Mapping[mapry.Class, str],
        auto_id: mapry.py.generate.AutoID, py: mapry.Py) -> str:
    """
    Generate the code to parse an embeddable structure.

    The code parses the ``value_expr`` into the ``target_expr``.

    :param value_expr: Python expression of the JSONable value
    :param target_expr: Python expression of where to store the parsed value
    :param ref_parts: Python expression of reference path segments to the value
    :param a_type: mapry definition of the value type
    :param registry_exprs:
        map class to Python expression of the registry of the class instances
    :param auto_id: generator of unique identifiers
    :param py: Python settings
    :return: generated code
    """
    uid = auto_id.next_identifier()

    references = mapry.references(a_type=a_type)

    return _PARSE_EMBED_TPL.render(
        value_expr=value_expr,
        target_expr=target_expr,
        ref_parts=ref_parts,
        uid=uid,
        embed_name=a_type.name,
        selected_registry_exprs=[
            registry_exprs[reference] for reference in references
        ],
        py=py)


_PARSE_COMPOSITE_TPL = mapry.py.jinja2_env.ENV.from_string(
    '''\
def _{{ composite.name|as_variable }}_from(
        value: typing.Any,
        {% for ref_cls in references %}
        {{ ref_cls.plural|as_variable }}_registry: typing.Mapping[
            str,
            {{ py.module_name }}.{{ ref_cls.name|as_composite }}],
        {% endfor %}
        ref: str,
        target: {{ py.module_name }}.{{ composite.name|as_composite }},
        errors: {{ py.module_name }}.parse.Errors
) -> None:
{% set doctext %}
parses {{ composite.name|as_composite }} from a JSONable value.

If ``errors``, the attributes of ``target`` have undefined values.

:param value: JSONable value
{% for ref_cls in references %}
:param {{ ref_cls.plural|as_variable }}_registry: registry of the {{
    ref_cls.name|as_composite }} instances
{% endfor %}
:param ref:
    reference to the value (e.g., a reference path)
:param target: parsed ``value`` as {{ composite.name|as_composite }}
:param errors: errors encountered during parsing
:return:
{% endset %}{# /set doctext #}
    {{ doctext|as_docstring|indent }}
    if not isinstance(value, dict):
        errors.add(
            ref,
            "Expected a dictionary, but got: {}".format(
                type(value)))
        return
    {% for prop in composite.properties.values() %}

    {{ property_parsing[prop]|indent }}
    if errors.full():
        return
    {% endfor %}{# /for prop in composite.properties.values() #}


def {{ composite.name|as_variable }}_from(
        value: typing.Any,
        {% if is_class %}
        id: str,
        {% endif %}
        {% for ref_cls in references %}
        {{ ref_cls.plural|as_variable }}_registry: typing.Mapping[
            str,
            {{ py.module_name }}.{{ ref_cls.name|as_composite }}],
        {% endfor %}
        ref: str,
        errors: {{ py.module_name }}.parse.Errors
) -> typing.Optional[{{ py.module_name }}.{{ composite.name|as_composite }}]:
{% set doctext %}
parses {{ composite.name|as_composite }} from a JSONable value.

:param value: JSONable value
:param id: identifier of the instance
{% for ref_cls in references %}
:param {{ ref_cls.plural|as_variable }}_registry:
    registry of the {{ ref_cls.name|as_composite }} instances
{% endfor %}
:param ref:
    reference to the value (e.g., a reference path)
:param errors: errors encountered during parsing
:return: parsed instance, or None if ``errors``
{% endset %}{# /set doctext #}
    {{ doctext|as_docstring|indent }}
    {% if is_class %}
    target = {{ py.module_name }}.parse.placeholder_{{
        composite.name|as_variable }}(id=id)
    {% else %}
    target = {{ py.module_name }}.parse.placeholder_{{
        composite.name|as_variable }}()
    {% endif %}{# /if is_class #}

    _{{ composite.name|as_variable }}_from(
        value=value,
        {% for ref_cls in references %}
        {{ ref_cls.plural|as_variable }}_registry={{
            ref_cls.plural|as_variable }}_registry,
        {% endfor %}
        ref=ref,
        target=target,
        errors=errors)

    if not errors.empty():
       return None

    return target''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_composite(
        composite: Union[mapry.Class, mapry.Embed], py: mapry.Py) -> str:
    """
    Generate the function that parses a composite.

    :param composite: mapry definition of the composite
    :param py: Python settings
    :return: generated code
    """
    references = mapry.references(a_type=composite)

    # yapf: disable
    registry_exprs = {
        ref_cls: '{}_registry'.format(
            mapry.py.naming.as_variable(ref_cls.plural))
        for ref_cls in references
    }
    # yapf: enable

    auto_id = mapry.py.generate.AutoID()

    # yapf: disable
    property_parsing = {
        prop: _parse_property(
            target_obj_expr="target",
            value_obj_expr="value",
            ref_obj_parts=["ref"],
            a_property=prop,
            registry_exprs=registry_exprs,
            auto_id=auto_id,
            py=py)
        for prop in composite.properties.values()
    }
    # yapf: enable

    return _PARSE_COMPOSITE_TPL.render(
        composite=composite,
        is_class=isinstance(composite, mapry.Class),
        references=references,
        property_parsing=property_parsing,
        py=py)


_PARSE_GRAPH_TPL = mapry.py.jinja2_env.ENV.from_string(
    '''\
def {{ graph.name|as_variable }}_from(
        value: typing.Any,
        ref: str,
        errors: {{ module_name }}.parse.Errors
) -> typing.Optional[{{ module_name }}.{{ graph.name|as_composite }}]:
{% set doctext %}
parses {{ graph.name|as_composite }} from a JSONable value.

:param value: JSONable value
:param ref: reference to the value (e.g., a reference path)
:param errors: errors encountered during parsing
:return: parsed {{ graph.name|as_composite }}, or None if ``errors``{#
#}{% endset %}{# /set doctext #}
    {{ doctext|as_docstring|indent }}
    if errors.full():
        return None

    if not isinstance(value, dict):
        errors.add(
            ref,
            "Expected a dictionary, but got: {}".format(type(value)))
        return None

    graph = {{ module_name }}.parse.placeholder_{{ graph.name|as_variable }}()
    {% for cls in graph.classes.values() %}

    ##
    # Pre-allocate {{ cls.plural|as_attribute }}
    ##

    registry_value = value.get({{ cls.plural|json_plural|repr }}, None)

    if registry_value is not None:
        if not isinstance(registry_value, dict):
            errors.add(
                '/'.join((
                    ref, {{ cls.plural|json_plural|repr }})),
                "Expected a dictionary, but got: {}".format(
                    type(registry_value)))
        else:
            if isinstance(registry_value, collections.OrderedDict):
                graph.{{ cls.plural|as_attribute }} = collections.OrderedDict()
            else:
                graph.{{ cls.plural|as_attribute }} = dict()

            {{ cls.plural|as_attribute }}_registry = graph.{{
                cls.plural|as_attribute }}
            for id in registry_value:
                {% if cls.id_pattern %}
                if not re.match(
                        r'{{ cls.id_pattern.pattern }}',
                        id):
                    errors.add(
                        '/'.join((
                            ref, {{ cls.plural|json_plural|repr }})),
                        {{ "Expected ID to match %s, but got: "|
                            format(cls.id_pattern.pattern)|repr }} + id)

                    if errors.full():
                        break

                {{ cls.plural|as_attribute
                    }}_registry[id] = {{ module_name }}.parse.placeholder_{{
                        cls.name|as_variable }}(id=id)
                {% else %}{# /if cls.id_pattern #}
                {{ cls.plural|as_attribute
                    }}_registry[id] = {{ module_name }}.parse.placeholder_{{
                        cls.name|as_variable }}(id=id)
                {% endif %}{# /if cls.id_pattern #}

    if errors.full():
        return None
    {% endfor %}{# /for cls #}
    {% if graph.classes %}

    # Errors from pre-allocation are considered critical.
    if not errors.empty():
        return None
    {% endif %}
    {% for cls in graph.classes.values() %}

    ##
    # Parse {{ cls.plural|as_attribute }}
    ##

    if {{ cls.plural|json_plural|repr }} in value:
        registry_value = value[{{ cls.plural|json_plural|repr }}]
        for id, instance_value in registry_value.items():
            target_{{ cls.name|as_variable }} = graph.{{
                cls.plural|as_attribute }}[id]
            target_{{ cls.name|as_variable }}.id = id

            _{{ cls.name|as_variable }}_from(
                instance_value,
                {% for ref_cls in references[cls] %}
                graph.{{ ref_cls.plural|as_attribute }},
                {% endfor %}
                '/'.join((
                    ref, {{ cls.plural|json_plural|repr }}, repr(id))),
                target_{{ cls.name|as_variable }},
                errors)

            if errors.full():
                return None
    {% endfor %}{# /for cls #}
    {% for property_parsing in property_parsings %}

    {{ property_parsing|indent }}

    if errors.full():
        return None
    {% endfor %}{# /for property_parsing #}

    if not errors.empty():
        return None

    return graph
''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_graph(graph: mapry.Graph, py: mapry.Py) -> str:
    """
    Generate the code that parses an object graph.

    :param graph: definition of the object graph
    :param py: Python settings
    :return: generated code
    """
    # Map mapry class -> referenced mapry classes
    references = dict()  # type: MutableMapping[mapry.Class, List[mapry.Class]]
    for cls in graph.classes.values():
        references[cls] = mapry.references(a_type=cls)

    # Map mapry class -> Python expression of the instance registry
    registry_exprs = dict()  # type: Dict[mapry.Class, str]
    for cls in graph.classes.values():
        plural_attribute = mapry.py.naming.as_attribute(identifier=cls.plural)
        registry_exprs[cls] = 'graph.{}'.format(plural_attribute)

    # Gather property parsings in a list
    # so that they can be readily inserted in the template
    property_parsings = []  # type: List[str]

    auto_id = mapry.py.generate.AutoID()
    for prop in graph.properties.values():
        property_parsings.append(
            _parse_property(
                target_obj_expr="graph",
                value_obj_expr="value",
                ref_obj_parts=["ref"],
                a_property=prop,
                registry_exprs=registry_exprs,
                auto_id=auto_id,
                py=py))

    text = _PARSE_GRAPH_TPL.render(
        graph=graph,
        module_name=py.module_name,
        references=references,
        property_parsings=property_parsings)

    return text.rstrip("\n")


@ensure(lambda result: result.endswith('\n'))
def generate(graph: mapry.Graph, py: mapry.Py) -> str:
    """
    Generate the source file to parse an object graph from a JSONable object.

    :param graph: mapry definition of the object graph
    :param py: Python settings
    :return: content of the source file
    """
    blocks = [
        mapry.py.generate.WARNING,
        mapry.py.generate.docstring("parses JSONable objects."),
        _imports(graph=graph, py=py)
    ]

    if mapry.needs_type(a_type=graph, query=mapry.Duration):
        blocks.append(_duration_from_string())

    nongraph_composites = []  # type: List[Union[mapry.Class, mapry.Embed]]
    nongraph_composites.extend(graph.classes.values())
    nongraph_composites.extend(graph.embeds.values())

    for class_or_embed in nongraph_composites:
        blocks.append(_parse_composite(composite=class_or_embed, py=py))

    blocks.append(_parse_graph(graph=graph, py=py))

    return '\n\n\n'.join(blocks) + '\n'
