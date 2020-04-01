"""Generate the implementation of de/serialization from/to Jsoncpp values."""

# pylint: disable=too-many-lines
# pylint: disable=too-many-arguments

import re
import textwrap
from typing import (  # pylint: disable=unused-import
    Dict, List, Mapping, MutableMapping, Set, Union)

import icontract
from icontract import ensure

import mapry
import mapry.cpp.generate
import mapry.cpp.jinja2_env
import mapry.cpp.naming
import mapry.indention


def _needs_regex(a_type: mapry.Type) -> bool:
    """
    Check if the type needs a regular expression.

    For example, types with pattern constraints need to verify the pattern
    with the regular expression.

    :param a_type: to be inspected
    :return: True if the type needs a regular expression
    """
    if isinstance(a_type, mapry.String) and a_type.pattern:
        return True

    if isinstance(a_type, mapry.Path) and a_type.pattern:
        return True

    if isinstance(a_type, mapry.Duration):
        return True

    return False


@ensure(lambda result: not result.endswith('\n'))
def _includes(
        graph: mapry.Graph, types_header_path: str, parse_header_path: str,
        jsoncpp_header_path: str, cpp: mapry.Cpp) -> str:
    """
    Generate the include directives of the implementation file.

    :param graph: mapry definition of the object graph
    :param types_header_path: defines the types of the object graph
    :param parse_header_path: defines the general parsing structures
    :param jsoncpp_header_path:
        defines parsing and serializing functions from/to Jsoncpp
    :param cpp: C++ settings
    :return: generated code
    """
    # yapf: disable
    first_party_block = {
        '#include "{}"'.format(pth)
        for pth in [types_header_path, parse_header_path, jsoncpp_header_path]}
    # yapf: enable

    third_party_block = set()  # type: Set[str]
    stl_block = {
        "#include <cstring>", "#include <string>", "#include <sstream>",
        '#include <stdexcept>', "#include <memory>", "#include <utility>"
    }

    ##
    # See if we need any regular expressions
    ##

    include_regex = False
    for a_type, _ in mapry.iterate_over_types(graph=graph):
        if _needs_regex(a_type=a_type):
            include_regex = True
            break

    for cls in graph.classes.values():
        if cls.id_pattern is not None:
            include_regex = True
            break

    if include_regex:
        stl_block.add("#include <regex>")

    ##
    # Date/time includes
    ##

    if cpp.datetime_library == 'ctime':
        # yapf: disable
        if any(mapry.needs_type(a_type=graph, query=query_type)
               for query_type in [mapry.Date, mapry.Time, mapry.Datetime]):
            # yapf: enable

            # needed at least for tm_to_string function
            stl_block.add("#include <cstring>")

    elif cpp.datetime_library == 'date.h':
        # yapf: disable
        if any(mapry.needs_type(a_type=graph, query=query_type)
               for query_type in [mapry.Date, mapry.Time, mapry.Datetime]):
            # yapf: enable

            # needed at least to parse the date.h date/times.
            stl_block.add("#include <sstream>")
            third_party_block.add("#include <date/date.h>")

        if mapry.needs_type(a_type=graph, query=mapry.TimeZone):
            third_party_block.add("#include <date/tz.h>")

    else:
        raise NotImplementedError(
            "Unhandled datetime library: {}".format(cpp.datetime_library))

    if mapry.needs_type(a_type=graph, query=mapry.Duration):
        # needed at least for duration_to_string function
        stl_block.add("#include <iomanip>")

        # needed at least for duration_from_string function
        stl_block.add("#include <limits>")
        stl_block.add("#include <cmath>")

    ##
    # Assemble
    ##

    # yapf: disable
    block_strs = (
            ['\n'.join(sorted(first_party_block))] +
            ['\n'.join(sorted(third_party_block))] +
            ['\n'.join(sorted(stl_block))])
    # yapf: enable

    return '\n\n'.join(
        [block_str for block_str in block_strs if block_str.strip()])


@ensure(lambda result: not result.endswith('\n'))
def _message_function() -> str:
    """
    Generate the function that joins strings for error messages.

    :return: generated code
    """
    return textwrap.dedent(
        '''\
        /**
         * generates an error message.
         *
         * @param cc char array as the description part of the message
         * @param cc_size size of the char array
         * @param s string as the detail part of the message
         * @return concatenated string
         */
        std::string message(const char* cc, size_t cc_size, std::string s) {
            std::string result;
            result.reserve(cc_size + s.size());
            result.append(cc, cc_size);
            result.append(s);
            return result;
        }''')


@ensure(lambda result: not result.endswith('\n'))
def _regex_constants(graph: mapry.Graph) -> str:
    """
    Generate the code to define regular expressions as constants.

    :param graph: mapry definition of the object graph
    :return: generated code
    """
    blocks = []  # type: List[str]

    # define regular expressions for duration
    if mapry.needs_type(a_type=graph, query=mapry.Duration):
        re_block = mapry.indention.reindent(
            '''\
            namespace re {
            const std::regex kDuration(
                "^(\\\\+|-)?P(((0|[1-9][0-9]*)(\\\\.[0-9]+)?)Y)?"
                "(((0|[1-9][0-9]*)(\\\\.[0-9]+)?)M)?"
                "(((0|[1-9][0-9]*)(\\\\.[0-9]+)?)W)?"
                "(((0|[1-9][0-9]*)(\\\\.[0-9]+)?)D)?"
                "(T"
                "(((0|[1-9][0-9]*)(\\\\.[0-9]+)?)H)?"
                "(((0|[1-9][0-9]*)(\\\\.[0-9]+)?)M)?"
                "(((0|[1-9][0-9]*)(\\\\.([0-9]+))?)S)?"
                ")?$");
            }  // namespace re''')

        blocks.append(re_block)

    for cls in graph.classes.values():
        if cls.id_pattern is None:
            continue

        blocks.append(
            textwrap.dedent(
                '''\
            namespace {composite_varname}_re {{
            const std::regex kID(
                R"v0g0n({regex})v0g0n");
            }}  // namespace {composite_varname}_re'''.format(
                    composite_varname=mapry.cpp.naming.as_variable(
                        identifier=cls.name),
                    regex=cls.id_pattern.pattern)))

    return "\n\n".join(blocks)


@ensure(lambda result: not result.endswith('\n'))
def _duration_from_string() -> str:
    """
    Generate the code for parsing durations from strings.

    :return: generated code
    """
    return textwrap.dedent(
        '''\
        /**
         * adds the left and the right and checks for the overflow.
         *
         * left and right are expected to be non-negative.
         *
         * @param[in] left summand
         * @param[in] right summand
         * @param[out] overflows true if the addition overflows
         * @return sum
         */
        template <typename rep_t>
        rep_t add_rep_double(rep_t left, double right, bool* overflows) {
            if (left < 0) {
                throw std::invalid_argument("Expected left >= 0");
            }

            if (right < 0) {
                throw std::invalid_argument("Expected right >= 0");
            }

            // 9223372036854775808 == 2^63, the first double that is
            // greater than max int64 (max int64 is 2^63 - 1).
            if (right >= 9223372036854775808.0) {
                *overflows = true;
                return 0;
            }

            const rep_t rightRep = right;

            if (rightRep > std::numeric_limits<rep_t>::max() - left) {
                *overflows = true;
                return 0;
            }

            return rightRep + left;
        }

        /**
         * parses the duration from a string.
         *
         *  Following STL chrono library, the following units are counted as:
         *   - years as 365.2425 days (the average length of a Gregorian year),
         *   - months as 30.436875 days (exactly 1/12 of years) and
         *   - weeks as 7 days.
         *
         * See https://en.cppreference.com/w/cpp/chrono/duration for details.
         *
         * @param[in] s string to parse
         * @param[out] error error message, if any
         * @return parsed duration
         */
        std::chrono::nanoseconds duration_from_string(
                const std::string& s,
                std::string* error) {
            std::smatch mtch;
            const bool matched = std::regex_match(s, mtch, re::kDuration);

            if (!matched) {
                std::stringstream sserr;
                sserr << "failed to match the duration: " << s;
                *error = sserr.str();
                return std::chrono::nanoseconds();
            }

            typedef std::chrono::nanoseconds::rep rep_t;

            ////
            // Extract nanoseconds
            ////

            const std::string nanoseconds_str = mtch[31];
            rep_t nanoseconds;
            if (nanoseconds_str.size() == 0) {
                // No nanoseconds specified
                nanoseconds = 0;
            } else if(nanoseconds_str.size() <= 9) {
                size_t first_nonzero = 0;
                for (; first_nonzero < nanoseconds_str.size();
                        ++first_nonzero) {
                    if (nanoseconds_str[first_nonzero] >= '0' and
                            nanoseconds_str[first_nonzero] <= '9') {
                        break;
                    }
                }

                if (first_nonzero == nanoseconds_str.size()) {
                    // No non-zero numbers, all zeros behind the seconds comma
                    nanoseconds = 0;
                } else {
                    const rep_t fraction_as_integer(
                        std::atol(&nanoseconds_str[first_nonzero]));

                    const size_t order = 9 - nanoseconds_str.size();
                    rep_t multiplier = 1;
                    for (size_t i = 0; i < order; ++i) {
                        multiplier *= 10;
                    }

                    nanoseconds = fraction_as_integer * multiplier;
                }
            } else {
                // Signal that the precision is lost
                std::stringstream sserr;
                sserr << "converting the duration to nanoseconds "
                    "results in loss of precision: " << s;
                *error = sserr.str();
                return std::chrono::nanoseconds();
            }

            ////
            // Extract all the other interval counts
            ////

            const std::string sign_str = mtch[1];
            const rep_t sign = (sign_str.empty() or sign_str == "+") ? 1 : -1;

            const double years(
                (mtch[3].length() == 0) ? 0.0 : std::stod(mtch[3]));
            const double months(
                (mtch[7].length() == 0) ? 0.0 : std::stod(mtch[7]));
            const double weeks(
                (mtch[11].length() == 0) ? 0.0 : std::stod(mtch[11]));
            const double days(
                (mtch[15].length() == 0) ? 0.0 : std::stod(mtch[15]));
            const double hours(
                (mtch[20].length() == 0) ? 0.0 : std::stod(mtch[20]));
            const double minutes(
                (mtch[24].length() == 0) ? 0.0 : std::stod(mtch[24]));
            const rep_t seconds(
                (mtch[29].length() == 0) ? 0 : std::stol(mtch[29]));

            ////
            // Sum
            ////

            rep_t sum = nanoseconds;

            const rep_t max_seconds(
                std::numeric_limits<rep_t>::max() / (1000L * 1000L * 1000L));
            if (seconds > max_seconds) {
                std::stringstream sserr;
                sserr << "seconds in duration overflow as nanoseconds: " << s;
                *error = sserr.str();
                return std::chrono::nanoseconds();
            }

            const rep_t seconds_as_ns = seconds * 1000L * 1000L * 1000L;
            if (sum > std::numeric_limits<rep_t>::max() - seconds_as_ns) {
                std::stringstream sserr;
                sserr << "duration overflow as nanoseconds: " << s;
                *error = sserr.str();
                return std::chrono::nanoseconds();
            }
            sum += seconds_as_ns;

            bool overflows;

            sum = add_rep_double(
                sum, minutes * 6e10, &overflows);
            if (overflows) {
                std::stringstream sserr;
                sserr << "duration overflows as nanoseconds: " << s;
                *error = sserr.str();
                return std::chrono::nanoseconds();
            }

            sum = add_rep_double(
                sum, hours * 3.6e12, &overflows);
            if (overflows) {
                std::stringstream sserr;
                sserr << "duration overflows as nanoseconds: " << s;
                *error = sserr.str();
                return std::chrono::nanoseconds();
            }

            sum = add_rep_double(
                sum, days * 24.0 * 3.6e12, &overflows);
            if (overflows) {
                std::stringstream sserr;
                sserr << "duration overflows as nanoseconds: " << s;
                *error = sserr.str();
                return std::chrono::nanoseconds();
            }

            sum = add_rep_double(
                sum, weeks * 7.0 * 24.0 * 3.6e12, &overflows);
            if (overflows) {
                std::stringstream sserr;
                sserr << "duration overflows as nanoseconds: " << s;
                *error = sserr.str();
                return std::chrono::nanoseconds();
            }

            sum = add_rep_double(
                sum, months * 30.436875 * 24.0 * 3.6e12, &overflows);
            if (overflows) {
                std::stringstream sserr;
                sserr << "duration overflows as nanoseconds: " << s;
                *error = sserr.str();
                return std::chrono::nanoseconds();
            }

            sum = add_rep_double(
                sum, years * 365.2425 * 24.0 * 3.6e12, &overflows);
            if (overflows) {
                std::stringstream sserr;
                sserr << "duration overflows as nanoseconds: " << s;
                *error = sserr.str();
                return std::chrono::nanoseconds();
            }

            // sum is always positive, so the multiplication by -1 can not
            // overflow since |max rep_t| < |min rep_t|
            if (sign < 0) {
                sum = -sum;
            }

            return std::chrono::nanoseconds(sum);
        }''')


