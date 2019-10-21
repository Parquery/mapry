#!/usr/bin/env python3
"""Test generated Go code by running it."""

import argparse
import json
import os
import pathlib
import subprocess
from typing import Any, Sequence

import icontract
import temppathlib

import mapry
import mapry.go.generate
import mapry.go.generate.fromjsonable
import mapry.go.generate.parse
import mapry.go.generate.tojsonable
import mapry.go.generate.types
import mapry.go.jinja2_env
import mapry.go.validation
import mapry.parse
import tests.path

_PARSE_SERIALIZE_TPL = mapry.go.jinja2_env.ENV.from_string(
    '''\
package main

// This program parses and serializes the given {{
    graph.name|ucamel_case }} as a JSON file.

import (
    "flag"
    "fmt"
    "encoding/json"
    "os"
    "path/filepath"

    {{ "parse_serialize/%s"|format(package)|escaped_str }}
)

var path = flag.String(
    "path",
    "",
    {{ "path to the instance of %s as a JSON file"|
        format(graph.name|ucamel_case)|escaped_str }})

func read(pth string) (value interface{}, err error) {
    f, err := os.Open(pth)
    if err != nil {
        return
    }
    defer func() {
        closeErr := f.Close()
        if closeErr != nil {
            if err != nil {
                err = fmt.Errorf(
                    "%s; also failed to close the file: %s",
                    err.Error(), closeErr.Error());
            } else {
                err = closeErr
            }
        }
    }()

    err = json.NewDecoder(f).Decode(&value)
    return
}

func main() {
    os.Exit(func() int {
        flag.Parse()

        if path == nil || *path == "" {
            fmt.Fprintf(os.Stderr, "-path is mandatory.\\n")
            return 1
        }

        value, err := read(*path)
        if err != nil {
            fmt.Fprintf(
                os.Stderr,
                "failed to read the file %s: %s\\n",
                filepath.Base(*path), err.Error())
            return 1
        }

        instance := &{{ package }}.{{ graph.name|ucamel_case }}{}
        errors := {{ package }}.NewErrors(0)

        {{ package }}.{{ graph.name|ucamel_case }}FromJSONable(
            value,
            "#",
            instance,
            errors)

        if !errors.Empty() {
            ee := errors.Values()
            for i := 0; i < len(ee); i++ {
                fmt.Fprintf(
                    os.Stderr,
                    "%s: %s\\n",
                    ee[i].Ref,
                    ee[i].Message)
            }
            return 1
        }

        var jsonable map[string]interface{}
        jsonable, err = {{ package }}.{{ graph.name|ucamel_case }}ToJSONable(
            instance)

        var data []byte
        data, err = json.MarshalIndent(jsonable, "", "  ")
        if err != nil {
            fmt.Fprintf(
                os.Stderr,
                "failed to marshal the jsonable: %s\\n",
                err.Error())
            return 1
        }
        os.Stdout.Write(data)
        os.Stdout.Sync()

        return 0
    }())
}

''')


@icontract.ensure(lambda result: result.endswith("\n"))
def generate_parse_serialize(graph: mapry.Graph, go: mapry.Go) -> str:
    """
    Generate the main Go file that parses and serializes back an input file.

    :param graph: mapry definition of the object graph
    :param go: Go settings
    :return: generated code
    """
    return _PARSE_SERIALIZE_TPL.render(graph=graph, package=go.package)


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
            relative path to the test case from the test_cases directory
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


def execute_case(case: Case, gopath: pathlib.Path) -> None:
    """
    Generate all the files, execute the test and check the output.

    :param case: definition of the test case
    :param gopath: path to the go environment associated with this test case
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

    errors = mapry.go.validation.validate_schema(schema=schema)
    if len(errors) > 0:
        raise AssertionError(
            "Errors while validating the schema {}:\n{}".format(
                case.schema_path, "\n".join(str(error) for error in errors)))

    graph = schema.graph
    go = schema.go

    assert go is not None, \
        "Expected Go settings to be specified in the schema {}".format(
            case.schema_path)

    ##
    # Generate the source files
    ##

    src_dir = gopath / "src"

    say("Generating the files in {} ...".format(src_dir))

    (src_dir / "parse_serialize" / go.package).mkdir(
        exist_ok=True, parents=True)

    (src_dir / "parse_serialize" / go.package / 'types.go').write_text(
        mapry.go.generate.types.generate(graph=graph, go=go))

    (src_dir / "parse_serialize" / go.package / 'parse.go').write_text(
        mapry.go.generate.parse.generate(go=go))

    (src_dir / "parse_serialize" / go.package / 'fromjsonable.go').write_text(
        mapry.go.generate.fromjsonable.generate(graph=graph, go=go))

    (src_dir / "parse_serialize" / go.package / 'tojsonable.go').write_text(
        mapry.go.generate.tojsonable.generate(graph=graph, go=go))

    (src_dir / "parse_serialize" / "main.go").write_text(
        generate_parse_serialize(graph=graph, go=go))
    (src_dir / "parse_serialize" / "main.go").chmod(mode=0o755)

    env = os.environ.copy()
    env['GOPATH'] = gopath.as_posix()

    ##
    # Validate
    ##

    say("go vet'ing the generated filies in {} ...".format(gopath))
    subprocess.check_call(['go', 'vet', '.'],
                          cwd=(src_dir / "parse_serialize").as_posix(),
                          env=env)

    ##
    # Build
    ##

    say("go build'ing {} ...".format(gopath))
    subprocess.check_call(['go', 'build', '.'],
                          cwd=(src_dir / "parse_serialize").as_posix(),
                          env=env)

    ##
    # Execute
    ##

    for example_pth in case.example_paths:
        example_id = example_pth.stem
        say("Running against the example: {}".format(example_id))

        expected_out_pth = (
            case.schema_path.parent / "go/live_test_generate_jsonable" /
            example_id / "expected.out")

        expected_err_pth = (
            case.schema_path.parent / "go/live_test_generate_jsonable" /
            example_id / "expected.err")

        # yapf: disable
        proc = subprocess.Popen(
            [(
                gopath / 'src' / 'parse_serialize' / 'parse_serialize'
             ).as_posix(),
             '-path', example_pth.as_posix()],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True)
        # yapf: enable

        out, err = proc.communicate()

        if not expected_out_pth.exists():
            raise FileNotFoundError(
                "The file with the expected STDOUT of not found: {}".format(
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
                "Expected stderr ({}):\n     {!r},\ngot: {!r}".format(
                    expected_err_pth, expected_err, err))

        else:
            # Everything is correct.
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
                    "Failed to decode the resulting output:\n{!r}".format(
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
    # Check the environment
    ##

    if subprocess.call(['which', 'go'], stderr=subprocess.DEVNULL) != 0:
        raise RuntimeError(
            "Go compiler could not be found. Please make sure you installed it "
            "and put it on your PATH.")

    ##
    # Collect test cases
    ##

    schema_pths = sorted(
        list(cases_dir.glob("general/**/schema.json")) +
        list(cases_dir.glob("go/**/schema.json")) +
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

        for case in cases:
            execute_case(
                case=case, gopath=base_operation_dir.path / case.rel_path)


if __name__ == "__main__":
    main()
