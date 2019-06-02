#!/usr/bin/env python3

# pylint: disable=missing-docstring

import pathlib
import tempfile
import unittest

import mapry.parse
import mapry.validation
import tests.path


class TestSchema(unittest.TestCase):
    def test_schema_from_invalid_mapping(self) -> None:  # pylint: disable=invalid-name
        # Test with list
        with tempfile.NamedTemporaryFile() as tmpfile:
            tmpfile.file.write('[]'.encode())  # type: ignore
            tmpfile.file.flush()  # type: ignore

            try:
                mapry.parse.schema_from_json_file(
                    path=pathlib.Path(tmpfile.name))
            except mapry.validation.SchemaError as err:
                self.assertEqual((
                    "{}#: Does not follow json schema: "
                    "[] is not of type 'object'").format(tmpfile.name),
                                 str(err))

        # Test with name as object instead of string
        with tempfile.NamedTemporaryFile() as tmpfile:
            tmpfile.file.write(  # type: ignore
                '{"name": {"unexpected": "value"}, '
                '"description": "some description."}'.encode())
            tmpfile.file.flush()  # type: ignore

            try:
                mapry.parse.schema_from_json_file(
                    path=pathlib.Path(tmpfile.name))
            except mapry.validation.SchemaError as err:
                self.assertEqual(
                    str(err), "{}#/name: Does not follow json schema: "
                    "{{'unexpected': 'value'}} is not of type 'string'".format(
                        tmpfile.name))

    def test_cases(self) -> None:  # pylint: disable=no-self-use
        cases_dir = tests.path.REPO_DIR / 'test_cases' / 'general'

        for pth in sorted(cases_dir.glob("**/schema.json")):
            _ = mapry.parse.schema_from_json_file(path=pth)


if __name__ == '__main__':
    unittest.main()
