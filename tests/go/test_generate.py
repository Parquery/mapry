#!/usr/bin/env python3
"""Test generation of Go code."""

# pylint: disable=missing-docstring
import collections
import unittest

import mapry.go.generate
import mapry.go.generate.fromjsonable
import mapry.go.generate.fromjsonable_test
import mapry.go.generate.parse
import mapry.go.generate.tojsonable
import mapry.go.generate.tojsonable_test
import mapry.go.generate.types
import mapry.go.validation
import mapry.parse
import tests.path


class TestGenerate(unittest.TestCase):
    def test_cases(self) -> None:  # pylint: disable=no-self-use
        cases_dir = tests.path.REPO_DIR / 'test_cases'

        # yapf: disable
        schema_pths = sorted(
            list(cases_dir.glob("general/**/schema.json")) +
            list(cases_dir.glob("go/**/schema.json")) +
            list(cases_dir.glob("docs/**/schema.json")))
        # yapf: enable

        for schema_pth in schema_pths:
            schema = mapry.parse.schema_from_json_file(path=schema_pth)

            errors = mapry.go.validation.validate_schema(schema=schema)
            if len(errors) > 0:
                raise AssertionError(
                    "Errors while validating the schema {}:\n{}".format(
                        schema_pth, "\n".join(str(error) for error in errors)))

            graph = schema.graph
            go = schema.go

            assert go is not None, \
                "Expected Go settings to be defined in the schema {}".format(
                    schema_pth)

            # yapf: disable
            filename_to_code = collections.OrderedDict([
                ('types.go',
                 mapry.go.generate.types.generate(graph=graph, go=go)),

                ('parse.go',
                 mapry.go.generate.parse.generate(go=go)),

                ('from_jsonable.go',
                 mapry.go.generate.fromjsonable.generate(graph=graph, go=go)),

                ('from_jsonable_test.go',
                 mapry.go.generate.fromjsonable_test.generate(
                     graph=graph, go=go)),

                ('to_jsonable.go',
                 mapry.go.generate.tojsonable.generate(graph=graph, go=go)),

                ('to_jsonable_test.go',
                 mapry.go.generate.tojsonable_test.generate(
                     graph=graph, go=go)),
            ])
            # yapf: enable

            for filename, code in filename_to_code.items():
                expected_pth = schema_pth.parent / "go/test_generate" / filename

                if not expected_pth.exists():
                    raise FileNotFoundError((
                        "File containing the expected Go code "
                        "could not be found: {}").format(expected_pth))

                expected = expected_pth.read_text()
                self.assertEqual(
                    expected, code,
                    "Generated code for {} and {} must match.".format(
                        filename, expected_pth))


if __name__ == '__main__':
    unittest.main()
