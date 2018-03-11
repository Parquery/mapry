#!/usr/bin/env python3

# pylint: disable=missing-docstring

import unittest
from typing import List, Optional, Tuple  # pylint: disable=unused-import

import lexery

import mapry.strftime


class TestTokenize(unittest.TestCase):
    def test_unparsable(self) -> None:
        lexery_error = None  # type: Optional[lexery.Error]
        try:
            _ = mapry.strftime.tokenize(format='%')
        except lexery.Error as err:
            lexery_error = err

        self.assertIsNotNone(lexery_error)
        self.assertEqual(
            'Unmatched text at line 0 and position 0:\n%\n^', str(lexery_error))

    def test_parsable_and_supported(self) -> None:
        tkn_lines = mapry.strftime.tokenize(format="%% %Y-%m-%dT%H:%M:%SZ")

        got = []  # type: List[List[Tuple[str, str]]]
        for tkn_line in tkn_lines:
            got.append([(tkn.identifier, tkn.content) for tkn in tkn_line])

        # yapf: disable
        expected = [
            [
                ('directive', '%%'), ('text', ' '), ('directive', '%Y'),
                ('text', '-'), ('directive', '%m'), ('text', '-'),
                ('directive', '%d'), ('text', 'T'), ('directive', '%H'),
                ('text', ':'), ('directive', '%M'), ('text', ':'),
                ('directive', '%S'), ('text', 'Z')
            ]
        ]
        # yapf: enable

        self.assertListEqual(expected, got)

    def test_unsupported_directives(self) -> None:
        not_implemented_err = None  # type: Optional[NotImplementedError]
        try:
            _ = mapry.strftime.tokenize(format='%j %U')
        except NotImplementedError as err:
            not_implemented_err = err

        self.assertIsNotNone(not_implemented_err)
        self.assertEqual(
            'unsupported directive(s): %j, %U', str(not_implemented_err))
