#!/usr/bin/env python3
"""Test generated Python code by running it."""

import argparse
import json
import os
import pathlib
import subprocess
import sys
from typing import Any, Sequence

import icontract
import temppathlib

import mapry
import mapry.parse
import mapry.py.generate
import mapry.py.generate.fromjsonable
import mapry.py.generate.parse
import mapry.py.generate.tojsonable
import mapry.py.generate.types
import mapry.py.jinja2_env
import mapry.py.validation
import tests.path

_PARSE_SERIALIZE_TPL = mapry.py.jinja2_env.ENV.from_string(
    '''\
#!/usr/bin/env python3
"""parses and serializes the given {{
    graph.name|as_composite }} as a JSON file."""
import argparse
import collections
import json
import pathlib
import sys


import {{ py.module_name }}.parse
import {{ py.module_name }}.fromjsonable
import {{ py.module_name }}.tojsonable


def main() -> int:
    """Execute the main routine."""
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "--path",
        help="path to the instance of {{
            graph.name|as_composite }} as a JSON file",
        required=True)

    args = parser.parse_args()
    path = pathlib.Path(args.path)

    if not path.exists():
        raise FileNotFoundError(
            {{ "The file containing an instance of %s does not exist: {}"
                    |format(graph.name|as_composite)|repr }}.format(
                path))

    value = json.loads(
        path.read_text(), object_pairs_hook=collections.OrderedDict)

    errors = {{ py.module_name }}.parse.Errors(cap=10)

    graph = {{ py.module_name }}.fromjsonable.{{ graph.name|as_variable }}_from(
        value=value,
        ref="#",
        errors=errors)

    if not errors.empty():
        for error in errors.values():
            print("{}: {}".format(error.ref, error.message), file=sys.stderr)

        return 1

    assert graph is not None, "Expected parsed graph to be non-None."

    try:
        jsonable = {{ py.module_name }}.tojsonable.serialize_{{
            graph.name|as_variable }}(
            graph,
            ordered=True)

        print(json.dumps(jsonable, indent=2))
    except Exception as err:
        print(
            "Caught an exception while serializing:\\n{}".format(str(err)),
            file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

''')


@icontract.ensure(lambda result: result.endswith("\n"))
def generate_parse_serialize(graph: mapry.Graph, py: mapry.Py) -> str:
    """
    Generate the main Python file that parses and serializes back an input file.

    :param graph: mapry definition of the object graph
    :param py: Python settings
    :return: generated code
    """
    return _PARSE_SERIALIZE_TPL.render(py=py, graph=graph)


class Case:
    """Represent a test schema with the examples."""

    # yapf: disable
    @icontract.require(
        lambda schema_path, example_paths: all(
            example_path.parent == schema_path.parent
            for example_path in example_paths),
        "Examples associated with the schema")
    @icontract.require(
        lambda schema_path, rel_path:
        schema_path.parent.parts[-len(rel_path.parts):] == rel_path.parts,
        "Relative path identifies the case")
    # yapf: enable
    def __init__(
            self, schema_path: pathlib.Path,
            example_paths: Sequence[pathlib.Path],
            rel_path: pathlib.Path) -> None:
        """
        Initialize the test case.

        :param schema_path: path to the mapry schema file
        :param example_paths:
            paths to the example files that should be parsed and re-serialized
        :param rel_path:
            relative path to the test case from the test cases directory
            (e.g., "general/primitive_types/float")
        """
        self.schema_path = schema_path
        self.example_paths = example_paths
        self.rel_path = rel_path


class Params:
    """Represent parsed command-line parameters."""

    def __init__(self, args: Any) -> None:
        """Parse command-line parameters."""
        self.operation_dir = (
            pathlib.Path(args.operation_dir)
            if args.operation_dir is not None else None)


