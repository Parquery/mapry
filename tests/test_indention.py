#!/usr/bin/env python3

# pylint: disable=missing-docstring

import unittest

import mapry.indention


class TestIndention(unittest.TestCase):
    def test_indention_of_single_line(self) -> None:
        indented = mapry.indention.reindent(
            text='oi', level=3, indention=' ' * 2)

        self.assertEqual(indented, '  ' * 3 + 'oi')

    def test_indention_of_multiple_lines(self) -> None:
        indented = mapry.indention.reindent(
            text='oi\nnoi', level=1, indention=' ' * 2)

        self.assertEqual(indented, '  oi\n  noi')


if __name__ == '__main__':
    unittest.main()
