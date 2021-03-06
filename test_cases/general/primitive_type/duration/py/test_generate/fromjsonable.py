# File automatically generated by mapry. DO NOT EDIT OR APPEND!


"""parses JSONable objects."""


import datetime
import re
import typing

import some.graph
import some.graph.parse


_DURATION_RE = re.compile(
    r'^(?P<sign>\+|-)?P'
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
                text)) from err


def some_graph_from(
        value: typing.Any,
        ref: str,
        errors: some.graph.parse.Errors
) -> typing.Optional[some.graph.SomeGraph]:
    """
    parses SomeGraph from a JSONable value.

    :param value: JSONable value
    :param ref: reference to the value (e.g., a reference path)
    :param errors: errors encountered during parsing
    :return: parsed SomeGraph, or None if ``errors``
    """
    if errors.full():
        return None

    if not isinstance(value, dict):
        errors.add(
            ref,
            "Expected a dictionary, but got: {}".format(type(value)))
        return None

    graph = some.graph.parse.placeholder_some_graph()

    ##
    # Parse some_duration
    ##

    value_0 = value.get(
        'some_duration',
        None)

    if value_0 is None:
        errors.add(
            ref,
            'Property is missing: some_duration')
    else:
        if not isinstance(value_0, str):
            errors.add(
                '/'.join((
                    ref, 'some_duration')),
                "Expected a string, but got: {}".format(
                    type(value_0)))
        else:
            try:
                graph.some_duration = _duration_from_string(
                    value_0)
            except (ValueError, OverflowError) as err:
                errors.add(
                    '/'.join((
                        ref, 'some_duration')),
                    str(err))

    if errors.full():
        return None

    if not errors.empty():
        return None

    return graph
