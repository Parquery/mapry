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
        with tempfile.TemporaryDirectory() as tmpdir:
            # Test with list
            tmpfile = pathlib.Path(tmpdir) / "test-schema-with-list.yml"
            tmpfile.write_text('[]')

            try:
                mapry.parse.schema_from_json_file(path=tmpfile)
            except mapry.validation.SchemaError as err:
                self.assertEqual((
                    "{}#: Does not follow json schema: "
                    "[] is not of type 'object'").format(tmpfile), str(err))

            # Test with name as object instead of string
            tmpfile = pathlib.Path(tmpdir) / "name-as-object.yml"

            tmpfile.write_text(
                '{"name": {"unexpected": "value"}, '
                '"description": "some description."}')

            try:
                mapry.parse.schema_from_json_file(path=tmpfile)
            except mapry.validation.SchemaError as err:
                self.assertEqual(
                    str(err), "{}#/name: Does not follow json schema: "
                    "{{'unexpected': 'value'}} is not of type 'string'".format(
                        tmpfile))

    def test_cases(self) -> None:  # pylint: disable=no-self-use
        cases_dir = tests.path.REPO_DIR / 'test_cases' / 'general'

        for pth in sorted(cases_dir.glob("**/schema.json")):
            _ = mapry.parse.schema_from_json_file(path=pth)


if __name__ == '__main__':
    unittest.main()