@ensure(lambda result: not result.endswith('\n'))
def _value_type_to_string() -> str:
    """
    Generate the function to convert Json::ValueType to a string.

    :return: generated code
    """
    return textwrap.dedent(
        '''\
        /**
         * converts a JSON value type to a human-readable string representation.
         *
         * @param value_type to be converted
         * @return string representation of the JSON value type
         */
        std::string value_type_to_string(Json::ValueType value_type) {
            switch (value_type) {
                case Json::ValueType::nullValue: return "null";
                case Json::ValueType::intValue: return "int";
                case Json::ValueType::uintValue: return "uint";
                case Json::ValueType::realValue: return "real";
                case Json::ValueType::stringValue: return "string";
                case Json::ValueType::booleanValue: return "bool";
                case Json::ValueType::arrayValue: return "array";
                case Json::ValueType::objectValue: return "object";
                default:
                    std::stringstream ss;
                    ss << "Unhandled value type in value_to_string: "
                        << value_type;
                    throw std::domain_error(ss.str());
            }
        }''')


class _AutoID:
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


_PARSE_BOOLEAN_TPL = mapry.cpp.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{% if value_expr|is_variable %}
{# short-circuit value as value expression if it is a variable so that
we don't end up with an unnecessary variable1 = variable2 statement.#}
{% set value = value_expr %}
{% else %}
{% set value = "value_%s"|format(uid) %}
const Json::Value& value_{{ uid }} = {{ value_expr }};
{% endif %}
if (!{{ value }}.isBool()) {
    constexpr auto expected_but_got(
        "Expected a bool, but got: ");

    errors->add(
        {{ ref_parts|join_strings|indent|indent }},
        message(
            expected_but_got,
            strlen(expected_but_got),
            value_type_to_string(
                {{ value }}.type())));
} else {
    {{ target_expr }} = {{ value }}.asBool();
}''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_boolean(
        value_expr: str, target_expr: str, ref_parts: List[str],
        auto_id: _AutoID) -> str:
    """
    Generate the code to parse a boolean.

    The code parses the ``value_expr`` into the ``target_expr``.

    :param value_expr: C++ expression of the JSON value
    :param target_expr: C++ expression of where to store the parsed value
    :param ref_parts: C++ expression of reference path segments to the value
    :param auto_id: generator of unique identifiers
    :return: C++ code
    """
    uid = auto_id.next_identifier()

    return _PARSE_BOOLEAN_TPL.render(
        uid=uid,
        value_expr=value_expr,
        ref_parts=ref_parts,
        target_expr=target_expr)


_PARSE_INTEGER_TPL = mapry.cpp.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{% if value_expr|is_variable %}
{# Short-circuit value as value expression if it is a variable so that
we don't end up with an unnecessary variable1 = variable2 statement.#}
{% set value = value_expr %}
{% else %}
{% set value = "value_%s"|format(uid) %}
const Json::Value& value_{{ uid }} = {{ value_expr }};
{% endif %}{# /value_expr|is_variable #}
if (!{{ value }}.isInt64()) {
    constexpr auto expected_but_got(
        "Expected an int64, but got: ");

    errors->add(
        {{ ref_parts|join_strings|indent|indent }},
        message(
            expected_but_got,
            strlen(expected_but_got),
            value_type_to_string(
                {{ value }}.type())));
} else {
    {% if a_type.minimum is none and a_type.maximum is none %}
    {{ target_expr }} = {{ value }}.asInt64();
    {% else %}
    const auto cast_{{ uid }} = {{ value }}.asInt64();
    bool ok_{{ uid }} = true;
    {% if a_type.minimum is not none %}

    {% set op = ">" if a_type.exclusive_minimum else ">="  %}
    if (!(cast_{{ uid }} {{ op }} {{ a_type.minimum }})) {
        constexpr auto expected_but_got(
            "Expected "
            {{ "%s %d"|format(op, a_type.minimum)|escaped_str }}
            ", but got: ");

        errors->add(
            {{ ref_parts|join_strings|indent|indent|indent }},
            message(
                expected_but_got,
                strlen(expected_but_got),
                std::to_string(cast_{{ uid }})));
        ok_{{ uid }} = false;
    }
    {% endif %}
    {% if a_type.maximum is not none %}

    {% set op = "<" if a_type.exclusive_maximum else "<=" %}
    if (!(cast_{{ uid }} {{ op }} {{ a_type.maximum }})) {
        constexpr auto expected_but_got(
            "Expected "
            {{ "%s %d"|format(op, a_type.maximum)|escaped_str }}
            ", but got: ");

        errors->add(
            {{ ref_parts|join_strings|indent|indent|indent }},
            message(
                expected_but_got,
                strlen(expected_but_got),
                std::to_string(cast_{{ uid }})));
        ok_{{ uid }} = false;
    }
    {% endif %}

    if (ok_{{ uid }}) {
        {{ target_expr }} = cast_{{ uid }};
    }
    {% endif %}{# /if a_type.minimum is none and a_type.maximum is none #}
}
''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_integer(
        value_expr: str, target_expr: str, ref_parts: List[str],
        a_type: mapry.Integer, auto_id: _AutoID) -> str:
    """
    Generate the code to parse an integer.

    The code parses the ``value_expr`` into the ``target_expr``.

    :param value_expr: C++ expression of the JSON value
    :param target_expr: C++ expression of where to store the parsed value
    :param ref_parts: C++ expression of reference path segments to the value
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


_PARSE_FLOAT_TPL = mapry.cpp.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{% if value_expr|is_variable %}
{# Short-circuit value as value expression if it is a variable so that
we don't end up with an unnecessary variable1 = variable2 statement.#}
{% set value = value_expr %}
{% else %}
{% set value = "value_%s"|format(uid) %}
const Json::Value& value_{{ uid }} = {{ value_expr }};
{% endif %}
if (!{{ value }}.isDouble()) {
    constexpr auto expected_but_got(
        "Expected a double, but got: ");

    errors->add(
        {{ ref_parts|join_strings|indent|indent }},
        message(
            expected_but_got,
            strlen(expected_but_got),
            value_type_to_string(
                {{ value }}.type())));
} else {
    {% if a_type.minimum is none and a_type.maximum is none %}
    {{ target_expr }} = {{ value }}.asDouble();
    {% else %}
    const auto cast_{{ uid }} = {{ value }}.asDouble();
    bool ok_{{ uid }} = true;
    {% if a_type.minimum is not none %}

    {% set op = ">" if a_type.exclusive_minimum else ">="  %}
    if (!(cast_{{ uid }} {{ op }} {{ a_type.minimum }})) {
        constexpr auto expected_but_got(
            "Expected "
            {{ "%s %f"|format(op, a_type.minimum)|escaped_str }}
            ", but got: ");

        errors->add(
            {{ ref_parts|join_strings|indent|indent|indent }},
            message(
                expected_but_got,
                strlen(expected_but_got),
                std::to_string(cast_{{ uid }})));
        ok_{{ uid }} = false;
    }
    {% endif %}{# /if a_type.minimum is not none #}
    {% if a_type.maximum is not none %}

    {% set op = "<" if a_type.exclusive_maximum else "<=" %}
    if (!(cast_{{ uid }} {{ op }} {{ a_type.maximum }})) {
        constexpr auto expected_but_got(
            "Expected "
            {{ "%s %f"|format(op, a_type.maximum)|escaped_str }}
            ", but got: ");

        errors->add(
            {{ ref_parts|join_strings|indent|indent|indent }},
            message(
                expected_but_got,
                strlen(expected_but_got),
                std::to_string(cast_{{ uid }})));
        ok_{{ uid }} = false;
    }
    {% endif %}{# /if a_type.maximum is not none #}

    if (ok_{{ uid }}) {
        {{ target_expr }} = cast_{{ uid }};
    }
    {% endif %}{# /if a_type.minimum is none and a_type.maximum is none #}
}''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_float(
        value_expr: str, target_expr: str, ref_parts: List[str],
        a_type: mapry.Float, auto_id: _AutoID) -> str:
    """
    Generate the code to parse a floating-point number.

    The code parses the ``value_expr`` into the ``target_expr``.

    :param value_expr: C++ expression of the JSON value
    :param target_expr: C++ expression of where to store the parsed value
    :param ref_parts: C++ expression of reference path segments to the value
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


_PARSE_STRING_TPL = mapry.cpp.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{% if value_expr|is_variable %}
{# Short-circuit value as value expression if it is a variable so that
we don't end up with an unnecessary variable1 = variable2 statement.#}
{% set value = value_expr %}
{% else %}
{% set value = "value_%s"|format(uid) %}
const Json::Value& value_{{ uid }} = {{ value_expr }};
{% endif %}
if (!{{ value }}.isString()) {
    constexpr auto expected_but_got(
        "Expected a string, but got: ");

    errors->add(
        {{ ref_parts|join_strings|indent|indent }},
        message(
            expected_but_got,
            strlen(expected_but_got),
            value_type_to_string(
                {{ value }}.type())));
} else {
    {% if a_type.pattern is none %}
    {{ target_expr }} = {{ value }}.asString();
    {% else %}
    const static std::regex regex_{{ uid }}(
        R"v0g0n({{ a_type.pattern.pattern }})v0g0n");
    const std::string cast_{{ uid }} = {{ value }}.asString();
    bool ok_{{ uid }} = true;

    if (!std::regex_match(cast_{{ uid }}, regex_{{ uid }})) {
        constexpr auto expected_but_got(
            "Expected to match "
            {{ a_type.pattern.pattern|escaped_str }}
            ", but got: ");

        errors->add(
            {{ ref_parts|join_strings|indent|indent|indent }},
            message(
                expected_but_got,
                strlen(expected_but_got),
                cast_{{ uid }}));
        ok_{{ uid }} = false;
    }

    if (ok_{{ uid }}) {
        {{ target_expr }} = cast_{{ uid }};
    }
    {% endif %}{# /if a_type.pattern is none #}
}''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_string(
        value_expr: str, target_expr: str, ref_parts: List[str],
        a_type: mapry.String, auto_id: _AutoID) -> str:
    """
    Generate the code to parse a string.

    The code parses the ``value_expr`` into the ``target_expr``.

    :param value_expr: C++ expression of the JSON value
    :param target_expr: C++ expression of where to store the parsed value
    :param ref_parts: C++ expression of reference path segments to the value
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


_PARSE_PATH_TPL = mapry.cpp.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{% if value_expr|is_variable %}
{# Short-circuit value as value expression if it is a variable so that
we don't end up with an unnecessary variable1 = variable2 statement.#}
{% set value = value_expr %}
{% else %}
{% set value = "value_%s"|format(uid) %}
const Json::Value& value_{{ uid }} = {{ value_expr }};
{% endif %}
if (!{{ value }}.isString()) {
    constexpr auto expected_but_got(
        "Expected a string, but got: ");

    errors->add(
        {{ ref_parts|join_strings|indent|indent }},
        message(
            expected_but_got,
            strlen(expected_but_got),
            value_type_to_string(
                {{ value }}.type())));
} else {
    {% set set_target %}
    {% if cpp.path_as == "std::filesystem::path" %}
    {{ target_expr }} = std::filesystem::path(
        {{ value }}.asString());
    {% elif cpp.path_as == "boost::filesystem::path" %}
    {{ target_expr }} = boost::filesystem::path(
        {{ value }}.asString());
    {% else %}
    {{ _raise("Unhandled cpp.path_as: %s"|format(cpp.path_as)) }}
    {% endif %}
    {% endset %}{#

    #}
    {% if a_type.pattern is none %}
    {{ set_target }}
    {% else %}
    const static std::regex regex(
        R"v0g0n({{ a_type.pattern.pattern }})v0g0n");
    const std::string cast_{{ uid }} = {{ value }}.asString();
    bool ok_{{ uid }} = true;

    if (!std::regex_match(cast_{{ uid }}, regex)) {
        constexpr auto expected_but_got(
            "Expected to match "
            {{ a_type.pattern.pattern|escaped_str }}
            ", but got: ");

        errors->add(
            {{ ref_parts|join_strings|indent|indent|indent }},
            message(
                expected_but_got,
                strlen(expected_but_got),
                cast_{{ uid }}));
        ok_{{ uid }} = false;
    }

    if (ok_{{ uid }}) {
        {{ set_target|indent }}
    }
    {% endif %}{# /if a_type.pattern is none #}
}''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_path(
        value_expr: str, target_expr: str, ref_parts: List[str],
        a_type: mapry.Path, auto_id: _AutoID, cpp: mapry.Cpp) -> str:
    """
    Generate the code to parse a path.

    The code parses the ``value_expr`` into the ``target_expr``.

    :param value_expr: C++ expression of the JSON value
    :param target_expr: C++ expression of where to store the parsed value
    :param ref_parts: C++ expression of reference path segments to the value
    :param a_type: mapry definition of the value type
    :param auto_id: generator of unique identifiers
    :param cpp: C++ settings
    :return: generated code
    """
    uid = auto_id.next_identifier()

    return _PARSE_PATH_TPL.render(
        uid=uid,
        value_expr=value_expr,
        ref_parts=ref_parts,
        target_expr=target_expr,
        a_type=a_type,
        cpp=cpp).rstrip("\n")


_PARSE_CTIME_TPL = mapry.cpp.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{% if value_expr|is_variable %}
{# Short-circuit value as value expression if it is a variable so that
we don't end up with an unnecessary variable1 = variable2 statement.#}
{% set value = value_expr %}
{% else %}
{% set value = "value_%s"|format(uid) %}
const Json::Value& value_{{ uid }} = {{ value_expr }};
{% endif %}
if (!{{ value }}.isString()) {
    constexpr auto expected_but_got(
        "Expected a string, but got: ");

    errors->add(
        {{ ref_parts|join_strings|indent|indent }},
        message(
            expected_but_got,
            strlen(expected_but_got),
            value_type_to_string(
                {{ value }}.type())));
} else {
    const std::string cast_{{ uid }} = {{ value }}.asString();
    struct tm tm_{{ uid }} = tm{0};
    char* ret_{{ uid }} = strptime(
        cast_{{ uid }}.c_str(),
        {{ a_type.format|escaped_str }},
        &tm_{{ uid }});

    if (ret_{{ uid }} == nullptr or *ret_{{ uid }} != '\\0') {
        constexpr auto expected_but_got(
            "Expected to strptime "
            {{ a_type.format|escaped_str }}
            ", but got: ");

        errors->add(
            {{ ref_parts|join_strings|indent|indent|indent }},
            message(
                expected_but_got,
                strlen(expected_but_got),
                cast_{{ uid }}));
    } else {
        {{ target_expr }} = tm_{{ uid }};
    }
}''')

_PARSE_DATE_TPL = mapry.cpp.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{% if value_expr|is_variable %}
{# Short-circuit value as value expression if it is a variable so that
we don't end up with an unnecessary variable1 = variable2 statement.#}
{% set value = value_expr %}
{% else %}
{% set value = "value_%s"|format(uid) %}
const Json::Value& value_{{ uid }} = {{ value_expr }};
{% endif %}
if (!{{ value }}.isString()) {
    constexpr auto expected_but_got(
        "Expected a string, but got: ");

    errors->add(
        {{ ref_parts|join_strings|indent|indent }},
        message(
            expected_but_got,
            strlen(expected_but_got),
            value_type_to_string(
                {{ value }}.type())));
} else {
    std::istringstream iss_{{ uid }}(
        {{ value }}.asString());
    iss_{{ uid }} >>
        date::parse(
            {{ a_type.format|escaped_str }},
            {{ target_expr }} );

    if (iss_{{ uid }}.fail()) {
        constexpr auto expected_but_got(
            "Expected to date::parse "
            {{ a_type.format|escaped_str }}
            ", but got: ");

        errors->add(
            {{ ref_parts|join_strings|indent|indent|indent }},
            message(
                expected_but_got,
                strlen(expected_but_got),
                {{ value }}.asString()));
    }
}''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_date(
        value_expr: str, target_expr: str, ref_parts: List[str],
        a_type: mapry.Date, auto_id: _AutoID, cpp: mapry.Cpp) -> str:
    """
    Generate the code to parse a date.

    The code parses the ``value_expr`` into the ``target_expr``.

    :param value_expr: C++ expression of the JSON value
    :param target_expr: C++ expression of where to store the parsed value
    :param ref_parts: C++ expression of reference path segments to the value
    :param a_type: mapry definition of the value type
    :param auto_id: generator of unique identifiers
    :param cpp: C++ settings
    :return: generated code
    """
    uid = auto_id.next_identifier()

    if cpp.datetime_library == 'ctime':
        return _PARSE_CTIME_TPL.render(
            uid=uid,
            value_expr=value_expr,
            ref_parts=ref_parts,
            target_expr=target_expr,
            a_type=a_type).rstrip("\n")

    if cpp.datetime_library == 'date.h':
        return _PARSE_DATE_TPL.render(
            uid=uid,
            value_expr=value_expr,
            ref_parts=ref_parts,
            target_expr=target_expr,
            a_type=a_type).rstrip("\n")

    raise NotImplementedError(
        "Unhnadled datetime library: {}".format(cpp.datetime_library))


@ensure(lambda result: not result.endswith('\n'))
def _parse_date_time(
        value_expr: str, target_expr: str, ref_parts: List[str],
        a_type: mapry.Datetime, auto_id: _AutoID, cpp: mapry.Cpp) -> str:
    """
    Generate the code to parse a date-time.

    The code parses the ``value_expr`` into the ``target_expr``.

    :param value_expr: C++ expression of the JSON value
    :param target_expr: C++ expression of where to store the parsed value
    :param ref_parts: C++ expression of reference path segments to the value
    :param a_type: mapry definition of the value type
    :param auto_id: generator of unique identifiers
    :param cpp: C++ settings
    :return: generated code
    """
    uid = auto_id.next_identifier()

    if cpp.datetime_library == 'ctime':
        return _PARSE_CTIME_TPL.render(
            uid=uid,
            value_expr=value_expr,
            ref_parts=ref_parts,
            target_expr=target_expr,
            a_type=a_type).rstrip("\n")

    if cpp.datetime_library == 'date.h':
        return _PARSE_DATE_TPL.render(
            uid=uid,
            value_expr=value_expr,
            ref_parts=ref_parts,
            target_expr=target_expr,
            a_type=a_type).rstrip("\n")

    raise NotImplementedError(
        "Unhnadled datetime library: {}".format(cpp.datetime_library))


_PARSE_TIME_OF_DAY_TPL = mapry.cpp.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{% if value_expr|is_variable %}
{# Short-circuit value as value expression if it is a variable so that
we don't end up with an unnecessary variable1 = variable2 statement.#}
{% set value = value_expr %}
{% else %}
{% set value = "value_%s"|format(uid) %}
const Json::Value& value_{{ uid }} = {{ value_expr }};
{% endif %}
if (!{{ value }}.isString()) {
    constexpr auto expected_but_got(
        "Expected a string, but got: ");

    errors->add(
        {{ ref_parts|join_strings|indent|indent }},
        message(
            expected_but_got,
            strlen(expected_but_got),
            value_type_to_string(
                {{ value }}.type())));
} else {
    std::chrono::seconds seconds_of_day_{{ uid }};
    std::istringstream iss_{{ uid }}(
        {{ value }}.asString());
    iss_{{ uid }} >>
        date::parse(
            {{ a_type.format|escaped_str }},
            seconds_of_day_{{ uid }} );

    if (iss_{{ uid }}.fail()) {
        constexpr auto expected_but_got(
            "Expected to date::parse "
            {{ a_type.format|escaped_str }}
            ", but got: ");

        errors->add(
            {{ ref_parts|join_strings|indent|indent|indent }},
            message(
                expected_but_got,
                strlen(expected_but_got),
                {{ value }}.asString()));
    } else {
        {{ target_expr }} = date::make_time(
            seconds_of_day_{{ uid }});
    }
}''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_time(
        value_expr: str, target_expr: str, ref_parts: List[str],
        a_type: mapry.Time, auto_id: _AutoID, cpp: mapry.Cpp) -> str:
    """
    Generate the code to parse a time.

    The code parses the ``value_expr`` into the ``target_expr``.

    :param value_expr: C++ expression of the JSON value
    :param target_expr: C++ expression of where to store the parsed value
    :param ref_parts: C++ expression of reference path segments to the value
    :param a_type: mapry definition of the value type
    :param auto_id: generator of unique identifiers
    :param cpp: C++ settings
    :return: generated code
    """
    uid = auto_id.next_identifier()

    if cpp.datetime_library == 'ctime':
        return _PARSE_CTIME_TPL.render(
            uid=uid,
            value_expr=value_expr,
            ref_parts=ref_parts,
            target_expr=target_expr,
            a_type=a_type).rstrip("\n")

    elif cpp.datetime_library == 'date.h':
        return _PARSE_TIME_OF_DAY_TPL.render(
            uid=uid,
            value_expr=value_expr,
            ref_parts=ref_parts,
            target_expr=target_expr,
            a_type=a_type).rstrip("\n")

    else:
        raise NotImplementedError(
            "Unhnadled datetime library: {}".format(cpp.datetime_library))


_PARSE_TIME_ZONE_AS_STR_TPL = mapry.cpp.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{% if value_expr|is_variable %}
{# Short-circuit value as value expression if it is a variable so that
we don't end up with an unnecessary variable1 = variable2 statement.#}
{% set value = value_expr %}
{% else %}
{% set value = "value_%s"|format(uid) %}
const Json::Value& value_{{ uid }} = {{ value_expr }};
{% endif %}
if (!{{ value }}.isString()) {
    constexpr auto expected_but_got(
        "Expected a string, but got: ");

    errors->add(
        {{ ref_parts|join_strings|indent|indent }},
        message(
            expected_but_got,
            strlen(expected_but_got),
            value_type_to_string(
                {{ value }}.type())));
} else {
    {{ target_expr }} = {{ value }}.asString();
}''')

_PARSE_TIME_ZONE_TPL = mapry.cpp.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{% if value_expr|is_variable %}
{# Short-circuit value as value expression if it is a variable so that
we don't end up with an unnecessary variable1 = variable2 statement.#}
{% set value = value_expr %}
{% else %}
{% set value = "value_%s"|format(uid) %}
const Json::Value& value_{{ uid }} = {{ value_expr }};
{% endif %}
if (!{{ value }}.isString()) {
    constexpr auto expected_but_got(
        "Expected a string, but got: ");

    errors->add(
        {{ ref_parts|join_strings|indent|indent }},
        message(
            expected_but_got,
            strlen(expected_but_got),
            value_type_to_string(
                {{ value }}.type())));
} else {
    const std::string cast_{{ uid }} = {{ value }}.asString();
    try {
        {{ target_expr }} = date::locate_zone(
            cast_{{ uid }});
    } catch(const std::runtime_error& e) {
        constexpr auto expected_but_got(
            "Expected a valid IANA time zone, but got: ");

        errors->add(
            {{ ref_parts|join_strings|indent|indent|indent }},
            message(
                expected_but_got,
                strlen(expected_but_got),
                cast_{{ uid }}));
    }
}''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_time_zone(
        value_expr: str, target_expr: str, ref_parts: List[str],
        a_type: mapry.TimeZone, auto_id: _AutoID, cpp: mapry.Cpp) -> str:
    """
    Generate the code to parse a time zone.

    The code parses the ``value_expr`` into the ``target_expr``.

    :param value_expr: C++ expression of the JSON value
    :param target_expr: C++ expression of where to store the parsed value
    :param ref_parts: C++ expression of reference path segments to the value
    :param a_type: mapry definition of the value type
    :param auto_id: generator of unique identifiers
    :param cpp: C++ settings
    :return: generated code
    """
    uid = auto_id.next_identifier()

    if cpp.datetime_library == 'ctime':
        return _PARSE_TIME_ZONE_AS_STR_TPL.render(
            uid=uid,
            value_expr=value_expr,
            ref_parts=ref_parts,
            target_expr=target_expr,
            a_type=a_type).rstrip("\n")

    if cpp.datetime_library == 'date.h':
        return _PARSE_TIME_ZONE_TPL.render(
            uid=uid,
            value_expr=value_expr,
            ref_parts=ref_parts,
            target_expr=target_expr,
            a_type=a_type).rstrip("\n")

    raise NotImplementedError(
        "Unhandled datetime library: {}".format(cpp.datetime_library))


_PARSE_DURATION_TPL = mapry.cpp.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{% if value_expr|is_variable %}
{# Short-circuit value as value expression if it is a variable so that
we don't end up with an unnecessary variable1 = variable2 statement.#}
{% set value = value_expr %}
{% else %}
{% set value = "value_%s"|format(uid) %}
const Json::Value& value_{{ uid }} = {{ value_expr }};
{% endif %}
if (!{{ value }}.isString()) {
    constexpr auto expected_but_got(
        "Expected a string, but got: ");

    errors->add(
        {{ ref_parts|join_strings|indent|indent }},
        message(
            expected_but_got,
            strlen(expected_but_got),
            value_type_to_string(
                {{ value }}.type())));
} else {
    const std::string cast_{{ uid }}_str = {{ value }}.asString();
    std::string error_{{ uid }};
    std::chrono::nanoseconds cast_{{ uid }} = duration_from_string(
        cast_{{ uid }}_str, &error_{{ uid }});

    if (!error_{{ uid }}.empty()) {
        constexpr auto invalid_duration(
            "Invalid duration: ");

        errors->add(
            {{ ref_parts|join_strings|indent|indent|indent }},
            message(
                invalid_duration,
                strlen(invalid_duration),
                error_{{ uid }}));
    } else {
        {{ target_expr }} = cast_{{ uid }};
    }
}''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_duration(
        value_expr: str, target_expr: str, ref_parts: List[str],
        a_type: mapry.Duration, auto_id: _AutoID) -> str:
    """
    Generate the code to parse a duration.

    The code parses the ``value_expr`` into the ``target_expr``.

    :param value_expr: C++ expression of the JSON value
    :param target_expr: C++ expression of where to store the parsed value
    :param ref_parts: C++ expression of reference path segments to the value
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


_PARSE_ARRAY_TPL = mapry.cpp.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{% if value_expr|is_variable %}{## set value expression ##}
{# Short-circuit value as value expression if it is a variable so that
we don't end up with an unnecessary variable1 = variable2 statement.#}
{% set value = value_expr %}
{% else %}
{% set value = "value_%s"|format(uid) %}
const Json::Value& value_{{ uid }} = {{ value_expr }};
{% endif %}
{% set set_target %}{## set target block ##}
{{ target_cpp_type }}& target_{{ uid }} = {{ target_expr }};
target_{{ uid }}.resize({{ value }}.size());
size_t i_{{ uid }} = 0;
for (const Json::Value& item_{{ uid }} : {{ value }}) {
    {{ item_parsing|indent }}
    ++i_{{ uid }};

    if (errors->full()) {
        break;
    }
}
{% endset %}
if (!{{ value }}.isArray()) {
    constexpr auto expected_but_got(
        "Expected an array, but got: ");

    errors->add(
        {{ ref_parts|join_strings|indent|indent }},
        message(
            expected_but_got,
            strlen(expected_but_got),
            value_type_to_string(
                {{ value }}.type())));
{% if minimum_size is not none %}
} else if ({{ value }}.size() < {{ minimum_size }}) {
    constexpr auto expected_but_got(
        "Expected an array of minimum size "
        {{ "%d"|format(minimum_size)|escaped_str }}
        ", but got: ");

    errors->add(
        {{ ref_parts|join_strings|indent|indent }},
        message(
            expected_but_got,
            strlen(expected_but_got),
            std::to_string({{ value }}.size())));
{% endif %}{# /if minimum_size is not none #}
{% if maximum_size is not none %}
} else if ({{ value }}.size() > {{ maximum_size }}) {
    constexpr auto expected_but_got(
        "Expected an array of maximum size "
        {{ "%d"|format(maximum_size)|escaped_str }}
        ", but got: ");

    errors->add(
        {{ ref_parts|join_strings|indent|indent }},
        message(
            expected_but_got,
            strlen(expected_but_got),
            std::to_string({{ value }}.size())));
{% endif %}{# /if maximum_size is not none #}
} else {
    {{ set_target|indent }}
}''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_array(
        value_expr: str, target_expr: str, ref_parts: List[str],
        a_type: mapry.Array, registry_exprs: Mapping[mapry.Class, str],
        auto_id: _AutoID, cpp: mapry.Cpp) -> str:
    """
    Generate the code to parse an array.

    The code parses the ``value_expr`` into the ``target_expr``.

    :param value_expr: C++ expression of the JSON value
    :param target_expr: C++ expression of where to store the parsed value
    :param ref_parts: C++ expression of reference path segments to the value
    :param a_type: mapry definition of the value type
    :param registry_exprs:
        map class to C++ expression of the registry of the class instances
    :param auto_id: generator of unique identifiers
    :param cpp: C++ settings
    :return: generated code
    """
    uid = auto_id.next_identifier()

    item_parsing = _parse_value(
        value_expr="item_{uid}".format(uid=uid),
        target_expr="target_{uid}.at(i_{uid})".format(uid=uid),
        ref_parts=ref_parts +
        ['"/"', 'std::to_string(i_{uid})'.format(uid=uid)],
        a_type=a_type.values,
        registry_exprs=registry_exprs,
        auto_id=auto_id,
        cpp=cpp)

    return _PARSE_ARRAY_TPL.render(
        value_expr=value_expr,
        target_expr=target_expr,
        ref_parts=ref_parts,
        uid=uid,
        minimum_size=a_type.minimum_size,
        maximum_size=a_type.maximum_size,
        target_cpp_type=mapry.cpp.generate.type_repr(a_type=a_type, cpp=cpp),
        item_parsing=item_parsing)


_PARSE_MAP_TPL = mapry.cpp.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{% if value_expr|is_variable %}
{# Short-circuit value as value expression if it is a variable so that
we don't end up with an unnecessary variable1 = variable2 statement.#}
{% set value = value_expr %}
{% else %}
{% set value = "value_%s"|format(uid) %}
const Json::Value& value_{{ uid }} = {{ value_expr }};
{% endif %}
if (!{{ value }}.isObject()) {
    constexpr auto expected_but_got(
        "Expected an object, but got: ");

    errors->add(
        {{ ref_parts|join_strings|indent|indent }},
        message(
            expected_but_got,
            strlen(expected_but_got),
            value_type_to_string(
                {{ value }}.type())));
} else {
    {{ target_cpp_type }}& target_{{ uid }} = {{ target_expr }};
    for (Json::ValueConstIterator it_{{ uid }} = {{ value }}.begin(); {#
        #}it_{{ uid }} != {{ value }}.end(); {#
        #}++it_{{ uid }}) {
        {{ item_parsing|indent|indent }}

        if (errors->full()) {
            break;
        }
    }
}''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_map(
        value_expr: str, target_expr: str, ref_parts: List[str],
        a_type: mapry.Map, registry_exprs: Mapping[mapry.Class, str],
        auto_id: _AutoID, cpp: mapry.Cpp) -> str:
    """
    Generate the code to parse a map.

    The code parses the ``value_expr`` into the ``target_expr``.

    :param value_expr: C++ expression of the JSON value
    :param target_expr: C++ expression of where to store the parsed value
    :param ref_parts: C++ expression of reference path segments to the value
    :param a_type: mapry definition of the value type
    :param registry_exprs:
        map class to C++ expression of the registry of the class instances
    :param auto_id: generator of unique identifiers
    :param cpp: C++ settings
    :return: generated code
    """
    uid = auto_id.next_identifier()

    item_parsing = _parse_value(
        value_expr="*it_{uid}".format(uid=uid),
        target_expr="target_{uid}[it_{uid}.name()]".format(uid=uid),
        ref_parts=ref_parts + ['"/"', 'it_{uid}.name()'.format(uid=uid)],
        a_type=a_type.values,
        registry_exprs=registry_exprs,
        auto_id=auto_id,
        cpp=cpp)

    return _PARSE_MAP_TPL.render(
        value_expr=value_expr,
        target_expr=target_expr,
        ref_parts=ref_parts,
        uid=uid,
        target_cpp_type=mapry.cpp.generate.type_repr(a_type=a_type, cpp=cpp),
        item_parsing=item_parsing)


_PARSE_CLASS_REF_TPL = mapry.cpp.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{% if value_expr|is_variable %}
{# Short-circuit value as value expression if it is a variable so that
we don't end up with an unnecessary variable1 = variable2 statement.#}
{% set value = value_expr %}
{% else %}
{% set value = "value_%s"|format(uid) %}
const Json::Value& value_{{ uid }} = {{ value_expr }};
{% endif %}
if (!{{ value }}.isString()) {
    constexpr auto expected_but_got(
        "Expected a string, but got: ");

    errors->add(
        {{ ref_parts|join_strings|indent|indent }},
        message(
            expected_but_got,
            strlen(expected_but_got),
            value_type_to_string(
                {{ value }}.type())));
} else {
    const std::string& cast_{{ uid }} = {{ value }}.asString();
    if ({{ registry_expr }}.count(cast_{{ uid }}) == 0) {
        constexpr auto reference_not_found(
            "Reference to an instance of class "
            {{ class_name|escaped_str }}
            " not found: ");

        errors->add(
            {{ ref_parts|join_strings|indent|indent|indent }},
            message(
                reference_not_found,
                strlen(reference_not_found),
                cast_{{ uid }}));
    } else {
        {{ target_expr }} = {{ registry_expr }}.at(cast_{{ uid }}).get();
    }
}''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_instance_reference(
        value_expr: str, target_expr: str, ref_parts: List[str],
        a_type: mapry.Class, registry_expr: str, auto_id: _AutoID) -> str:
    """
    Generate the code to parse a reference to an instance of a class.

    The code parses the ``value_expr`` into the ``target_expr``.

    :param value_expr: C++ expression of the JSON value
    :param target_expr: C++ expression of where to store the parsed value
    :param ref_parts: C++ expression of reference path segments to the value
    :param a_type: mapry definition of the value type
    :param registry_expr:
        C++ expression of the registry of the class instances
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


_PARSE_EMBED_TPL = mapry.cpp.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
{% if value_expr|is_variable %}
{# Short-circuit value as value expression if it is a variable so that
we don't end up with an unnecessary variable1 = variable2 statement.#}
{% set value = value_expr %}
{% else %}
{% set value = "value_%s"|format(uid) %}
const Json::Value& value_{{ uid }} = {{ value_expr }};
{% endif %}
{{ embed_name|as_variable }}_from(
    {{ value }},
    {% for registry_expr in selected_registry_exprs %}
    {{ registry_expr }},
    {% endfor %}
    {{ ref_parts|join_strings|indent }},
    &{{ target_expr }},
    errors);''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_embed(
        value_expr: str, target_expr: str, ref_parts: List[str],
        a_type: mapry.Embed, registry_exprs: Mapping[mapry.Class, str],
        auto_id: _AutoID) -> str:
    """
    Generate the code to parse an embeddable structure.

    The code parses the ``value_expr`` into the ``target_expr``.

    :param value_expr: C++ expression of the JSON value
    :param target_expr: C++ expression of where to store the parsed value
    :param ref_parts: C++ expression of reference path segments to the value
    :param a_type: mapry definition of the value type
    :param registry_exprs:
        map class to C++ expression of the registry of the class instances
    :param auto_id: generator of unique identifiers
    :return: generated code
    """
    uid = auto_id.next_identifier()

    references = mapry.references(a_type=a_type)

    # yapf: disable
    return _PARSE_EMBED_TPL.render(
        value_expr=value_expr,
        target_expr=target_expr,
        ref_parts=ref_parts,
        uid=uid,
        embed_name=a_type.name,
        selected_registry_exprs=[
            registry_exprs[reference]
            for reference in references])
    # yapf: enable


@ensure(lambda result: not result.endswith('\n'))
def _parse_value(
        value_expr: str, target_expr: str, ref_parts: List[str],
        a_type: mapry.Type, registry_exprs: Mapping[mapry.Class, str],
        auto_id: _AutoID, cpp: mapry.Cpp) -> str:
    """
    Generate the code to parse the the ``value_expr`` into the ``target_expr``.

    :param value_expr: C++ expression of the JSON value
    :param target_expr: C++ expression of where to store the parsed value
    :param ref_parts: C++ expression of reference path segments to the value
    :param a_type: mapry type of the value
    :param registry_exprs:
        map class to C++ expression of the registry of the class instances
    :param auto_id: generator of unique identifiers
    :param cpp: C++ settings
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
            cpp=cpp)

    elif isinstance(a_type, mapry.Date):
        body = _parse_date(
            value_expr=value_expr,
            target_expr=target_expr,
            ref_parts=ref_parts,
            a_type=a_type,
            auto_id=auto_id,
            cpp=cpp)

    elif isinstance(a_type, mapry.Datetime):
        body = _parse_date_time(
            value_expr=value_expr,
            target_expr=target_expr,
            ref_parts=ref_parts,
            a_type=a_type,
            auto_id=auto_id,
            cpp=cpp)

    elif isinstance(a_type, mapry.Time):
        body = _parse_time(
            value_expr=value_expr,
            target_expr=target_expr,
            ref_parts=ref_parts,
            a_type=a_type,
            auto_id=auto_id,
            cpp=cpp)

    elif isinstance(a_type, mapry.TimeZone):
        body = _parse_time_zone(
            value_expr=value_expr,
            target_expr=target_expr,
            ref_parts=ref_parts,
            a_type=a_type,
            auto_id=auto_id,
            cpp=cpp)

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
            cpp=cpp)

    elif isinstance(a_type, mapry.Map):
        body = _parse_map(
            value_expr=value_expr,
            target_expr=target_expr,
            ref_parts=ref_parts,
            a_type=a_type,
            registry_exprs=registry_exprs,
            auto_id=auto_id,
            cpp=cpp)

    elif isinstance(a_type, mapry.Class):
        assert a_type in registry_exprs, \
            ('Missing registry expression for class {} (ref: {}); '
             'available registry expressions: {}').format(
                a_type.name, a_type.ref,
                [cls.name for cls in registry_exprs.keys()])

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
            auto_id=auto_id)

    else:
        raise NotImplementedError(
            "Unhandled parsing of type: {}".format(a_type))

    return body


_PARSE_PROPERTY_TPL = mapry.cpp.jinja2_env.ENV.from_string(
    '''\
{# Assume `errors` is defined to collect errors. #}
////
// Parse {{ a_property.name|as_field }}
////

{% if not a_property.optional %}
if (!{{value_obj_expr}}.isMember({{a_property.json|escaped_str}})) {
    errors->add(
        {{ ref_obj_parts|join_strings|indent|indent }},
        {{ "Property is missing: %s"|format(a_property.json)|escaped_str }});
} else {
    {{ parsing|indent }}
}
{% else %}
if ({{value_obj_expr}}.isMember({{a_property.json|escaped_str}})) {
    {% if needs_emplace %}
    {{ property_target_expr }}.emplace();
    {% endif %}{# /if needs_emplace #}
    {{ parsing|indent }}
}
{% endif %}{# /if not a_property.optional #}''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_property(
        target_obj_expr: str, value_obj_expr: str, ref_obj_parts: List[str],
        a_property: mapry.Property, registry_exprs: Mapping[mapry.Class, str],
        auto_id: _AutoID, cpp: mapry.Cpp) -> str:
    """
    Generate the code to parse a property of a composite from a JSON object.

    :param target_obj_expr:
        C++ expression of the object to store the properties
    :param value_obj_expr: C++ expression of the JSON object
    :param ref_obj_parts:
        C++ expression of the reference path segments to the object
    :param a_property: mapry definition of the property
    :param registry_exprs:
        map class to C++ expression of the registry of the class instances
    :param auto_id: generator of unique identifiers
    :param cpp: C++ settings
    :return: generated code
    """
    field = mapry.cpp.naming.as_field(identifier=a_property.name)
    property_target_expr = "{}->{}".format(target_obj_expr, field)
    property_value_expr = "{}[{}]".format(
        value_obj_expr, mapry.cpp.generate.escaped_str(a_property.json))
    property_ref_parts = ref_obj_parts + [
        mapry.cpp.generate.escaped_str("/" + a_property.json)
    ]

    # Special handling of the optional property
    needs_emplace = isinstance(
        a_property.type, (mapry.Array, mapry.Map, mapry.Embed))

    parsing_target_expr = property_target_expr
    if a_property.optional:
        if isinstance(a_property.type, (mapry.Array, mapry.Map)):
            parsing_target_expr = "*{}".format(property_target_expr)
        elif isinstance(a_property.type, mapry.Embed):
            parsing_target_expr = "(*{})".format(property_target_expr)

    # yapf: disable
    parsing = _parse_value(
        value_expr=property_value_expr,
        target_expr=parsing_target_expr,
        ref_parts=property_ref_parts,
        a_type=a_property.type,
        registry_exprs=registry_exprs,
        auto_id=auto_id,
        cpp=cpp)
    # yapf: enable

    text = _PARSE_PROPERTY_TPL.render(
        a_property=a_property,
        value_obj_expr=value_obj_expr,
        ref_obj_parts=ref_obj_parts,
        parsing=parsing,
        property_target_expr=property_target_expr,
        needs_emplace=needs_emplace)

    return text.rstrip("\n")


_PARSE_COMPOSITE_TPL = mapry.cpp.jinja2_env.ENV.from_string(
    '''\
void {{ composite.name|as_variable }}_from(
        const Json::Value& value,
{% for ref_cls in references %}
        const std::map<std::string, std::unique_ptr<{{
            ref_cls.name|as_composite }}>>& {{
                ref_cls.plural|as_variable }}_registry,
{% endfor %}
        std::string ref,
        {{ composite.name|as_composite }}* target,
        parse::Errors* errors) {
    if (!value.isObject()) {
        constexpr auto expected_but_got(
            "Expected an object, but got: ");

        errors->add(
            ref,
            message(
                expected_but_got,
                strlen(expected_but_got),
                value_type_to_string(
                    value.type())));
        return;
    }
    {% for prop in composite.properties.values() %}

    {{ property_parsing[prop]|indent }}
    if (errors->full()) {
        return;
    }
    {% endfor %}{# /for prop in composite.properties.values() #}
}''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_composite(
        composite: Union[mapry.Class, mapry.Embed], cpp: mapry.Cpp) -> str:
    """
    Generate the code of the function that parses a composite.

    :param composite: mapry definition of the composite
    :param cpp: C++ settings
    :return: generated code
    """
    references = mapry.references(a_type=composite)

    # yapf: disable
    registry_exprs = {
        ref_cls: '{}_registry'.format(
            mapry.cpp.naming.as_variable(ref_cls.plural))
        for ref_cls in references
    }
    # yapf: enable

    auto_id = _AutoID()

    # yapf: disable
    property_parsing = {
        prop: _parse_property(
            target_obj_expr="target",
            value_obj_expr="value",
            ref_obj_parts=["ref"],
            a_property=prop,
            registry_exprs=registry_exprs,
            auto_id=auto_id,
            cpp=cpp)
        for prop in composite.properties.values()
    }
    # yapf: enable

    return _PARSE_COMPOSITE_TPL.render(
        composite=composite,
        references=references,
        property_parsing=property_parsing)


_PARSE_GRAPH_TPL = mapry.cpp.jinja2_env.ENV.from_string(
    '''\
void {{ graph.name|as_variable }}_from(
        const Json::Value& value,
        std::string ref,
        {{ graph.name|as_composite }}* target,
        parse::Errors* errors) {
    if (errors == nullptr) {
        throw std::invalid_argument("Unexpected null errors");
    }

    if (!errors->empty()) {
        throw std::invalid_argument("Unexpected non-empty errors");
    }

    if (!value.isObject()) {
        constexpr auto expected_but_got(
            "Expected an object, but got: ");

        errors->add(
            ref,
            message(
                expected_but_got,
                strlen(expected_but_got),
                value_type_to_string(
                    value.type())));
        return;
    }
{% for cls in graph.classes.values() %}

    ////
    // Pre-allocate {{ cls.plural|as_field }}
    ////

    std::string {{ cls.plural|as_variable }}_ref;
    {{ cls.plural|as_variable }}_ref.reserve(ref.size() + {{
        "/%s"|format(cls.plural|json_plural)|length }});
    {{ cls.plural|as_variable }}_ref += ref;
    {{ cls.plural|as_variable }}_ref += {{
        "/%s"|format(cls.plural|json_plural)|escaped_str }};

    if (value.isMember({{ cls.plural|json_plural|escaped_str }})) {
        const Json::Value& obj = value[{{
            cls.plural|json_plural|escaped_str }}];
        if (!obj.isObject()) {
            constexpr auto expected_but_got(
                "Expected an object, but got: ");

            errors->add(
                {{ cls.plural|as_variable }}_ref,
                message(
                    expected_but_got,
                    strlen(expected_but_got),
                    value_type_to_string(
                        obj.type())));
        } else {
            for (Json::ValueConstIterator it = obj.begin();
                    it != obj.end(); ++it) {
                {% set set_instance %}
                auto instance = std::make_unique<{{ cls.name|as_composite }}>();
                instance->id = it.name();
                target->{{
                    cls.plural|as_field }}[it.name()] = std::move(instance);
                {% endset %}
                {% if cls.id_pattern is not none %}
                if (!std::regex_match(
                        it.name(),
                        {{ cls.name|as_variable }}_re::kID)) {
                    constexpr auto expected_but_got(
                        "Expected ID to match "
                        {{ cls.id_pattern.pattern|escaped_str }}
                        ", but got: ");

                    errors->add(
                        {{ cls.plural|as_variable }}_ref,
                        message(
                            expected_but_got,
                            strlen(expected_but_got),
                            it.name()));

                    if (errors->full()) {
                        break;
                    }
                } else {
                    {{ set_instance|indent }}
                }
                {% else %}
                {{ set_instance }}
                {% endif %}{# /if cls.id_pattern is not none #}
            }
        }
    }
{% endfor %}
{% if graph.classes %}

    // Pre-allocating class instances is critical.
    // If the pre-allocation failed, we can not continue to parse the instances.
    if (!errors->empty()) {
        return;
    }

    // Keep the prefix fixed in this buffer so that
    // it is copied as little as possible
    std::string instance_ref;
{% endif %}
{% for cls in graph.classes.values() %}

    ////
    // Parse {{ cls.plural|as_field }}
    ////

    // clear() does not shrink the reserved memory,
    // see https://en.cppreference.com/w/cpp/string/basic_string/clear
    instance_ref.clear();
    instance_ref += {{ cls.plural|as_variable }}_ref;
    instance_ref += '/';

    if (value.isMember({{ cls.plural|json_plural|escaped_str }})) {
        const Json::Value& obj = value[{{
            cls.plural|json_plural|escaped_str }}];

        for (Json::ValueConstIterator it = obj.begin(); it != obj.end(); ++it) {
            instance_ref.reserve(
                {{ cls.plural|as_variable }}_ref.size() + 1 + it.name().size());
            instance_ref.resize(
                {{ cls.plural|as_variable }}_ref.size() + 1);
            instance_ref.append(
                it.name());

            {{ cls.name|as_composite }}* instance(
                target->{{ cls.plural|as_field }}.at(it.name()).get());
            {{ cls.name|as_variable }}_from(
                *it,
                {% for ref_cls in references[cls] %}
                target->{{ ref_cls.plural|as_field }},
                {% endfor %}
                instance_ref,
                instance,
                errors);

            if (errors->full()) {
                break;
            }
        }
    }
    if (errors->full()) {
        return;
    }
{% endfor %}
{% for property_parsing in property_parsings %}

    {{ property_parsing|indent }}
    if (errors->full()) {
        return;
    }
{% endfor %}
}''')


@ensure(lambda result: not result.endswith('\n'))
def _parse_graph(graph: mapry.Graph, cpp: mapry.Cpp) -> str:
    """
    Generate the code that parses an object graph.

    :param graph: definition of the object graph
    :param cpp: C++ settings
    :return: generated code
    """
    # Map mapry class -> referenced mapry classes
    references = dict()  # type: MutableMapping[mapry.Class, List[mapry.Class]]
    for cls in graph.classes.values():
        references[cls] = mapry.references(a_type=cls)

    # Map mapry class -> C++ expression of the instance registry
    registry_exprs = dict()  # type: Dict[mapry.Class, str]
    for cls in graph.classes.values():
        plural_field = mapry.cpp.naming.as_field(identifier=cls.plural)
        registry_exprs[cls] = 'target->{}'.format(plural_field)

    # Gather property parsings in a list so that they can be readily inserted
    # in the template
    property_parsings = []  # type: List[str]

    auto_id = _AutoID()
    for prop in graph.properties.values():
        property_parsings.append(
            _parse_property(
                target_obj_expr="target",
                value_obj_expr="value",
                ref_obj_parts=['ref'],
                a_property=prop,
                registry_exprs=registry_exprs,
                auto_id=auto_id,
                cpp=cpp))

    text = _PARSE_GRAPH_TPL.render(
        graph=graph, references=references, property_parsings=property_parsings)

    assert isinstance(text, str)
    return text.rstrip("\n")


@ensure(lambda result: not result.endswith('\n'))
def _datetime_to_string() -> str:
    """
    Generate the code of a function that translates the date/time to a string.

    :return: generated code
    """
    return textwrap.dedent(
        '''\
        /**
         * serializes the date/time/datetime to a string.
         *
         * @param[in] t time structure
         * @param[in] fmt format
         * @return time structure serialized to a string according to the format
         */
        std::string tm_to_string(const struct tm& t, const char* fmt) {{
            if(fmt == nullptr or fmt[0] == '\\0') {
                return "";
            }

            const size_t fmt_size = strlen(fmt);

            std::string buf;
            buf.resize(fmt_size * 4);
            int len = strftime(&buf[0], buf.size(), fmt, &t);

            while(len == 0) {{
                buf.resize(buf.size() * 2);
                int len = strftime(&buf[0], buf.size(), fmt, &t);
            }}
            buf.resize(len);
            return buf;
        }}''')


@ensure(lambda result: not result.endswith('\n'))
def _duration_to_string() -> str:
    """
    Generate the code for serializing durations to strings.

    :return: generated code
    """
    return textwrap.dedent(
        '''\
        /**
         * serializes the duration to a string.
         *
         * @param[in] d duration to be serialized
         * @return duration as string
         */
        std::string duration_to_string(const std::chrono::nanoseconds& d) {
            typedef std::chrono::nanoseconds::rep rep_t;

            const rep_t abscount = (d.count() < 0) ? -d.count() : d.count();
            if (abscount < 0) {
                std::stringstream sserr;
                sserr
                    << "Computing the absolute number of nanoseconds "
                        "in the duration underflowed: "
                    << d.count();
                throw std::overflow_error(sserr.str());
            }

            const rep_t nanoseconds_in_day = 86400L*1000L*1000L*1000L;
            const rep_t days = abscount / nanoseconds_in_day;
            rep_t rest = abscount % nanoseconds_in_day;

            const rep_t nanoseconds_in_hour = 3600L*1000L*1000L*1000L;
            const rep_t hours = rest / nanoseconds_in_hour;
            rest = rest % nanoseconds_in_hour;

            const rep_t nanoseconds_in_minute = 60L*1000L*1000L*1000L;
            const rep_t minutes = rest / nanoseconds_in_minute;
            rest = rest % nanoseconds_in_minute;

            const rep_t nanoseconds_in_second = 1000L*1000L*1000L;
            const rep_t seconds = rest / nanoseconds_in_second;
            rest = rest % nanoseconds_in_second;

            const rep_t nanoseconds = rest;

            std::stringstream ss;
            if (d.count() < 0) {
                ss << "-";
            }

            ss << "P";

            if(days > 0) {
                ss << days << "D";
            }

            if(hours > 0 or minutes > 0 or
                    seconds > 0 or nanoseconds > 0) {
                ss << "T";

                if(hours > 0) {
                    ss << hours << "H";
                }

                if(minutes > 0) {
                    ss << minutes << "M";
                }

                if(nanoseconds == 0) {
                    if(seconds > 0) {
                        ss << seconds << "S";
                    }
                } else {
                    std::stringstream ssnano;
                    ssnano << std::setfill('0') << std::setw(9) << nanoseconds;
                    const std::string nanos_str = ssnano.str();

                    // Nag trailing zeros
                    size_t i = nanos_str.size() - 1;
                    for(; i >= 0; --i) {
                        if (nanos_str.at(i) != '0') {
                            break;
                        }
                    }

                    ss << seconds << "." << nanos_str.substr(0, i + 1) << "S";
                }
            }

            return ss.str();
        }''')


_SERIALIZE_CTIME_TPL = mapry.cpp.jinja2_env.ENV.from_string(
    '''\
{% if dt_format %}
{{ target_expr }} = tm_to_string(
    {{ value_expr }},
    {{ dt_format|escaped_str }});
{% else %}
{{ target_expr }} = "";
{% endif %}{# /if dt_format #}
''')

_SERIALIZE_DATE_TIME_TPL = mapry.cpp.jinja2_env.ENV.from_string(
    '''\
{% if dt_format %}
{{ target_expr }} = date::format(
    {{ dt_format|escaped_str }},
    {{ value_expr }});
{% else %}
{{ target_expr }} = "";
{% endif %}{# /if dt_format #}
''')


@ensure(lambda result: not result.endswith('\n'))
def _serialize_date_time(
        target_expr: str, value_expr: str,
        a_type: Union[mapry.Date, mapry.Datetime], cpp: mapry.Cpp) -> str:
    """
    Generate the code to serialize a date/datetime.

    The code serializes the ``value_expr`` into the ``target_expr``.

    :param target_expr: C++ expression of the Json::Value to be set
    :param value_expr: C++ expression of the value to be serialized
    :param a_type: the mapry type of the value
    :param cpp: C++ settings
    :return: generated serialization code
    """
    if cpp.datetime_library == 'ctime':
        return _SERIALIZE_CTIME_TPL.render(
            value_expr=value_expr,
            target_expr=target_expr,
            dt_format=a_type.format).rstrip()
    if cpp.datetime_library == 'date.h':
        return _SERIALIZE_DATE_TIME_TPL.render(
            value_expr=value_expr,
            target_expr=target_expr,
            dt_format=a_type.format).rstrip()
    raise NotImplementedError(
        "Unhandled datetime library: {}".format(cpp.datetime_library))


_SERIALIZE_TIME_TPL = mapry.cpp.jinja2_env.ENV.from_string(
    '''\
{% if dt_format %}
{{ target_expr }} = date::format(
    {{ dt_format|escaped_str }},
    {{ value_expr }}.to_duration());
{% else %}
{{ target_expr }} = "";
{% endif %}{# /if dt_format #}
''')


@ensure(lambda result: not result.endswith('\n'))
def _serialize_time(
        target_expr: str, value_expr: str, a_type: mapry.Time,
        cpp: mapry.Cpp) -> str:
    """
    Generate the code to serialize a time zone.

    The code serializes the ``value_expr`` into the ``target_expr``.

    :param target_expr: C++ expression of the Json::Value to be set
    :param value_expr: C++ expression of the value to be serialized
    :param a_type: the mapry type of the value
    :param cpp: C++ settings
    :return: generated serialization code
    """
    if cpp.datetime_library == 'ctime':
        return _SERIALIZE_CTIME_TPL.render(
            value_expr=value_expr,
            target_expr=target_expr,
            dt_format=a_type.format).rstrip()
    if cpp.datetime_library == 'date.h':
        return _SERIALIZE_TIME_TPL.render(
            value_expr=value_expr,
            target_expr=target_expr,
            dt_format=a_type.format).rstrip()

    raise NotImplementedError(
        "Unhandled datetime library: {}".format(cpp.datetime_library))


@ensure(lambda result: not result.endswith('\n'))
def _serialize_time_zone(
        target_expr: str, value_expr: str, cpp: mapry.Cpp) -> str:
    """
    Generate the code to serialize a time zone.

    The code serializes the ``value_expr`` into the ``target_expr``.

    :param target_expr: C++ expression of the Json::Value to be set
    :param value_expr: C++ expression of the value to be serialized
    :param cpp: C++ settings
    :return: generated serialization code
    """
    if cpp.datetime_library == 'ctime':
        return '{} = {};'.format(target_expr, value_expr)

    if cpp.datetime_library == 'date.h':
        return '{} = {}->name();'.format(target_expr, value_expr)

    raise NotImplementedError(
        "Unhandled datetime library: {}".format(cpp.datetime_library))


_SERIALIZE_ARRAY_TPL = mapry.cpp.jinja2_env.ENV.from_string(
    '''\
Json::Value target_{{ uid }}(Json::arrayValue);
const auto& vector_{{ uid }} = {{ value_expr }};
for (int i_{{ uid }} = 0;
        i_{{ uid }} < vector_{{ uid }}.size();
        ++i_{{ uid }}) {
    {{ item_serialization|indent }}
}
{{ target_expr }} = std::move(target_{{ uid }});
''')


@ensure(lambda result: not result.endswith('\n'))
def _serialize_array(
        target_expr: str, value_expr: str, a_type: mapry.Array,
        auto_id: _AutoID, cpp: mapry.Cpp) -> str:
    """
    Generate the code to serialize an array.

    The code serializes the ``value_expr`` into the ``target_expr``.

    :param target_expr: C++ expression of the Json::Value to be set
    :param value_expr: C++ expression of the value to be serialized
    :param a_type: the mapry type of the value
    :param auto_id: generator of unique identifiers
    :param cpp: C++ settings
    :return: generated serialization code
    """
    uid = auto_id.next_identifier()

    item_serialization = _serialize_value(
        target_expr="target_{uid}[i_{uid}]".format(uid=uid),
        value_expr="vector_{uid}[i_{uid}]".format(uid=uid),
        a_type=a_type.values,
        auto_id=auto_id,
        cpp=cpp)

    return _SERIALIZE_ARRAY_TPL.render(
        uid=uid,
        value_expr=value_expr,
        item_serialization=item_serialization,
        target_expr=target_expr)


_SERIALIZE_MAP_TPL = mapry.cpp.jinja2_env.ENV.from_string(
    '''\
Json::Value target_{{ uid }}(Json::objectValue);
const auto& map_{{ uid }} = {{ value_expr }};
for (const auto& kv_{{ uid }} : map_{{ uid }}) {
    {{ item_serialization|indent }}
}
{{ target_expr }} = std::move(target_{{ uid }});
''')


@ensure(lambda result: not result.endswith('\n'))
def _serialize_map(
        target_expr: str, value_expr: str, a_type: mapry.Map, auto_id: _AutoID,
        cpp: mapry.Cpp) -> str:
    """
    Generate the code to serialize a map.

    The code serializes the ``value_expr`` into the ``target_expr``.

    :param target_expr: C++ expression of the Json::Value to be set
    :param value_expr: C++ expression of the value to be serialized
    :param a_type: the mapry type of the value
    :param auto_id: generator of unique identifiers
    :param cpp: C++ settings
    :return: generated serialization code
    """
    uid = auto_id.next_identifier()

    item_serialization = _serialize_value(
        target_expr="target_{uid}[kv_{uid}.first]".format(uid=uid),
        value_expr="kv_{uid}.second".format(uid=uid),
        a_type=a_type.values,
        auto_id=auto_id,
        cpp=cpp)

    return _SERIALIZE_MAP_TPL.render(
        uid=uid,
        value_expr=value_expr,
        item_serialization=item_serialization,
        target_expr=target_expr)


@ensure(lambda result: not result.endswith('\n'))
def _serialize_value(
        target_expr: str, value_expr: str, a_type: mapry.Type, auto_id: _AutoID,
        cpp: mapry.Cpp) -> str:
    """
    Generate the code to serialize the ``value_expr`` into the ``target_expr``.

    :param target_expr: C++ expression of the Json::Value to be set
    :param value_expr: C++ expression of the value to be serialized
    :param a_type: the mapry type of the value
    :param auto_id: generator of unique identifiers
    :param cpp: C++ settings
    :return: generated serialization code
    """
    result = ''

    if isinstance(a_type,
                  (mapry.Boolean, mapry.Integer, mapry.Float, mapry.String)):
        result = '{} = {};'.format(target_expr, value_expr)

    elif isinstance(a_type, mapry.Path):
        result = "{} = {}.string();".format(target_expr, value_expr)

    elif isinstance(a_type, (mapry.Date, mapry.Datetime)):
        result = _serialize_date_time(
            target_expr=target_expr,
            value_expr=value_expr,
            a_type=a_type,
            cpp=cpp)

    elif isinstance(a_type, mapry.Time):
        result = _serialize_time(
            target_expr=target_expr,
            value_expr=value_expr,
            a_type=a_type,
            cpp=cpp)

    elif isinstance(a_type, mapry.TimeZone):
        result = _serialize_time_zone(
            target_expr=target_expr, value_expr=value_expr, cpp=cpp)

    elif isinstance(a_type, mapry.Duration):
        result = '{} = duration_to_string({});'.format(target_expr, value_expr)

    elif isinstance(a_type, mapry.Array):
        result = _serialize_array(
            target_expr=target_expr,
            value_expr=value_expr,
            a_type=a_type,
            auto_id=auto_id,
            cpp=cpp)

    elif isinstance(a_type, mapry.Map):
        result = _serialize_map(
            target_expr=target_expr,
            value_expr=value_expr,
            a_type=a_type,
            auto_id=auto_id,
            cpp=cpp)

    elif isinstance(a_type, mapry.Class):
        result = "{} = {}->id;".format(target_expr, value_expr)

    elif isinstance(a_type, mapry.Embed):
        result = "{} = serialize_{}({});".format(
            target_expr, mapry.cpp.naming.as_variable(a_type.name), value_expr)

    else:
        raise NotImplementedError(
            "Unhandled serialization of type: {}".format(a_type))

    return result


_SERIALIZE_OPTIONAL_PROPERTY_TPL = mapry.cpp.jinja2_env.ENV.from_string(
    '''\
if ({{ value_expr }}) {
    {{ serialization|indent }}
}
''')


@ensure(lambda result: not result.endswith('\n'))
def _serialize_property(
        target_expr: str, value_expr: str, a_property: mapry.Property,
        auto_id: _AutoID, cpp: mapry.Cpp) -> str:
    """
    Generate the code to serialize the property.

    The value as the property is given as ``value_expr`` and serialized
    into the ``target_expr``.

    :param target_expr: C++ expression of the Json::Value to be set
    :param value_expr: C++ expression of the value to be serialized
    :param a_property: the property definition
    :param auto_id: generator of unique identifiers
    :param cpp: C++ settings
    :return: generated serialization code
    """
    if not a_property.optional:
        return _serialize_value(
            target_expr=target_expr,
            value_expr=value_expr,
            a_type=a_property.type,
            auto_id=auto_id,
            cpp=cpp)

    ##
    # Handle optional property
    ##

    deref_value_expr = "(*{})".format(value_expr)

    serialization = _serialize_value(
        target_expr=target_expr,
        value_expr=deref_value_expr,
        a_type=a_property.type,
        auto_id=auto_id,
        cpp=cpp)

    return _SERIALIZE_OPTIONAL_PROPERTY_TPL.render(
        value_expr=value_expr, serialization=serialization)


_SERIALIZE_CLASS_OR_EMBED_TPL = mapry.cpp.jinja2_env.ENV.from_string(
    '''\
Json::Value serialize_{{ composite.name|as_variable }}(
        const {{ composite.name|as_composite }}& {{
            composite.name|as_variable }}) {
    {% set value = "%s_as_value"|format(composite.name|as_variable) %}
    {% if property_serializations %}
    Json::Value {{ value }};
    {% for serialization in property_serializations %}

    {{ serialization|indent }}
    {% endfor %}

    return {{ value }};
    {% else %}
    return Json::objectValue;
    {% endif %}
}''')


@ensure(lambda result: not result.endswith('\n'))
def _serialize_class_or_embed(
        class_or_embed: Union[mapry.Class, mapry.Embed], cpp: mapry.Cpp) -> str:
    """
    Generate the function to serialize a class or an embeddable structure.

    :param embed: a mapry definition of the class or the embeddable structure
    :param cpp: C++ settings
    :return: generated code
    """
    value_expr = mapry.cpp.naming.as_variable(class_or_embed.name)

    auto_id = _AutoID()

    # yapf: disable
    property_serializations = [
        _serialize_property(
            target_expr="{}_as_value[{}]".format(
                mapry.cpp.naming.as_variable(class_or_embed.name),
                mapry.cpp.generate.escaped_str(prop.json)),
            value_expr="{}.{}".format(value_expr, prop.name),
            a_property=prop,
            auto_id=auto_id,
            cpp=cpp)
        for prop in class_or_embed.properties.values()
    ]
    # yapf: enable

    return _SERIALIZE_CLASS_OR_EMBED_TPL.render(
        composite=class_or_embed,
        property_serializations=property_serializations)


_SERIALIZE_GRAPH_TPL = mapry.cpp.jinja2_env.ENV.from_string(
    '''\
Json::Value serialize_{{ graph.name|as_variable }}(
        const {{ graph.name|as_composite }}& {{ graph.name|as_variable }}) {
    {% set value = "%s_as_value"|format(graph.name|as_variable) %}
    {% if property_serializations or graph.classes %}
    Json::Value {{ value }};
    {% for serialization in property_serializations %}

    {{ serialization|indent }}
    {% endfor %}{# /for property_serializations #}
    {% for cls in graph.classes.values() %}

    if (!{{ graph.name|as_variable }}.{{ cls.plural|as_variable }}.empty()) {
        Json::Value {{ cls.plural|as_variable }}_as_value;
        for (const auto& kv : {{
                graph.name|as_variable }}.{{ cls.plural|as_variable }}) {
            const std::string& id = kv.first;
            const {{ cls.name|as_composite }}* instance = kv.second.get();

            if (id != instance->id) {
                constexpr auto expected(
                    "Expected the class instance of "
                    {{ cls.name|as_composite|escaped_str }}
                    "to have the ID ");
                constexpr auto but_got(", but got: ");

                std::string msg;
                msg.reserve(
                    strlen(expected) + id.size() +
                    strlen(but_got) + instance->id.size());
                msg += expected;
                msg += id;
                msg += but_got;
                msg += instance->id;

                throw std::invalid_argument(msg);
            }

            {{ cls.plural|as_variable }}_as_value[instance->id] = {#
            #}serialize_{{ cls.name|as_variable }}(*instance);
        }
        {{ value }}[{{ cls.plural|json_plural|escaped_str }}] = {{
            cls.plural|as_variable }}_as_value;
    }
    {% endfor %}{# /for cls #}

    return {{ value }};
    {% else %}{## case no properties nor classes ##}
    return Json::objectValue;
    {% endif %}{# /if property_serializations or graph.classes #}
}''')


@ensure(lambda result: not result.endswith('\n'))
def _serialize_graph(graph: mapry.Graph, cpp: mapry.Cpp) -> str:
    """
    Generate the implementation of the function that serializes a mapry graph.

    :param graph: mapry definition of the object graph
    :param cpp: C++ settings
    :return: generated code
    """
    value_expr = mapry.cpp.naming.as_variable(graph.name)

    auto_id = _AutoID()

    # yapf: disable
    property_serializations = [
        _serialize_property(
            target_expr="{}_as_value[{}]".format(
                mapry.cpp.naming.as_variable(graph.name),
                mapry.cpp.generate.escaped_str(prop.json)),
            value_expr="{}.{}".format(value_expr, prop.name),
            a_property=prop,
            auto_id=auto_id,
            cpp=cpp)
        for prop in graph.properties.values()
    ]
    # yapf: enable

    return _SERIALIZE_GRAPH_TPL.render(
        graph=graph, property_serializations=property_serializations)


@ensure(lambda result: result.endswith('\n'))
def generate(
        graph: mapry.Graph, cpp: mapry.Cpp, types_header_path: str,
        parse_header_path: str, jsoncpp_header_path: str) -> str:
    """
    Generate the implementation file for de/serialization from/to Jsoncpp.

    :param graph: definition of the object graph
    :param cpp: C++ settings
    :param types_header_path: defines the types of the object graph
    :param parse_header_path: defines the general parsing structures
    :param jsoncpp_header_path:
        defines parsing and serializing functions from/to Jsoncpp
    :return: content of the implementation file
    """
    ##
    # Header
    ##

    blocks = [
        mapry.cpp.generate.WARNING,
        _includes(
            graph=graph,
            types_header_path=types_header_path,
            parse_header_path=parse_header_path,
            jsoncpp_header_path=jsoncpp_header_path,
            cpp=cpp)
    ]

    namespace_parts = cpp.namespace.split('::')
    if namespace_parts:
        namespace_opening = '\n'.join([
            'namespace {} {{'.format(namespace_part)
            for namespace_part in namespace_parts
        ])
        blocks.append(namespace_opening)

    blocks.append("namespace jsoncpp {")

    ##
    # Parse
    ##

    blocks.append(_message_function())

    regex_constants_text = _regex_constants(graph=graph)
    if regex_constants_text != '':
        blocks.append(regex_constants_text)

    if mapry.needs_type(a_type=graph, query=mapry.Duration):
        blocks.append(_duration_from_string())

    blocks.append(_value_type_to_string())

    blocks.append(_parse_graph(graph=graph, cpp=cpp))

    ##
    # Serialize
    ##

    if cpp.datetime_library == 'ctime':
        # yapf: disable
        if any(mapry.needs_type(a_type=graph, query=query_type)
               for query_type in [mapry.Date, mapry.Time, mapry.Datetime]):
            # yapf: enable
            blocks.append(_datetime_to_string())
    elif cpp.datetime_library == 'date.h':
        pass
    else:
        raise NotImplementedError(
            "Unhandled datetime library: {}".format(cpp.datetime_library))

    if mapry.needs_type(a_type=graph, query=mapry.Duration):
        blocks.append(_duration_to_string())

    nongraph_composites = []  # type: List[Union[mapry.Class, mapry.Embed]]
    nongraph_composites.extend(graph.classes.values())
    nongraph_composites.extend(graph.embeds.values())

    for class_or_embed in nongraph_composites:
        blocks.append(_parse_composite(composite=class_or_embed, cpp=cpp))

    for class_or_embed in nongraph_composites:
        blocks.append(
            _serialize_class_or_embed(class_or_embed=class_or_embed, cpp=cpp))

    blocks.append(_serialize_graph(graph=graph, cpp=cpp))

    blocks.append("}  // namespace jsoncpp")

    ##
    # Footer
    ##

    if namespace_parts:
        # yapf: disable
        namespace_closing = '\n'.join(
            ['}}  // namespace {}'.format(namespace_part)
             for namespace_part in reversed(namespace_parts)])
        # yapf: enable
        blocks.append(namespace_closing)

    blocks.append(mapry.cpp.generate.WARNING)

    text = '\n\n'.join(blocks) + '\n'

    return mapry.indention.reindent(text=text, indention=cpp.indention)
