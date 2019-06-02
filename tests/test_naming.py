#!/usr/bin/env python3

# pylint: disable=missing-docstring

import unittest

import mapry.naming


class TestNaming(unittest.TestCase):
    def test_to_snake_case(self) -> None:
        # yapf: disable
        table = [
            (('cv_size_int', True), 'CvSizeInt'),
            (('cv_size_int', False), 'cvSizeInt'),
            (('URLs_to_find', True), 'URLsToFind'),
            (('URLs_to_find', False), 'urlsToFind'),
            (('some_IDs', True), 'SomeIDs'),
            (('some_IDs', False), 'someIDs'),
            (('some_IDs_to_store', True), 'SomeIDsToStore'),
            (('some_IDs_to_store', False), 'someIDsToStore')
        ]
        # yapf: enable

        for (identifier, capital), expected in table:
            if capital:
                got = mapry.naming.ucamel_case(identifier=identifier)
            else:
                got = mapry.naming.camel_case(identifier=identifier)

            self.assertEqual(expected, got)


if __name__ == '__main__':
    unittest.main()
