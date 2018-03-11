#!/usr/bin/env python3

# pylint: disable=missing-docstring
import collections
import unittest

import mapry
import mapry.cpp.generate.jsoncpp_header
import mapry.cpp.generate.jsoncpp_impl
import mapry.cpp.generate.parse_header
import mapry.cpp.generate.parse_impl
import mapry.cpp.generate.types_header
import mapry.cpp.validation
import mapry.indention
import mapry.parse
import tests.path


class TestGenerate(unittest.TestCase):
    def test_cases(self) -> None:  # pylint: disable=no-self-use
        cases_dir = tests.path.REPO_DIR / 'test_cases'

        schema_pths = sorted(
            list(cases_dir.glob("general/**/schema.json")) +
            list(cases_dir.glob("cpp/**/schema.json")) +
            list(cases_dir.glob("docs/**/schema.json")))

        for schema_pth in schema_pths:
            schema = mapry.parse.schema_from_json_file(path=schema_pth)

            errors = mapry.cpp.validation.validate_schema(schema=schema)
            if len(errors) > 0:
                raise AssertionError(
                    "Errors while validating the schema {}:\n{}".format(
                        schema_pth, "\n".join(str(error) for error in errors)))

            graph = schema.graph
            cpp = schema.cpp

            assert cpp is not None, \
                "Expected C++ settings to be defined in the schema {}".format(
                    schema_pth)

            # yapf: disable
            filename_to_code = collections.OrderedDict([
                ('types.h',
                 mapry.cpp.generate.types_header.generate(
                     graph=graph, cpp=cpp)),
                ('parse.h',
                 mapry.cpp.generate.parse_header.generate(cpp=cpp)),
                ('parse.cpp',
                 mapry.cpp.generate.parse_impl.generate(
                     cpp=cpp, parse_header_path='parse.h')),
                ('jsoncpp.h', mapry.cpp.generate.jsoncpp_header.generate(
                    graph=graph, cpp=cpp, types_header_path='types.h',
                    parse_header_path='parse.h')),
                ('jsoncpp.cpp', mapry.cpp.generate.jsoncpp_impl.generate(
                    graph=graph, cpp=cpp, types_header_path='types.h',
                    parse_header_path='parse.h',
                    jsoncpp_header_path='jsoncpp.h'))
            ])
            # yapf: enable

            for filename, code in filename_to_code.items():
                expected_pth = (
                    schema_pth.parent / "cpp/test_generate" / filename)

                if not expected_pth.exists():
                    raise FileNotFoundError((
                        "File containing the expected C++ code "
                        "could not be found: {}").format(expected_pth))

                expected = expected_pth.read_text()
                self.assertEqual(
                    expected, code,
                    "Generated code for {} and {} must match.".format(
                        filename, expected_pth))


if __name__ == '__main__':
    unittest.main()
