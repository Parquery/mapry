#!/usr/bin/env python3
"""Convert date/time format from strftime directives to Go."""
from typing import List  # pylint: disable=unused-import

from icontract import ensure

import mapry.strftime

# Taken from https://github.com/bdotdub/fuckinggodateformat
_STRFTIME_TO_GO = {
    '%a': 'Sun',
    '%A': 'Sunday',
    '%b': 'Jan',
    '%B': 'January',
    '%d': '02',
    '%e': '_2',
    '%m': '01',
    '%y': '06',
    '%Y': '2006',
    '%H': '15',
    '%I': '03',
    '%l': '3',
    '%M': '04',
    '%P': 'pm',
    '%p': 'PM',
    '%S': '05',
    '%z': '-0700',
    '%Z': 'MST',
    '%%': '%'
}


@ensure(lambda result: not result.endswith('\n'))
def convert(a_format: str) -> str:
    r"""
    Convert the strftime/strptime directives to Go directives.

    :param format:  strftime/strptime directives
    :return: string literal representing the date/time format with Go directives

    >>> convert(a_format="%Y-%m-%d %H:%M:%SZ")
    '2006-01-02 15:04:05Z'

    >>> convert(a_format="%Y-%m-%d\\n%H:%M:%SZ")
    '2006-01-02\\n15:04:05Z'

    """
    tkn_lines = mapry.strftime.tokenize(format=a_format)

    parts = []  # type: List[str]

    for i, tkn_line in enumerate(tkn_lines):
        if i > 0:
            parts.append('\n')

        for tkn in tkn_line:
            if tkn.identifier == 'directive':
                assert tkn.content in _STRFTIME_TO_GO, \
                    "Unhandled strftime->go mapping for: {}".format(tkn.content)

                parts.append(_STRFTIME_TO_GO[tkn.content])
            elif tkn.identifier == 'text':
                parts.append(tkn.content)

    return ''.join(parts)
