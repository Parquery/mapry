"""Generate the code that parses the object graph from a JSONable structure."""

import textwrap
from typing import (  # pylint: disable=unused-import
    List, Mapping, MutableMapping, Optional, Pattern, Union)

from icontract import ensure

import mapry
import mapry.go.generate
import mapry.go.jinja2_env
import mapry.go.timeformat
import mapry.indention
import mapry.naming
import mapry.strftime


def _has_pattern_recursively(a_type: mapry.Type) -> bool:
    """
    Check if the type is constrained by a pattern.

    :param a_type: to be inspected
    :return: True if the type is constrained by a pattern
    """
    if isinstance(a_type, mapry.String) and a_type.pattern:
        return True

    if isinstance(a_type, mapry.Path) and a_type.pattern:
        return True

    if isinstance(a_type, mapry.Array):
        return _has_pattern_recursively(a_type=a_type.values)

    if isinstance(a_type, mapry.Map):
        return _has_pattern_recursively(a_type=a_type.values)

    return False


@ensure(lambda result: not result.endswith('\n'))
def _imports(graph: mapry.Graph) -> str:
    """
    Generate the import declaration.

    :param graph: mapry definition of the object graph
    :param go: Go settings
    :return: generated code
    """
    import_set = {'strings', 'fmt'}

    if mapry.needs_type(a_type=graph, query=mapry.Integer):
        import_set.add('math')

    # yapf: disable
    if any(mapry.needs_type(a_type=graph, query=query)
           for query in (mapry.Date, mapry.Time,
                         mapry.Datetime, mapry.TimeZone)):
        # yapf: enable
        import_set.add('time')

    if mapry.needs_type(a_type=graph, query=mapry.Duration):
        import_set.add('math')
        import_set.add('time')
        import_set.add('regexp')
        import_set.add('strconv')

    ##
    # Constrained by a pattern?
    ##

    has_pattern = False
    for a_type, _ in mapry.iterate_over_types(graph=graph):
        if (isinstance(a_type, (mapry.String, mapry.Path))
                and a_type.pattern is not None):
            has_pattern = True
            break

    for cls in graph.classes.values():
        if cls.id_pattern is not None:
            has_pattern = True
            break

    if has_pattern:
        import_set.add("regexp")

    ##
    # Any arrays?
    ##

    if any(isinstance(a_type, mapry.Array)
           for a_type, _ in mapry.iterate_over_types(graph=graph)):
        # needed to convert indices to strings in error messages
        import_set.add('strconv')

    return mapry.go.generate.import_declarations(import_set)


@ensure(lambda result: not result.endswith('\n'))
def _duration_from_string() -> str:
    """
    Generate the code for parsing durations from strings.

    :return: generated code
    """
    return textwrap.dedent(
        '''\
    var durationRe = regexp.MustCompile(
        `^(-|\\+)?P`+
        `(((0|[1-9][0-9]*)(\.[0-9]+)?)Y)?`+
        `(((0|[1-9][0-9]*)(\.[0-9]+)?)M)?`+
        `(((0|[1-9][0-9]*)(\.[0-9]+)?)W)?`+
        `(((0|[1-9][0-9]*)(\.[0-9]+)?)D)?`+
        `(T`+
        `(((0|[1-9][0-9]*)(\.[0-9]+)?)H)?`+
        `(((0|[1-9][0-9]*)(\.[0-9]+)?)M)?`+
        `(((0|[1-9][0-9]*)(\.([0-9]+))?)S)?`+
        `)?$`)

    // addDuration adds right nanoseconds to the left duration.
    //
    // addDurationInt64 requires:
    //  * left >= 0
    //  * right >= 0
    func addDuration(
        left time.Duration,
        right float64) (result time.Duration, overflow bool) {

        if !(left >= 0) {
            panic("Expected left >= 0")
        }

        if !(right >= 0) {
            panic("Expected right >= 0")
        }

        // 9223372036854775808.0 == 2^63 is the first float > MaxInt64.
        if right >= 9223372036854775808.0 {
            overflow = true
            return
        }

        rightAsNs := time.Duration(right)
        if rightAsNs > math.MaxInt64 - left {
            overflow = true
            return
        }

        result = left + rightAsNs
        return
    }

    // durationFromString parses the duration as ISO 8601 format.
    //
    // Following C++ chrono library, the following units are counted as:
    //  * years as 365.2425 days (the average length of a Gregorian year),
    //  * months as 30.436875 days (exactly 1/12 of years) and
    //  * weeks as 7 days.
    //
    // Since time.Duration is measured in nanoseconds, beware of overflow
    // issues due to finite representation of integers.
    func durationFromString(s string) (d time.Duration, err error) {
        m := durationRe.FindStringSubmatch(s)

        if len(m) == 0 {
            err = fmt.Errorf("failed to match the duration pattern")
            return
        }

        ////
        // Interprete
        ////

        var years, months, weeks, days, hours, minutes float64
        var seconds, nanoseconds int64

        sign := int64(1)
        if len(m[1]) > 0 && m[1][0] == '-' {
            sign = -1
        }

        if len(m[3]) > 0 {
            years, err = strconv.ParseFloat(m[3], 64)
            if err != nil {
                err = fmt.Errorf("failed to parse the years: %s", err.Error())
                return
            }
        }

        if len(m[7]) > 0 {
            months, err = strconv.ParseFloat(m[7], 64)
            if err != nil {
                err = fmt.Errorf("failed to parse the months: %s", err.Error())
                return
            }
        }

        if len(m[11]) > 0 {
            weeks, err = strconv.ParseFloat(m[11], 64)
            if err != nil {
                err = fmt.Errorf("failed to parse the weeks: %s", err.Error())
                return
            }
        }

        if len(m[15]) > 0 {
            days, err = strconv.ParseFloat(m[15], 64)
            if err != nil {
                err = fmt.Errorf("failed to parse the days: %s", err.Error())
                return
            }
        }

        if len(m[20]) > 0 {
            hours, err = strconv.ParseFloat(m[20], 64)
            if err != nil {
                err = fmt.Errorf("failed to parse the hours: %s", err.Error())
                return
            }
        }

        if len(m[24]) > 0 {
            minutes, err = strconv.ParseFloat(m[24], 64)
            if err != nil {
                err = fmt.Errorf("failed to parse the minutes: %s", err.Error())
                return
            }
        }

        if len(m[29]) > 0 {
            seconds, err = strconv.ParseInt(m[29], 10, 64)
            if err != nil {
                err = fmt.Errorf("failed to parse the seconds: %s", err.Error())
                return
            }
        }

        switch {
        case len(m[31]) == 0:
            // pass
        case len(m[31]) <= 9:
            trimmed := strings.TrimLeft(m[31], "0")
            if len(trimmed) > 0 {
                nanoseconds, err = strconv.ParseInt(trimmed, 10, 64)
                if err != nil {
                    err = fmt.Errorf(
                        "failed to parse nanoseconds from: %s",
                        err.Error())
                }

                order := 9 - len(m[31])
                for i := 0; i < order; i++ {
                    nanoseconds *= 10
                }
            }
        default:
            err = fmt.Errorf(
                "precision only up to nanoseconds supported")
            return
        }

        ////
        // Sum
        ////

        d = time.Duration(nanoseconds)

        if seconds > (math.MaxInt64 / (1000 * 1000 * 1000)) {
            err = fmt.Errorf("seconds overflow in nanoseconds")
            return
        }

        secondsAsNs := time.Duration(seconds * 1000 * 1000 * 1000)
        if secondsAsNs > math.MaxInt64 - d {
            err = fmt.Errorf(
                "overflow in nanoseconds")
            return
        }
        d += secondsAsNs

        var overflow bool
        d, overflow = addDuration(d, minutes * 6e10)
        if overflow {
            err = fmt.Errorf("overflow in nanoseconds")
            return
        }

        d, overflow = addDuration(d, hours * 3.6e12)
        if overflow {
            err = fmt.Errorf("overflow in nanoseconds")
            return
        }

        d, overflow = addDuration(d, days * 24.0 * 3.6e12)
        if overflow {
            err = fmt.Errorf("overflow in nanoseconds")
            return
        }

        d, overflow = addDuration(d, weeks * 7.0 * 24.0 * 3.6e12)
        if overflow {
            err = fmt.Errorf("overflow in nanoseconds")
            return
        }

        d, overflow = addDuration(d, months * 30.436875 * 24.0 * 3.6e12)
        if overflow {
            err = fmt.Errorf("overflow in nanoseconds")
            return
        }

        d, overflow = addDuration(d, years * 365.2425 * 24.0 * 3.6e12)
        if overflow {
            err = fmt.Errorf("overflow in nanoseconds")
            return
        }

        // d is always positive, so the multiplication by -1 can not
        // overflow since |math.MaxInt64| < |math.MinInt64|
        d *= time.Duration(sign);

        return
    }''')


