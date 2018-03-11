"""Parse and convert strftime directives."""
import collections
import re
from typing import (  # pylint: disable=unused-import
    List, MutableMapping, Optional)

import lexery

_LEXER = lexery.Lexer(
    rules=[
        lexery.Rule(identifier='directive', pattern=re.compile(r'%[a-zA-Z%]')),
        lexery.Rule(identifier='text', pattern=re.compile(r'[^%]+'))
    ],
    skip_whitespace=False)

# Supported strftime directives.
#
# Mapry can't support all the directives since the format needs
# to be parsed with different libraries.
#
# For example, see what Go ``time`` package can do:
# http://fuckinggodateformat.com/
SUPPORTED_DIRECTIVES = {
    "%a",  # The abbreviated weekday name ("Sun")
    "%A",  # The full weekday name ("Sunday")
    "%b",  # The abbreviated month name ("Jan")
    "%B",  # The full month name ("January")
    "%d",  # Day of the month (01..31)
    "%e",  # Day of the month with a leading blank instead of zero ( 1..31)
    "%m",  # Month of the year (01..12)
    "%y",  # Year without a century (00..99)
    "%Y",  # Year with century
    "%H",  # Hour of the day, 24-hour clock (00..23)
    "%I",  # Hour of the day, 12-hour clock (01..12)
    "%l",  # Hour of the day, 12-hour clock without a leading zero (1..12)
    "%M",  # Minute of the hour (00..59)
    "%P",  # Meridian indicator ("am" or "pm")
    "%p",  # Meridian indicator ("AM" or "PM")
    "%S",  # Second of the minute (00..60)
    "%z",  # Time zone hour and minute offset from UTC
    "%Z",  # Time zone name
    "%%",  # Literal "%" character
}

# Set of directives expected in a date format
DATE_DIRECTIVES = {
    "%a",  # The abbreviated weekday name ("Sun")
    "%A",  # The full weekday name ("Sunday")
    "%b",  # The abbreviated month name ("Jan")
    "%B",  # The full month name ("January")
    "%d",  # Day of the month (01..31)
    "%e",  # Day of the month with a leading blank instead of zero ( 1..31)
    "%m",  # Month of the year (01..12)
    "%y",  # Year without a century (00..99)
    "%Y",  # Year with century
    "%z",  # Time zone hour and minute offset from UTC
    "%Z",  # Time zone name
    "%%",  # Literal "%" character
}

# Set of directives expected in a time format
TIME_DIRECTIVES = {
    "%H",  # Hour of the day, 24-hour clock (00..23)
    "%I",  # Hour of the day, 12-hour clock (01..12)
    "%l",  # Hour of the day, 12-hour clock without a leading zero (1..12)
    "%M",  # Minute of the hour (00..59)
    "%P",  # Meridian indicator ("am" or "pm")
    "%p",  # Meridian indicator ("AM" or "PM")
    "%S",  # Second of the minute (00..60)
    "%z",  # Time zone hour and minute offset from UTC
    "%Z",  # Time zone name
    "%%",  # Literal "%" character
}


def tokenize(format: str) -> List[List[lexery.Token]]:
    """
    Tokenize the date/time format.

    Also validate that the format contains only the supported subset of
    strftime directives.

    :param format: to be validated
    :return:
        list of token lines defining the text and the directives
        lexed from the format
    :raises:
        lexery.Error if the format could not be parsed,
        NotImplementedError if there are unsupported directives
    """
    # pylint: disable=redefined-builtin
    token_lines = _LEXER.lex(text=format)

    unsupported = collections.OrderedDict()  # type: MutableMapping[str, bool]
    for token_line in token_lines:
        for token in token_line:
            if (token.identifier == 'directive'
                    and token.content not in SUPPORTED_DIRECTIVES):
                unsupported[token.content] = True

    if unsupported:
        raise NotImplementedError(
            "unsupported directive(s): {}".format(
                ", ".join(unsupported.keys())))

    return token_lines


def validate_date_tokens(token_lines: List[List[lexery.Token]]
                         ) -> Optional[ValueError]:
    """
    Check that the tokens represent a valid sequence of date format directives.

    :param token_lines: tokenized date format
    :return: ValueError if the tokens do not represent a valid date format
    """
    if sum((len(token_line) for token_line in token_lines)) == 0:
        return ValueError("Unexpected empty format")

    for token_line in token_lines:
        for token in token_line:
            if (token.identifier == 'directive'
                    and token.content not in DATE_DIRECTIVES):
                return ValueError(
                    "Unexpected directive {!r} in a date format".format(
                        token.content))

    return None


def validate_time_tokens(token_lines: List[List[lexery.Token]]
                         ) -> Optional[ValueError]:
    """
    Check that the tokens represent a valid sequence of time format directives.

    :param token_lines: tokenized time format
    :return: ValueError if the tokens do not represent a valid time format
    """
    if sum((len(token_line) for token_line in token_lines)) == 0:
        return ValueError("Unexpected empty format")

    for token_line in token_lines:
        for token in token_line:
            if (token.identifier == 'directive'
                    and token.content not in TIME_DIRECTIVES):
                return ValueError(
                    "Unexpected directive {!r} in a time format".format(
                        token.content))

    return None
