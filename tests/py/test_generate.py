"""Test generation of Python code."""

# !/usr/bin/env python3

# pylint: disable=missing-docstring
import collections
import unittest

import mapry.parse
import mapry.py.generate
import mapry.py.generate.fromjsonable
import mapry.py.generate.parse
import mapry.py.generate.tojsonable
import mapry.py.generate.types
import mapry.py.validation
import tests.path


class TestGenerateDocstring(unittest.TestCase):
    def test_single_line(self) -> None:
        got = mapry.py.generate.docstring(text='single line')
        self.assertEqual('"""single line"""', got)

    def test_multi_line(self) -> None:
        got = mapry.py.generate.docstring(text='multi\nline')
        self.assertEqual('"""\nmulti\nline\n"""', got)

    def test_backslash(self) -> None:
        got = mapry.py.generate.docstring(text='back\\slash')
        self.assertEqual(r'r"""back\slash"""', got)

    def test_triple_quote(self) -> None:
        got = mapry.py.generate.docstring(text='triple"""quote')
        self.assertEqual(r'"""triple\"\"\"quote"""', got)


class TestGenerate(unittest.TestCase):
    def test_cases(self) -> None:  # pylint: disable=no-self-use
        cases_dir = tests.path.REPO_DIR / 'test_cases'

        # yapf: disable
        schema_pths = sorted(
            list(cases_dir.glob("general/**/schema.json")) +
            list(cases_dir.glob("py/**/schema.json")) +
            list(cases_dir.glob("docs/**/schema.json")))
        # yapf: enable

        for schema_pth in schema_pths:
            schema = mapry.parse.schema_from_json_file(path=schema_pth)

            errors = mapry.py.validation.validate_schema(schema=schema)
            if len(errors) > 0:
                raise AssertionError(
                    "Errors while validating the schema {}:\n{}".format(
                        schema_pth, "\n".join(str(error) for error in errors)))

            graph = schema.graph
            py = schema.py

            assert py is not None, \
                ("Expected Python settings to be defined "
                 "in the schema: {}").format(schema_pth)

            # yapf: disable
            filename_to_code = collections.OrderedDict([
                ('__init__.py',
                 mapry.py.generate.types.generate(graph=graph, py=py)),

                ('parse.py',
                 mapry.py.generate.parse.generate(graph=graph, py=py)),

                ('fromjsonable.py',
                 mapry.py.generate.fromjsonable.generate(graph=graph, py=py)),

                ('tojsonable.py',
                 mapry.py.generate.tojsonable.generate(graph=graph, py=py)),
            ])
            # yapf: enable

            for filename, code in filename_to_code.items():
                expected_pth = schema_pth.parent / "py/test_generate" / filename

                if not expected_pth.exists():
                    raise FileNotFoundError((
                        "File containing the expected Python code "
                        "could not be found: {}").format(expected_pth))

                expected = expected_pth.read_text()
                self.assertEqual(
                    expected, code,
                    "Generated code for {} and {} must match.".format(
                        filename, expected_pth))


if __name__ == '__main__':
    unittest.main()