def _enumerate_type_patterns_recursively(
        a_type: mapry.Type, mapping: MutableMapping[Pattern[str], int],
        next_id: int) -> int:
    """
    Recursively map patterns of the types to unique identifiers.

    :param a_type: to be uniquely identified
    :param mapping: resulting mapping
    :return: next available identifier to be assigned to a pattern
    """
    if isinstance(a_type, mapry.String) and a_type.pattern:
        mapping[a_type.pattern] = next_id
        next_id += 1
        return next_id

    if isinstance(a_type, mapry.Path) and a_type.pattern:
        mapping[a_type.pattern] = next_id
        next_id += 1
        return next_id

    if isinstance(a_type, mapry.Array):
        return _enumerate_type_patterns_recursively(
            a_type=a_type.values, mapping=mapping, next_id=next_id)

    if isinstance(a_type, mapry.Map):
        return _enumerate_type_patterns_recursively(
            a_type=a_type.values, mapping=mapping, next_id=next_id)

    return next_id


def _enumerate_patterns(graph: mapry.Graph
                        ) -> MutableMapping[Pattern[str], int]:
    """
    Map all the patterns to unique identifiers.

    The patterns include all the type patterns, class ID patterns *etc.*

    :param graph: mapry definition of the object graph
    :return: mapping from patterns to unique identifiers
    """
    mapping = dict()  # type: MutableMapping[Pattern[str], int]

    next_id = 0

    for cls in graph.classes.values():
        if cls.id_pattern is not None:
            mapping[cls.id_pattern] = next_id
            next_id += 1

    for cls in graph.classes.values():
        for prop in cls.properties.values():
            next_id = _enumerate_type_patterns_recursively(
                a_type=prop.type, mapping=mapping, next_id=next_id)

    for embed in graph.embeds.values():
        for prop in embed.properties.values():
            next_id = _enumerate_type_patterns_recursively(
                a_type=prop.type, mapping=mapping, next_id=next_id)

    for prop in graph.properties.values():
        next_id = _enumerate_type_patterns_recursively(
            a_type=prop.type, mapping=mapping, next_id=next_id)

    return mapping


_COMPILE_REGEXES_TPL = mapry.go.jinja2_env.ENV.from_string(
    '''\
{% for uid in uids %}
var pattern{{ uid }} = regexp.MustCompile(
    {{ uids_to_patterns[uid].pattern|ticked_str }})
{% endfor %}{# /for uid in uids #}
''')


@ensure(lambda result: not result.endswith('\n'))
def _compile_regexes(pattern_uids: Mapping[Pattern[str], int]) -> str:
    """
    Generate statements that compile the global regular expressions.

    :param pattern_uids: uniquely identified patterns
    :return: generated code (or empty if no regexes need to be compiled)
    """
    if len(pattern_uids) == 0:
        return ''

    assert len(set(pattern_uids.values())) == len(pattern_uids.values()), \
        "Expected pattern identifiers to be unique, but got:\n{!r}".format(
            pattern_uids)

    uids_to_patterns = {uid: pattern for pattern, uid in pattern_uids.items()}

    return _COMPILE_REGEXES_TPL.render(
        uids_to_patterns=uids_to_patterns,
        uids=sorted(uids_to_patterns.keys())).rstrip('\n')


_PARSE_BOOLEAN_TPL = mapry.go.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{% if value_expr|is_variable %}
cast{{ uid }}, ok{{ uid }} := {{ value_expr }}.(bool)
{% else %}
cast{{ uid }}, ok{{ uid }} := ({{ value_expr }}).(bool)
{% endif %}
if !ok{{ uid }} {
    errors.Add(
        strings.Join(
            []string{
                {{ ref_parts|join(', ') }}},
            "/"),
        fmt.Sprintf(
            "expected a bool, but got: %T",
            {{ value_expr }}))
} else {
    {{ target_expr }} = cast{{ uid }}
}
''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_boolean(
        value_expr: str, target_expr: str, ref_parts: List[str],
        auto_id: mapry.go.generate.AutoID) -> str:
    """
    Generate the code to parse a boolean.

    The code parses the JSONable ``value_expr`` into the ``target_expr``.

    :param value_expr: Go expression of the value
    :param target_expr: Go expression of where to store the parsed value
    :param ref_parts: Go expression of reference path segments to the value
    :param auto_id: generator of unique identifiers
    :return: Go code
    """
    uid = auto_id.next_identifier()

    return _PARSE_BOOLEAN_TPL.render(
        uid=uid,
        value_expr=value_expr,
        ref_parts=ref_parts,
        target_expr=target_expr)


