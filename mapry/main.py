#!/usr/bin/env python3
"""Provide the main point of entry."""

import argparse
import collections
import pathlib
import sys
from typing import Optional  # pylint: disable=unused-import

import icontract

import mapry
import mapry.cpp.generate.jsoncpp_header
import mapry.cpp.generate.jsoncpp_impl
import mapry.cpp.generate.parse_header
import mapry.cpp.generate.parse_impl
import mapry.cpp.generate.types_header
import mapry.cpp.validation
import mapry.go.generate
import mapry.go.generate.fromjsonable
import mapry.go.generate.fromjsonable_test
import mapry.go.generate.parse
import mapry.go.generate.tojsonable
import mapry.go.generate.tojsonable_test
import mapry.go.generate.types
import mapry.go.validation
import mapry.parse
import mapry.py.generate
import mapry.py.generate.fromjsonable
import mapry.py.generate.parse
import mapry.py.generate.tojsonable
import mapry.py.generate.types
import mapry.py.validation


@icontract.require(lambda outdir: outdir.exists())
def generate_cpp(schema: mapry.Schema, outdir: pathlib.Path) -> int:
    """
    Generate the C++ code.

    :param schema: parsed mapry schema
    :param outdir: output directory where generated files should be stored
    :return: exit code
    """
    errors = mapry.cpp.validation.validate_schema(schema=schema)

    if errors:
        print('Schema failed to validate:', file=sys.stderr)
        for error in errors:
            print(str(error), file=sys.stderr)
        return 1

    graph = schema.graph
    cpp = schema.cpp

    if cpp is None:
        print(
            'Expected the C++ settings to be set in the schema, '
            'but found none (no "cpp" field)',
            file=sys.stderr)
        return 1

    # yapf: disable
    filename_to_code = collections.OrderedDict([
        ('types.h', mapry.cpp.generate.types_header.generate(
            graph=graph, cpp=cpp)),
        ('parse.h', mapry.cpp.generate.parse_header.generate(cpp=cpp)),
        ('parse.cpp', mapry.cpp.generate.parse_impl.generate(
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
        pth = outdir / filename
        pth.write_text(code)

    print('Files generated in: {}'.format(outdir))

    return 0


@icontract.require(lambda outdir: outdir.exists())
def generate_go(schema: mapry.Schema, outdir: pathlib.Path) -> int:
    """
    Generate the Go code.

    :param schema: parsed mapry schema
    :param outdir: output directory where generated files should be stored
    :return: exit code
    """
    errors = mapry.go.validation.validate_schema(schema=schema)

    if errors:
        print('Schema failed to validate:', file=sys.stderr)
        for error in errors:
            print(str(error), file=sys.stderr)
        return 1

    graph = schema.graph
    go = schema.go

    if go is None:
        print(
            'Expected the C++ settings to be set in the schema, '
            'but found none (no "go" field)',
            file=sys.stderr)
        return 1

    # yapf: disable
    filename_to_code = collections.OrderedDict([
        ('types.go', mapry.go.generate.types.generate(graph=graph, go=go)),
        ('parse.go', mapry.go.generate.parse.generate(go=go)),
        ('from_jsonable.go', mapry.go.generate.fromjsonable.generate(
            graph=graph, go=go)),
        ('from_jsonable_test.go', mapry.go.generate.fromjsonable_test.generate(
            graph=graph, go=go)),
        ('to_jsonable.go', mapry.go.generate.tojsonable.generate(
            graph=graph, go=go)),
        ('to_jsonable_test.go', mapry.go.generate.tojsonable_test.generate(
            graph=graph, go=go)),
    ])
    # yapf: enable

    outdir.mkdir(exist_ok=True, parents=True)

    for filename, code in filename_to_code.items():
        pth = outdir / filename
        pth.write_text(code)

    print('Files generated in: {}'.format(outdir))

    return 0


@icontract.require(lambda outdir: outdir.exists())
def generate_py(schema: mapry.Schema, outdir: pathlib.Path) -> int:
    """
    Generate the Python code.

    :param schema: parsed mapry schema
    :param outdir: output directory where generated files should be stored
    :return: exit code
    """
    errors = mapry.py.validation.validate_schema(schema=schema)

    if errors:
        print('Schema failed to validate:', file=sys.stderr)
        for error in errors:
            print(str(error), file=sys.stderr)
        return 1

    graph = schema.graph
    py = schema.py

    if py is None:
        print(
            'Expected the Python settings to be set in the schema, '
            'but found none (no "py" field)',
            file=sys.stderr)
        return 1

    # yapf: disable
    filename_to_code = collections.OrderedDict([
        ('__init__.py', mapry.py.generate.types.generate(
            graph=graph, py=py)),
        ('parse.py', mapry.py.generate.parse.generate(
            graph=graph, py=py)),
        ('fromjsonable.py', mapry.py.generate.fromjsonable.generate(
            graph=graph, py=py)),
        ('tojsonable.py', mapry.py.generate.tojsonable.generate(
            graph=graph, py=py)),
    ])
    # yapf: enable

    outdir.mkdir(exist_ok=True, parents=True)

    for filename, code in filename_to_code.items():
        pth = outdir / filename
        pth.write_text(code)

    print('Files generated in: {}'.format(outdir))

    return 0


def main() -> int:
    """Execute the main routine."""
    parser = argparse.ArgumentParser(
        description="Generate the code for de/serialization of object graphs "
        "from JSONables.")
    subparsers = parser.add_subparsers(
        help='defines which generator to use', dest='command')
    subparsers.required = True

    parser_cpp = subparsers.add_parser('cpp', help='generate C++ code')
    parser_cpp.add_argument(
        "--schema", help="path to the schema definition", required=True)
    parser_cpp.add_argument(
        "--outdir",
        help="path to the directory where the generated files should be stored",
        required=True)

    parser_go = subparsers.add_parser('go', help='generate Go code')
    parser_go.add_argument(
        "--schema", help="path to the schema definition", required=True)
    parser_go.add_argument(
        "--outdir",
        help="path to the directory where the generated files should be stored",
        required=True)

    parser_go = subparsers.add_parser('py', help='generate Python code')
    parser_go.add_argument(
        "--schema", help="path to the schema definition", required=True)
    parser_go.add_argument(
        "--outdir",
        help="path to the directory where the generated files should be stored",
        required=True)

    args = parser.parse_args()

    command = str(args.command)

    schema = None  # type: Optional[mapry.Schema]
    schema_pth = pathlib.Path(args.schema) if args.schema else None
    if schema_pth is not None:
        if not schema_pth.exists():
            print(
                'Schema does not exist: {}'.format(schema_pth), file=sys.stderr)
            return 1

        if not schema_pth.is_file():
            print(
                'Schema must be a file, but got: {}'.format(schema_pth),
                file=sys.stderr)
            return 1

        schema = mapry.parse.schema_from_json_file(path=schema_pth)

    outdir = pathlib.Path(args.outdir) if args.outdir else None
    if outdir is not None:
        outdir.mkdir(exist_ok=True, parents=True)

    if command == 'cpp':
        assert outdir is not None, "Expected outdir to be specified"
        assert schema is not None, "Expected schema to be loaded"
        return generate_cpp(schema=schema, outdir=outdir)
    elif command == 'go':
        assert outdir is not None, "Expected outdir to be specified"
        assert schema is not None, "Expected schema to be loaded"
        return generate_go(schema=schema, outdir=outdir)
    elif command == 'py':
        assert outdir is not None, "Expected outdir to be specified"
        assert schema is not None, "Expected schema to be loaded"
        return generate_py(schema=schema, outdir=outdir)
    else:
        raise NotImplementedError('command: {}'.format(command))