def execute_case(case: Case, case_src_dir: pathlib.Path) -> None:
    """
    Generate all the files, execute the test and check the output.

    :param case: definition of the test case
    :param case_src_dir:
        directory where Python source files of the test case should be generated
    :return:
    """

    def say(message: str) -> None:
        """Write a message prefixed with the relative test path."""
        print("[{}] {}".format(case.rel_path, message))

    ##
    # Parse the schema
    ##

    say("Parsing the schema...")

    schema = mapry.parse.schema_from_json_file(path=case.schema_path)

    errors = mapry.py.validation.validate_schema(schema=schema)
    if len(errors) > 0:
        raise AssertionError(
            "Errors while validating the schema {}:\n{}".format(
                case.schema_path, "\n".join(str(error) for error in errors)))

    graph = schema.graph
    py = schema.py

    assert py is not None, \
        "Expected Python settings to be specified in the schema {}".format(
            case.schema_path)
    module_dir = case_src_dir / os.path.join(*py.module_name.split("."))
    module_dir.mkdir(exist_ok=True, parents=True)

    ##
    # Generate dummy __init__.py in parent modules
    ##

    for parent in list(module_dir.relative_to(case_src_dir).parents)[:-1]:
        (case_src_dir / parent / "__init__.py"
         ).write_text('"""automatically generated by mapry-to-py."""\n')

    ##
    # Generate the source files
    ##

    say("Generating the files in {} ...".format(case_src_dir))

    (module_dir / '__init__.py').write_text(
        mapry.py.generate.types.generate(graph=graph, py=py))

    (module_dir / 'parse.py').write_text(
        mapry.py.generate.parse.generate(graph=graph, py=py))

    (module_dir / 'fromjsonable.py').write_text(
        mapry.py.generate.fromjsonable.generate(graph=graph, py=py))

    (module_dir / 'tojsonable.py').write_text(
        mapry.py.generate.tojsonable.generate(graph=graph, py=py))

    (module_dir / "parse_serialize.py").write_text(
        generate_parse_serialize(graph=graph, py=py))

    (module_dir / "parse_serialize.py").chmod(mode=0o755)

    ##
    # Validate
    ##

    say("Mypy'ing the generated filies in {} ...".format(case_src_dir))
    subprocess.check_call(['mypy', '--strict', str(case_src_dir)])

    say("doctest'ing the generated filies in {} ...".format(case_src_dir))
    for pth in sorted(case_src_dir.glob("**/*.py")):
        subprocess.check_call([sys.executable, '-m', 'doctest',
                               str(pth)],
                              cwd=str(case_src_dir))

    ##
    # Execute
    ##

    for example_pth in case.example_paths:
        example_id = example_pth.stem
        say("Running against the example: {}".format(example_id))

        expected_out_pth = (
            case.schema_path.parent / "py/live_test_generate_jsonable" /
            example_id / "expected.out")

        expected_err_pth = (
            case.schema_path.parent / "py/live_test_generate_jsonable" /
            example_id / "expected.err")

        env = os.environ.copy()
        env['PYTHONPATH'] = '{}:{}'.format(
            os.environ.get('PYTHONPATH', ''), str(case_src_dir))

        # yapf: disable
        proc = subprocess.Popen(
            [str(module_dir / 'parse_serialize.py'),
             '--path', str(example_pth)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=env,
            universal_newlines=True)
        # yapf: enable

        out, err = proc.communicate()

        if not expected_out_pth.exists():
            raise FileNotFoundError(
                "The file with the expected STDOUT not found: {}".format(
                    expected_out_pth))

        if not expected_err_pth.exists():
            raise FileNotFoundError(
                "The file with the expected STDERR not found: {}".format(
                    expected_out_pth))

        expected_out = expected_out_pth.read_text()
        expected_err = expected_err_pth.read_text()

        if expected_out != out and expected_err != err:
            raise AssertionError((
                "Expected stdout ({}): {!r}, got: {!r}\n"
                "Expected stderr ({}): {!r}, got: {!r}").format(
                    expected_out_pth, expected_out, out, expected_err_pth,
                    expected_err, err))

        elif expected_out != out:
            raise AssertionError(
                "Expected stdout ({}): {!r}, got: {!r}".format(
                    expected_out_pth, expected_out, out))

        elif expected_err != err:
            raise AssertionError(
                "Expected stderr ({}): {!r}, got: {!r}".format(
                    expected_err_pth, expected_err, err))

        else:
            # Everything worked as expected.
            pass

        ##
        # Check input == output if example_ok
        ##

        if example_pth.name == "example_ok.json":
            assert err == '', \
                "Expected no error on example_ok from {}, but got:\n{}".format(
                    example_pth, err)

            try:
                origin = json.loads(example_pth.read_text())
            except json.JSONDecodeError as err:
                raise RuntimeError(
                    "Failed to decode the example file: {}".format(
                        example_pth)) from err

            try:
                got = json.loads(out)
            except json.JSONDecodeError as err:
                raise AssertionError(
                    "Failed to decode the resulting output from:\n{!r}".format(
                        out)) from err

            if origin != got:
                raise AssertionError(
                    "Expected {!r}, got {!r}".format(origin, got))


def main() -> None:
    """Execute the main routine."""
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "--operation_dir",
        help="path to the directory where temporary test files are stored; "
        "if not specified, uses mkdtemp()")

    args = parser.parse_args()

    params = Params(args=args)

    cases_dir = tests.path.REPO_DIR / 'test_cases'

    ##
    # Collect test cases
    ##

    schema_pths = sorted(
        list(cases_dir.glob("general/**/schema.json")) +
        list(cases_dir.glob("py/**/schema.json")) +
        list(cases_dir.glob("docs/**/schema.json")))

    # yapf: disable
    cases = [
        Case(
            schema_path=schema_pth,
            example_paths=sorted(schema_pth.parent.glob("example_*.json")),
            rel_path=schema_pth.parent.relative_to(cases_dir))
        for schema_pth in schema_pths
    ]
    # yapf: enable

    with temppathlib.TmpDirIfNecessary(
            path=params.operation_dir) as base_operation_dir:
        ##
        # Execute the test cases
        ##

        src_dir = base_operation_dir.path / "src"
        src_dir.mkdir(exist_ok=True)

        for case in cases:
            execute_case(case=case, case_src_dir=src_dir / case.rel_path)


if __name__ == "__main__":
    main()