_PARSE_INTEGER_TPL = mapry.go.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{% if value_expr|is_variable %}
fcast{{ uid }}, ok{{ uid }} := {{ value_expr }}.(float64)
{% else %}
fcast{{ uid }}, ok{{ uid }} := ({{ value_expr }}).(float64)
{% endif %}{# /if value_expr|is_variable #}
if !ok{{ uid }} {
    errors.Add(
        strings.Join(
            []string{
                {{ ref_parts|join(', ') }}},
            "/"),
        fmt.Sprintf(
            "expected a float64, but got: %T",
            {{ value_expr }}))
} else if fcast{{ uid }} != math.Trunc(fcast{{ uid }}) {
    errors.Add(
        strings.Join(
            []string{
                {{ ref_parts|join(', ') }}},
            "/"),
        fmt.Sprintf(
            "expected a whole number, but got: %f",
            fcast{{ uid }}))
// 9223372036854775808.0 == 2^63 is the first float > MaxInt64.
// -9223372036854775808.0 == -(2^63) is the last float >= MinInt64.
} else if fcast{{ uid }} >= 9223372036854775808.0 ||
    fcast{{ uid }} < -9223372036854775808.0 {

    errors.Add(
        strings.Join(
            []string{
                {{ ref_parts|join(', ') }}},
            "/"),
        fmt.Sprintf(
            "expected the value to fit into int64, but got an overflow: %f",
            fcast{{ uid }}))
} else {
    {% if a_type.minimum is none and a_type.maximum is none %}
    {{ target_expr }} = int64(fcast{{ uid }})
    {% else %}
    cast{{ uid }} := int64(fcast{{ uid }})

    {% set got_cond_before = False %}
    {% if a_type.minimum is not none %}
    {% set op = ">" if a_type.exclusive_minimum else ">="  %}
    if !(cast{{ uid }} {{ op }} {{ a_type.minimum }}) {
        errors.Add(
            strings.Join(
                []string{
                    {{ ref_parts|join(', ') }}},
                "/"),
            fmt.Sprintf(
                {{ "expected %s %d, but got: %%d"|
                    format(op, a_type.minimum)|escaped_str }},
                cast{{ uid }}))
    {% set got_cond_before = True %}
    {% endif %}{# /if a_type.minimum is not none #}
    {% if a_type.maximum is not none %}
    {% set op = "<" if a_type.exclusive_maximum else "<=" %}
    {{ '} else if'
        if got_cond_before else 'if'
    }} !(cast{{ uid }} {{ op }} {{ a_type.maximum }}) {
        errors.Add(
            strings.Join(
                []string{
                    {{ ref_parts|join(', ') }}},
                    "/"),
            fmt.Sprintf(
                {{ "expected %s %d, but got: %%d"|
                    format(op, a_type.maximum)|escaped_str }},
                cast{{ uid }}))
    {% set got_cond_before = True %}
    {% endif %}{# /if a_type.maximum is not none #}
    } else {
        {{ target_expr }} = cast{{ uid }}
    }
    {% endif %}{# /if a_type.minimum is none and a_type.maximum is none #}
}
''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_integer(
        value_expr: str, target_expr: str, ref_parts: List[str],
        a_type: mapry.Integer, auto_id: mapry.go.generate.AutoID) -> str:
    """
    Generate the code to parse an integer.

    The code parses the JSONable ``value_expr`` into the ``target_expr``.

    :param value_expr: Go expression of the value
    :param target_expr: Go expression of where to store the parsed value
    :param ref_parts: Go expression of reference path segments to the value
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


_PARSE_FLOAT_TPL = mapry.go.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{% if value_expr|is_variable %}
cast{{ uid }}, ok{{ uid }} := {{ value_expr }}.(float64)
{% else %}
cast{{ uid }}, ok{{ uid }} := ({{ value_expr }}).(float64)
{% endif %}{# /if value_expr|is_variable #}
if !ok{{ uid }} {
    errors.Add(
        strings.Join(
            []string{
                {{ ref_parts|join(', ') }}},
            "/"),
        fmt.Sprintf(
            "expected a float64, but got: %T",
            {{ value_expr }}))
} else {
    {% if a_type.minimum is none and a_type.maximum is none %}
    {{ target_expr }} = cast{{ uid }}
    {% else %}
    {% set got_cond_before = False %}
    {% if a_type.minimum is not none %}
    {% set op = ">" if a_type.exclusive_minimum else ">="  %}
    if !(cast{{ uid }} {{ op }} {{ a_type.minimum }}) {
        errors.Add(
            strings.Join(
                []string{
                    {{ ref_parts|join(', ') }}},
                "/"),
            fmt.Sprintf(
                {{ "expected %s %f, but got: %%f"|
                    format(op, a_type.minimum)|escaped_str }},
                cast{{ uid }}))
    {% set got_cond_before = True %}
    {% endif %}{# /if a_type.minimum is not none #}
    {% if a_type.maximum is not none %}
    {% set op = "<" if a_type.exclusive_maximum else "<=" %}
    {{ '} else if'
        if got_cond_before else 'if'
    }} !(cast{{ uid }} {{ op }} {{ a_type.maximum }}) {
        errors.Add(
            strings.Join(
                []string{
                    {{ ref_parts|join(', ') }}},
                    "/"),
            fmt.Sprintf(
                {{ "expected %s %f, but got: %%f"|
                    format(op, a_type.maximum)|escaped_str }},
                cast{{ uid }}))
    {% set got_cond_before = True %}
    {% endif %}{# /if a_type.maximum is not none #}
    } else {
        {{ target_expr }} = cast{{ uid }}
    }
    {% endif %}{# /if a_type.minimum is none and a_type.maximum is none #}
}
''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_float(
        value_expr: str, target_expr: str, ref_parts: List[str],
        a_type: mapry.Float, auto_id: mapry.go.generate.AutoID) -> str:
    """
    Generate the code to parse a floating-point number.

    The code parses the JSONable ``value_expr`` into the ``target_expr``.

    :param value_expr: Go expression of the value
    :param target_expr: Go expression of where to store the parsed value
    :param ref_parts: Go expression of reference path segments to the value
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


_PARSE_STRING_TPL = mapry.go.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{% if value_expr|is_variable %}
cast{{ uid }}, ok{{ uid }} := {{ value_expr }}.(string)
{% else %}
cast{{ uid }}, ok{{ uid }} := ({{ value_expr }}).(string)
{% endif %}{# /if value_expr|is_variable #}
if !ok{{ uid }} {
    errors.Add(
        strings.Join(
            []string{
                {{ ref_parts|join(', ') }}},
            "/"),
        fmt.Sprintf(
            "expected a string, but got: %T",
            {{ value_expr }}))
} else {
    {% if a_type.pattern is none %}
    {{ target_expr }} = cast{{ uid }}
    {% else %}
    if !pattern{{ pattern_uids[a_type.pattern] }}.MatchString(cast{{ uid }}) {
        errors.Add(
            strings.Join(
                []string{
                    {{ ref_parts|join(', ') }}},
                "/"),
            fmt.Sprintf(
                {{ "expected to match %s, but got: %%s"|
                    format(a_type.pattern.pattern)|escaped_str }},
                cast{{ uid }}))
    } else {
        {{ target_expr }} = cast{{ uid }}
    }
    {% endif %}{# /if a_type.pattern is none #}
}
''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_string(
        value_expr: str, target_expr: str, ref_parts: List[str],
        a_type: Union[mapry.String, mapry.Path],
        pattern_uids: Mapping[Pattern[str], int],
        auto_id: mapry.go.generate.AutoID) -> str:
    """
    Generate the code to parse a string.

    The code parses the JSONable ``value_expr`` into the ``target_expr``.

    :param value_expr: Go expression of the value
    :param target_expr: Go expression of where to store the parsed value
    :param ref_parts: Go expression of reference path segments to the value
    :param a_type: mapry definition of the value type
    :param pattern_uids: uniquely identified patterns
    :param auto_id: generator of unique identifiers
    :return: generated code
    """
    uid = auto_id.next_identifier()

    return _PARSE_STRING_TPL.render(
        uid=uid,
        value_expr=value_expr,
        ref_parts=ref_parts,
        target_expr=target_expr,
        a_type=a_type,
        pattern_uids=pattern_uids).rstrip("\n")


_PARSE_DATE_TIME_TPL = mapry.go.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{% if value_expr|is_variable %}
cast{{ uid }}, ok{{ uid }} := {{ value_expr }}.(string)
{% else %}
cast{{ uid }}, ok{{ uid }} := ({{ value_expr }}).(string)
{% endif %}{# /if value_expr|is_variable #}
if !ok{{ uid }} {
    errors.Add(
        strings.Join(
            []string{
                {{ ref_parts|join(', ') }}},
            "/"),
        fmt.Sprintf(
            "expected a string, but got: %T",
            {{ value_expr }}))
} else {
    target{{ uid }}, err{{ uid }} := time.Parse(
        {{ converted_format|escaped_str }},
        cast{{ uid }})
    if err{{ uid }} != nil {
        errors.Add(
            strings.Join(
                []string{
                    {{ ref_parts|join(', ') }}},
                "/"),
            fmt.Sprintf(
                {{ "expected layout %s, got: %%s"|
                    format(converted_format)|escaped_str }},
                cast{{ uid }}))
    } else {
        {{ target_expr }} = target{{ uid }}
    }
}
''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_date_time(
        value_expr: str, target_expr: str, ref_parts: List[str],
        a_type: Union[mapry.Date, mapry.Datetime, mapry.Time],
        auto_id: mapry.go.generate.AutoID) -> str:
    """
    Generate the code to parse a time.Time.

    The code parses the JSONable ``value_expr`` into the ``target_expr``.

    :param value_expr: Go expression of the value
    :param target_expr: Go expression of where to store the parsed value
    :param ref_parts: Go expression of reference path segments to the value
    :param a_type: mapry definition of the value type
    :param auto_id: generator of unique identifiers
    :return: generated code
    """
    uid = auto_id.next_identifier()

    converted_format = mapry.go.timeformat.convert(a_format=a_type.format)

    return _PARSE_DATE_TIME_TPL.render(
        value_expr=value_expr,
        uid=uid,
        ref_parts=ref_parts,
        converted_format=converted_format,
        target_expr=target_expr)


_PARSE_TIME_ZONE_TPL = mapry.go.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{% if value_expr|is_variable %}
cast{{ uid }}, ok{{ uid }} := {{ value_expr }}.(string)
{% else %}
cast{{ uid }}, ok{{ uid }} := ({{ value_expr }}).(string)
{% endif %}{# /if value_expr|is_variable #}
if !ok{{ uid }} {
    errors.Add(
        strings.Join(
            []string{
                {{ ref_parts|join(', ') }}},
            "/"),
        fmt.Sprintf(
            "expected a string, but got: %T",
            {{ value_expr }}))
} else {
    target{{ uid }}, err{{ uid }} := time.LoadLocation(cast{{ uid }})
    if err{{ uid }} != nil {
        errors.Add(
            strings.Join(
                []string{
                    {{ ref_parts|join(', ') }}},
                "/"),
            fmt.Sprintf(
                "failed to load location from %#v: %s",
                cast{{ uid }},
                err{{ uid }}.Error()))
    } else {
        {{ target_expr }} = target{{ uid }}
    }
}
''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_time_zone(
        value_expr: str, target_expr: str, ref_parts: List[str],
        auto_id: mapry.go.generate.AutoID) -> str:
    """
    Generate the code to parse a time.Loc.

    The code parses the JSONable ``value_expr`` into the ``target_expr``.

    :param value_expr: Go expression of the value
    :param target_expr: Go expression of where to store the parsed value
    :param ref_parts: Go expression of reference path segments to the value
    :param a_type: mapry definition of the value type
    :param auto_id: generator of unique identifiers
    :return: generated code
    """
    uid = auto_id.next_identifier()

    return _PARSE_TIME_ZONE_TPL.render(
        value_expr=value_expr,
        uid=uid,
        ref_parts=ref_parts,
        target_expr=target_expr)


_PARSE_DURATION_TPL = mapry.go.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{% if value_expr|is_variable %}
cast{{ uid }}, ok{{ uid }} := {{ value_expr }}.(string)
{% else %}
cast{{ uid }}, ok{{ uid }} := ({{ value_expr }}).(string)
{% endif %}{# /if value_expr|is_variable #}
if !ok{{ uid }} {
    errors.Add(
        strings.Join(
            []string{
                {{ ref_parts|join(', ') }}},
            "/"),
        fmt.Sprintf(
            "expected a string, but got: %T",
            {{ value_expr }}))
} else {
    target{{ uid }}, err{{ uid }} := durationFromString(cast{{uid}})
    if err{{ uid }} != nil {
        errors.Add(
            strings.Join(
                []string{
                    {{ ref_parts|join(', ') }}},
                "/"),
            fmt.Sprintf(
                "failed to parse duration from %#v: %s",
                cast{{ uid }},
                err{{ uid }}.Error()))
    } else {
        {{ target_expr }} = target{{ uid }}
    }
}
''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_duration(
        value_expr: str, target_expr: str, ref_parts: List[str],
        auto_id: mapry.go.generate.AutoID) -> str:
    """
    Generate the code to parse a time.Duration.

    The code parses the ``value_expr`` into the ``target_expr``.

    :param value_expr: Go expression of the value
    :param target_expr: Go expression of where to store the parsed value
    :param ref_parts: Go expression of reference path segments to the value
    :param auto_id: generator of unique identifiers
    :return: generated code
    """
    uid = auto_id.next_identifier()

    return _PARSE_DURATION_TPL.render(
        value_expr=value_expr,
        uid=uid,
        ref_parts=ref_parts,
        target_expr=target_expr)


_PARSE_ARRAY_TPL = mapry.go.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{% set set_target %}{## set target block ##}
target{{ uid }} := make(
    {{ target_go_type }},
    len(cast{{ uid }}))
for i{{ uid }} := range cast{{ uid }} {
    {{ item_parsing|indent }}

    if errors.Full() {
        break;
    }
}

{{ target_expr }} = target{{ uid }}{#
#}{% endset %}{# /set target block #}
{% if value_expr|is_variable %}
cast{{ uid }}, ok{{ uid }} := {{ value_expr }}.([]interface{})
{% else %}
cast{{ uid }}, ok{{ uid }} := ({{ value_expr }}).([]interface{})
{% endif %}{# /if value_expr|is_variable #}
if !ok{{ uid }} {
    errors.Add(
        strings.Join(
            []string{
                {{ ref_parts|join(', ') }}},
            "/"),
        fmt.Sprintf(
            "expected a []interface{}, but got: %T",
            {{ value_expr }}))
{% if minimum_size is not none %}
} else if len(cast{{ uid }}) < {{ minimum_size }} {
    errors.Add(
        strings.Join(
            []string{
                {{ ref_parts|join(', ') }}},
            "/"),
        fmt.Sprintf(
            {{ "expected an array of minimum size %d, but got: %%d"|
                format(minimum_size)|escaped_str }},
            len(cast{{ uid }})))
{% endif %}{# /if minimum_size is not none #}
{% if maximum_size is not none %}
} else if len(cast{{ uid }}) > {{ maximum_size }} {
    errors.Add(
        strings.Join(
            []string{
                {{ ref_parts|join(', ') }}},
            "/"),
        fmt.Sprintf(
            {{ "expected an array of maximum size %d, but got: %%d"|
                format(maximum_size)|escaped_str }},
            len(cast{{ uid }})))
{% endif %}{# /if maximum_size is not none #}
} else {
    {{ set_target|indent }}
}
''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_array(
        value_expr: str, target_expr: str, ref_parts: List[str],
        a_type: mapry.Array, registry_exprs: Mapping[mapry.Class, str],
        pattern_uids: Mapping[Pattern[str], int],
        auto_id: mapry.go.generate.AutoID, go: mapry.Go) -> str:
    """
    Generate the code to parse an array.

    The code parses the ``value_expr`` into the ``target_expr``.

    :param value_expr: Go expression of the value
    :param target_expr: Go expression of where to store the parsed value
    :param ref_parts: Go expression of reference path segments to the value
    :param a_type: mapry definition of the value type
    :param registry_exprs:
        map class to Go expression of the registry of the class instances
    :param pattern_uids: uniquely identified patterns
    :param auto_id: generator of unique identifiers
    :param go: Go settings
    :return: generated code
    """
    uid = auto_id.next_identifier()

    item_parsing = _parse_value(
        value_expr="cast{uid}[i{uid}]".format(uid=uid),
        target_expr="target{uid}[i{uid}]".format(uid=uid),
        ref_parts=ref_parts + ["strconv.Itoa(i{uid})".format(uid=uid)],
        a_type=a_type.values,
        registry_exprs=registry_exprs,
        pattern_uids=pattern_uids,
        auto_id=auto_id,
        go=go)

    return _PARSE_ARRAY_TPL.render(
        value_expr=value_expr,
        target_expr=target_expr,
        ref_parts=ref_parts,
        uid=uid,
        minimum_size=a_type.minimum_size,
        maximum_size=a_type.maximum_size,
        target_go_type=mapry.go.generate.type_repr(a_type=a_type, go=go),
        item_parsing=item_parsing).rstrip('\n')


_PARSE_MAP_TPL = mapry.go.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{% if value_expr|is_variable %}
cast{{ uid }}, ok{{ uid }} := {{ value_expr }}.(map[string]interface{})
{% else %}
cast{{ uid }}, ok{{ uid }} := ({{ value_expr }}).(map[string]interface{})
{% endif %}{# /if value_expr|is_variable #}
if !ok{{ uid }} {
    errors.Add(
        strings.Join(
            []string{
                {{ ref_parts|join(', ') }}},
            "/"),
        fmt.Sprintf(
            "expected a map[string]interface{}, but got: %T",
            {{ value_expr }}))
} else {
    target{{ uid }} := make({{ target_go_type }})
    for k{{ uid }} := range cast{{ uid }} {
        {{ item_parsing|indent|indent }}

        if errors.Full() {
            break;
        }
    }

    {{ target_expr }} = target{{ uid }}
}
''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_map(
        value_expr: str, target_expr: str, ref_parts: List[str],
        a_type: mapry.Map, registry_exprs: Mapping[mapry.Class, str],
        pattern_uids: Mapping[Pattern[str], int],
        auto_id: mapry.go.generate.AutoID, go: mapry.Go) -> str:
    """
    Generate the code to parse a map.

    The code parses the ``value_expr`` into the ``target_expr``.

    :param value_expr: Go expression of the value
    :param target_expr: Go expression of where to store the parsed value
    :param ref_parts: Go expression of reference path segments to the value
    :param a_type: mapry definition of the value type
    :param registry_exprs:
        map class to Go expression of the registry of the class instances
    :param pattern_uids: uniquely identified patterns
    :param auto_id: generator of unique identifiers
    :param go: Go settings
    :return: generated code
    """
    uid = auto_id.next_identifier()

    item_parsing = _parse_value(
        value_expr="cast{uid}[k{uid}]".format(uid=uid),
        target_expr="target{uid}[k{uid}]".format(uid=uid),
        ref_parts=ref_parts + ["k{uid}".format(uid=uid)],
        a_type=a_type.values,
        registry_exprs=registry_exprs,
        pattern_uids=pattern_uids,
        auto_id=auto_id,
        go=go)

    return _PARSE_MAP_TPL.render(
        value_expr=value_expr,
        target_expr=target_expr,
        ref_parts=ref_parts,
        uid=uid,
        target_go_type=mapry.go.generate.type_repr(a_type=a_type, go=go),
        item_parsing=item_parsing).rstrip('\n')


@ensure(lambda result: not result.endswith('\n'))
def _parse_value(
        value_expr: str, target_expr: str, ref_parts: List[str],
        a_type: mapry.Type, registry_exprs: Mapping[mapry.Class, str],
        pattern_uids: Mapping[Pattern[str], int],
        auto_id: mapry.go.generate.AutoID, go: mapry.Go) -> str:
    """
    Generate the code to parse a value.

    The code parses the ``value_expr`` into the ``target_expr``.

    :param value_expr: Go expression of the value
    :param target_expr: Go expression of where to store the parsed value
    :param ref_parts: Go expression of reference path segments to the value
    :param a_type: mapry type of the value
    :param registry_exprs:
        map class to Go expression of the registry of the class instances
    :param pattern_uids: uniquely identified patterns
    :param auto_id: generator of unique identifiers
    :param go: Go settings
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

    elif isinstance(a_type, (mapry.String, mapry.Path)):
        body = _parse_string(
            value_expr=value_expr,
            target_expr=target_expr,
            ref_parts=ref_parts,
            a_type=a_type,
            pattern_uids=pattern_uids,
            auto_id=auto_id)

    elif isinstance(a_type, (mapry.Date, mapry.Datetime, mapry.Time)):
        body = _parse_date_time(
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
            auto_id=auto_id)

    elif isinstance(a_type, mapry.Duration):
        body = _parse_duration(
            value_expr=value_expr,
            target_expr=target_expr,
            ref_parts=ref_parts,
            auto_id=auto_id)

    elif isinstance(a_type, mapry.Array):
        body = _parse_array(
            value_expr=value_expr,
            target_expr=target_expr,
            ref_parts=ref_parts,
            a_type=a_type,
            registry_exprs=registry_exprs,
            pattern_uids=pattern_uids,
            auto_id=auto_id,
            go=go)

    elif isinstance(a_type, mapry.Map):
        body = _parse_map(
            value_expr=value_expr,
            target_expr=target_expr,
            ref_parts=ref_parts,
            a_type=a_type,
            registry_exprs=registry_exprs,
            pattern_uids=pattern_uids,
            auto_id=auto_id,
            go=go)

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
            go=go)

    else:
        raise NotImplementedError(
            "Unhandled parsing of type: {}".format(a_type))

    return body


_PARSE_PROPERTY_TPL = mapry.go.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
////
// Parse {{ a_property.name|ucamel_case }}
////

value{{ uid }}, ok{{ uid }} := {{ value_map_expr }}[
    {{ a_property.json|escaped_str }}]

{% if not a_property.optional %}
if !ok{{ uid }} {
    errors.Add(
        {% if ref_obj_parts|length > 1 %}
        strings.Join(
            []string{
                {{ ref_obj_parts|join(', ') }}},
            "/"),
        {% elif ref_obj_parts|length == 1 %}
        {{ ref_obj_parts[0] }},
        {% else %}
        {{ _raise('Expected ref_obj_parts to be non-empty') }}
        {% endif %}{# /if ref_obj_parts|length > 1 #}
        {{ "property is missing: %s"|format(a_property.json)|escaped_str }})
} else {
    {{ parsing|indent }}
}
{% else %}
if ok{{ uid }} {
    {% if not is_pointer_type %}
    var target{{ uid }} {{ property_target_type }}
    {{ parsing|indent }}

    {{ property_target_expr }} = &target{{ uid }}
    {% else %}
    {{ parsing|indent }}
    {% endif %}{# /if not is_pointer_type #}
}
{% endif %}{# /if not a_property.optional #}
''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_property(
        target_obj_expr: str, value_map_expr: str, ref_obj_parts: List[str],
        a_property: mapry.Property, registry_exprs: Mapping[mapry.Class, str],
        pattern_uids: Mapping[Pattern[str], int],
        auto_id: mapry.go.generate.AutoID, go: mapry.Go) -> str:
    """
    Generate the code to parse a composite property from a JSONable object.

    :param target_obj_expr: Go expression of the object to store the properties
    :param value_map_expr: Go expression of the object as map[string]interface{}
    :param ref_obj_parts: Go expression of reference path segments to the object
    :param a_property: mapry definition of the property
    :param registry_exprs:
        map class to Go expression of the registry of the class instances
    :param pattern_uids: uniquely identified patterns
    :param auto_id: generator of unique identifiers
    :param go: Go settings
    :return: generated code
    """
    uid = auto_id.next_identifier()

    field = mapry.naming.ucamel_case(identifier=a_property.name)
    property_target_expr = '{}.{}'.format(target_obj_expr, field)
    property_ref_parts = (
        ref_obj_parts + [mapry.go.generate.escaped_str(a_property.json)])

    is_pointer_type = None  # type: Optional[bool]

    if not a_property.optional:
        # yapf: disable
        parsing = _parse_value(
            value_expr="value{uid}".format(uid=uid),
            target_expr=property_target_expr,
            ref_parts=property_ref_parts,
            a_type=a_property.type,
            registry_exprs=registry_exprs,
            pattern_uids=pattern_uids,
            auto_id=auto_id,
            go=go)
        # yapf: enable
    else:
        is_pointer_type = mapry.go.generate.is_pointer_type(
            a_type=a_property.type)

        if is_pointer_type:
            # yapf: disable
            parsing = _parse_value(
                value_expr="value{uid}".format(uid=uid),
                target_expr=property_target_expr,
                ref_parts=property_ref_parts,
                a_type=a_property.type,
                registry_exprs=registry_exprs,
                pattern_uids=pattern_uids,
                auto_id=auto_id,
                go=go)
            # yapf: enable
        else:
            # The target field is a pointer so the resulting field needs
            # to reference the intermediate parsed value.
            # yapf: disable
            parsing = _parse_value(
                value_expr="value{uid}".format(uid=uid),
                target_expr="target{uid}".format(uid=uid),
                ref_parts=property_ref_parts,
                a_type=a_property.type,
                registry_exprs=registry_exprs,
                pattern_uids=pattern_uids,
                auto_id=auto_id,
                go=go)
            # yapf: enable

    text = _PARSE_PROPERTY_TPL.render(
        a_property=a_property,
        value_map_expr=value_map_expr,
        ref_obj_parts=ref_obj_parts,
        uid=uid,
        is_pointer_type=is_pointer_type,
        property_target_type=mapry.go.generate.type_repr(
            a_type=a_property.type, go=go),
        parsing=parsing,
        property_target_expr=property_target_expr)

    return text.rstrip("\n")


_PARSE_CLASS_REF_TPL = mapry.go.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{% if value_expr|is_variable %}
cast{{ uid }}, ok{{ uid }} := {{ value_expr }}.(string)
{% else %}
cast{{ uid }}, ok{{ uid }} := ({{ value_expr }}).(string)
{% endif %}{# /if value_expr|is_variable #}
if !ok{{ uid }} {
    errors.Add(
        strings.Join(
            []string{
                {{ ref_parts|join(', ') }}},
            "/"),
        fmt.Sprintf(
            "expected a string, but got: %T",
            {{ value_expr }}))
} else {
    target{{ uid }}, ok{{ uid }} := {{ registry_expr }}[cast{{ uid }}]
    if !ok{{ uid }} {
        errors.Add(
            strings.Join(
                []string{
                    {{ ref_parts|join(', ') }}},
                "/"),
            fmt.Sprintf(
                {{ "reference to an instance of class %s not found: %%s"
                    |format(class_name|ucamel_case)|escaped_str }},
                {{ value_expr }}))
    } else {
        {{ target_expr }} = target{{uid}}
    }
}
''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_instance_reference(
        value_expr: str, target_expr: str, ref_parts: List[str],
        a_type: mapry.Class, registry_expr: str,
        auto_id: mapry.go.generate.AutoID) -> str:
    """
    Generate the code to parse a reference to an instance.

    The code parses the ``value_expr`` into the ``target_expr``.

    :param value_expr: Go expression of the value
    :param target_expr: Go expression of where to store the parsed value
    :param ref_parts: Go expression of reference path segments to the value
    :param a_type: mapry definition of the value type
    :param registry_expr: Go expression of the registry of the class instances
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


_PARSE_EMBED_TPL = mapry.go.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{{ embed_name|ucamel_case }}FromJSONable(
    {{ value_expr|indent }},
    {% for registry_expr in selected_registry_exprs %}
    {{ registry_expr }},
    {% endfor %}
    strings.Join(
        []string{
            {{ ref_parts|join(', ') }}},
        "/"),
    &({{ target_expr }}),
    errors)
''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_embed(
        value_expr: str, target_expr: str, ref_parts: List[str],
        a_type: mapry.Embed, registry_exprs: Mapping[mapry.Class, str],
        auto_id: mapry.go.generate.AutoID, go: mapry.Go) -> str:
    """
    Generate the code to parse an embeddable structure.

    The code parses the ``value_expr`` into the ``target_expr``.

    :param value_expr: Go expression of the value
    :param target_expr: Go expression of where to store the parsed value
    :param ref_parts: Go expression of reference path segments to the value
    :param a_type: mapry definition of the value type
    :param registry_exprs:
        map class to Go expression of the registry of the class instances
    :param auto_id: generator of unique identifiers
    :param go: Go settings
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
        go=go)


_PARSE_COMPOSITE_TPL = mapry.go.jinja2_env.ENV.from_string(
    '''\
// {{ composite.name|ucamel_case }}FromJSONable parses {{
        composite.name|ucamel_case }} from a JSONable value.
//
// If there are any errors, the state of the target is undefined.
//
// {{ composite.name|ucamel_case }}FromJSONable requires:
//  * target != nil
//  * errors != nil
//  * errors.Empty()
func {{ composite.name|ucamel_case }}FromJSONable(
    value interface{},
    {% if is_class %}
    id string,
    {% endif %}
    {% for ref_cls in references %}
    {{ ref_cls.plural|camel_case }}Registry map[string]*{{
        ref_cls.name|ucamel_case }},
    {% endfor %}
    ref string,
    target *{{ composite.name|ucamel_case }},
    errors *Errors) {

    if target == nil {
        panic("unexpected nil target")
    }

    if errors == nil {
        panic("unexpected nil errors")
    }

    if !errors.Empty() {
        panic("unexpected non-empty errors")
    }

    {% if property_parsings %}
    cast, ok := value.(map[string]interface{})
    {% else %}
    _, ok := value.(map[string]interface{})
    {% endif %}{# /if property_parsings #}
    if !ok {
        errors.Add(
            ref,
            fmt.Sprintf(
                "expected a map[string]interface{}, but got: %T",
                value))
        return
    }
    {% if is_class %}

    target.ID = id
    {% endif %}
    {% for property_parsing in property_parsings %}

    {{ property_parsing|indent }}

    if errors.Full() {
        return
    }
    {% endfor %}{# /for property_parsing #}

    return
}
''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_composite(
        composite: Union[mapry.Class, mapry.Embed],
        pattern_uids: Mapping[Pattern[str], int], go: mapry.Go) -> str:
    """
    Generate the code of the function that parses a composite.

    :param composite: mapry definition of the composite
    :param pattern_uids: uniquely identified patterns
    :param go: Go settings
    :return: generated code
    """
    references = mapry.references(a_type=composite)

    # yapf: disable
    registry_exprs = {
        ref_cls: '{}Registry'.format(mapry.naming.camel_case(ref_cls.plural))
        for ref_cls in references
    }
    # yapf: enable

    auto_id = mapry.go.generate.AutoID()

    # yapf: disable
    property_parsings = [
        _parse_property(
            target_obj_expr="target",
            value_map_expr="cast",
            ref_obj_parts=["ref"],
            a_property=prop,
            registry_exprs=registry_exprs,
            pattern_uids=pattern_uids,
            auto_id=auto_id,
            go=go)
        for prop in composite.properties.values()
    ]
    # yapf: enable

    return _PARSE_COMPOSITE_TPL.render(
        composite=composite,
        is_class=isinstance(composite, mapry.Class),
        references=references,
        property_parsings=property_parsings,
        go=go)


_PARSE_GRAPH_TPL = mapry.go.jinja2_env.ENV.from_string(
    '''\
// {{ graph.name|ucamel_case }}FromJSONable parses {{
    graph.name|ucamel_case }} from a JSONable value.
//
// If there are any errors, the state of target is undefined.
//
// {{ graph.name|ucamel_case }}FromJSONable requires:
//  * target != nil
//  * errors != nil
//  * errors.Empty()
func {{ graph.name|ucamel_case }}FromJSONable(
    value interface{},
    ref string,
    target *{{ graph.name|ucamel_case }},
    errors *Errors) {

    if target == nil {
        panic("unexpected nil target")
    }

    if errors == nil {
        panic("unexpected nil errors")
    }

    if !errors.Empty() {
        panic("unexpected non-empty errors")
    }

    cast, ok := value.(map[string]interface{})
    if !ok {
        errors.Add(
            ref,
            fmt.Sprintf(
                "expected a map[string]interface{}, but got: %T",
                value))
        return
    }
    {% for cls in graph.classes.values() %}

    ////
    // Pre-allocate {{ cls.plural|ucamel_case }}
    ////

    {{ cls.plural|camel_case }}Ref := ref+{{ "/%s"|
        format(cls.plural|json_plural)|escaped_str }};
    var {{ cls.plural|camel_case }}Ok bool
    var {{ cls.plural|camel_case }}Value interface{}
    var {{ cls.plural|camel_case }}Map map[string]interface{}

    {{ cls.plural|camel_case }}Value, {{ cls.plural|camel_case }}Ok = cast[
        {{ cls.plural|json_plural|escaped_str }}]
    if {{ cls.plural|camel_case }}Ok {
        {{ cls.plural|camel_case }}Map, ok = {{
            cls.plural|camel_case }}Value.(map[string]interface{})
        if !ok {
            errors.Add(
                {{ cls.plural|camel_case }}Ref,
                fmt.Sprintf(
                    "expected a map[string]interface{}, but got: %T",
                    {{ cls.plural|camel_case }}Value));
        } else {
            target.{{ cls.plural|ucamel_case }} = make(
                map[string]*{{ cls.name|ucamel_case }})

            for id := range {{ cls.plural|camel_case }}Map {
                {% set preallocate_instance %}{#
                    #}target.{{ cls.plural|ucamel_case }}[id] = &{{
                        cls.name|ucamel_case }}{}{#
                #}{% endset %}
                {% if cls.id_pattern is not none %}
                if !pattern{{ pattern_uids[cls.id_pattern] }}.MatchString(id) {
                    errors.Add(
                        {{ cls.plural|camel_case }}Ref,
                        fmt.Sprintf(
                            {{ "expected ID to match %s, but got: %%s"|
                                format(cls.id_pattern.pattern)|escaped_str }},
                            id))
                } else {
                    {{ preallocate_instance|
                        indent|indent|indent|indent|indent }}
                }
                {% else %}
                {{ preallocate_instance|indent|indent|indent|indent }}
                {% endif %}{# /if cls.id_pattern is not none #}
            }
        }
    }
    {% endfor %}{# /for cls in graph.classes.values() #}
    {% if graph.classes %}

    // Pre-allocating class instances is critical.
    // If the pre-allocation failed, we can not continue to parse the instances.
    if !errors.Empty() {
        return
    }
    {% endif %}
    {% for cls in graph.classes.values() %}

    ////
    // Parse {{ cls.plural|ucamel_case }}
    ////

    if {{ cls.plural|camel_case }}Ok {
        for id, value := range {{ cls.plural|camel_case }}Map {
            {{ cls.name|ucamel_case }}FromJSONable(
                value,
                id,
                {% for ref_cls in references[cls] %}
                target.{{ ref_cls.plural|ucamel_case }},
                {% endfor %}
                strings.Join([]string{
                    {{ cls.plural|camel_case }}Ref, id}, "/"),
                target.{{ cls.plural|ucamel_case }}[id],
                errors)

            if errors.Full() {
                break
            }
        }
    }

    if errors.Full() {
        return
    }
    {% endfor %}{# /for cls in graph.classes.values() #}
    {% for property_parsing in property_parsings %}

    {{ property_parsing|indent }}

    if errors.Full() {
        return
    }
    {% endfor %}{# /for property_parsing #}

    return
}
''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_graph(
        graph: mapry.Graph, pattern_uids: Mapping[Pattern[str], int],
        go: mapry.Go) -> str:
    """
    Generate the code that parses an object graph.

    :param graph: definition of the object graph
    :param pattern_uids: uniquely identified patterns
    :param go: Go settings
    :return: generated code
    """
    # Map mapry class -> referenced mapry classes
    # yapf: disable
    references = {
        cls: mapry.references(a_type=cls)
        for cls in graph.classes.values()
    }
    # yapf: enable

    # Map mapry class -> Go expression of the instance registry
    # yapf: disable
    registry_exprs = {
        cls: 'target.{}'.format(mapry.naming.ucamel_case(identifier=cls.plural))
        for cls in graph.classes.values()
    }
    # yapf: disable

    # Gather property parsings in a list
    # so that they can be readily inserted in the template
    property_parsings = []  # type: List[str]

    auto_id = mapry.go.generate.AutoID()
    for prop in graph.properties.values():
        property_parsings.append(
            _parse_property(
                target_obj_expr="target",
                value_map_expr="cast",
                ref_obj_parts=["ref"],
                a_property=prop,
                registry_exprs=registry_exprs,
                pattern_uids=pattern_uids,
                auto_id=auto_id,
                go=go))

    text = _PARSE_GRAPH_TPL.render(
        graph=graph, package=go.package, references=references,
        pattern_uids=pattern_uids,
        property_parsings=property_parsings)

    return text.rstrip("\n")


@ensure(lambda result: result.endswith('\n'))
def generate(graph: mapry.Graph, go: mapry.Go) -> str:
    """
    Generate the source file to parse an object graph from a JSONable object.

    :param graph: mapry definition of the object graph
    :param go: Go settings
    :return: content of the source file
    """
    blocks = [
        'package {}'.format(go.package),
        mapry.go.generate.WARNING,
        _imports(graph=graph)
    ]

    if mapry.needs_type(a_type=graph, query=mapry.Duration):
        blocks.append(_duration_from_string())

    pattern_uids = _enumerate_patterns(graph=graph)
    if pattern_uids:
        blocks.append(_compile_regexes(pattern_uids=pattern_uids))

    nongraph_composites = []  # type: List[Union[mapry.Class, mapry.Embed]]
    nongraph_composites.extend(graph.classes.values())
    nongraph_composites.extend(graph.embeds.values())

    for class_or_embed in nongraph_composites:
        blocks.append(
            _parse_composite(
                composite=class_or_embed, pattern_uids=pattern_uids, go=go))

    blocks.append(_parse_graph(graph=graph, pattern_uids=pattern_uids, go=go))

    blocks.append(mapry.go.generate.WARNING)

    return mapry.indention.reindent(
        text='\n\n'.join(blocks) + '\n', indention='\t')
