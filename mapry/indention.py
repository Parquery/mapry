"""Re-indent the code."""
import re
import textwrap
from typing import List  # pylint: disable=unused-import

_SPACE4_RE = re.compile('^([ ]{4})+')


def reindent(text: str, level: int = 0, indention: str = ' ' * 4) -> str:
    r"""
    Reindent the given ``text`` to the indention ``level`` with ``indention``.

    The prefix indentation is stripped, the indention in ``text`` is parsed
    as 4 spaces indention and finally re-indented to ``level``.

    :param text: to be re-indented
    :param level: indention level
    :param indention: how to reindent
    :return: re-indented text

    >>> result = reindent(text='''\
    ...     test me:
    ...         again
    ...             and again
    ...     ''', indention='|')
    >>> assert result == ('test me:\n'
    ...                   '|again\n'
    ...                   '||and again\n')

    >>> result = reindent(text='''\
    ...     test me:
    ...         again
    ...             and again
    ...     ''', level=1, indention='|')
    >>> assert result == ('|test me:\n'
    ...                   '||again\n'
    ...                   '|||and again\n')

    """
    text = textwrap.dedent(text)

    lines = text.splitlines(keepends=True)
    result_lines = []  # type: List[str]
    for line in lines:
        mtch = _SPACE4_RE.match(line)
        if mtch:
            _, end = mtch.span()
            spaces = end
            assert spaces % 4 == 0, \
                ("Expected to match indention at 4 spaces, "
                 "but got spaces == {}").format(spaces)

            result_lines.append(
                indention * int(spaces / 4 + level) + line[end:])

        else:
            result_lines.append(indention * level + line)

    return ''.join(result_lines)
