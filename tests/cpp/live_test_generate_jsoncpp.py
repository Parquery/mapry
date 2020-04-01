#!/usr/bin/env python3
"""Test generated C++ code by compiling it and running it."""

import argparse
import json
import os
import pathlib
import subprocess
import textwrap
from typing import Any, Sequence

import icontract
import temppathlib

import mapry
import mapry.cpp.generate.jsoncpp_header
import mapry.cpp.generate.jsoncpp_impl
import mapry.cpp.generate.parse_header
import mapry.cpp.generate.parse_impl
import mapry.cpp.generate.types_header
import mapry.cpp.jinja2_env
import mapry.cpp.validation
import mapry.parse
import tests.path

_PARSE_SERIALIZE_TPL = mapry.cpp.jinja2_env.ENV.from_string(
    '''\
#include "types.h"
#include "parse.h"
#include "jsoncpp.h"

#include <json/json.h>

#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <streambuf>
#include <string>

void print_usage() {
    std::cerr << "Usage: parse_serialize [JSON file]" << std::endl;
}

Json::Value value_from_file(const char* path) {
    Json::Value value;

    std::ifstream ifs(path);

    ifs >> value;
    return value;
}

void print_value(const Json::Value& value) {
    Json::StreamWriterBuilder builder;
    builder["commentStyle"] = "None";
    builder["indentation"] = "    ";
    builder["enableYAMLCompatibility"] = true;

    std::unique_ptr<Json::StreamWriter> writer(builder.newStreamWriter());
    writer->write(value, &std::cout);
}

int main(int argc, char* argv[]) {
    if (argc != 2) {
        print_usage();
        return 1;
    }

    Json::Value value;
    try {
        value = value_from_file(argv[1]);
    } catch(std::exception& err) {
        std::cerr << "Error loading JSON from file " << argv[1] << ": "
            << err.what();
        return 1;
    }

    const std::string in_path(argv[1]);

    {{ namespace }}::parse::Errors errors(1024);
    {{ namespace }}::{{ graph.name|as_composite }} graph;

    {{ namespace }}::jsoncpp::{{ graph.name|as_variable }}_from(
            value,
            "#",
            &graph,
            &errors);

    if (not errors.empty()) {
        for (const auto& err : errors.get()) {
            std::cerr << err.ref << ": " << err.message << std::endl;
        }
        return 1;
    }
    try {
        const Json::Value out_value(
            {{ namespace }}::jsoncpp::serialize_{{ graph.name|as_variable }}(
                graph));
        print_value(out_value);
    } catch(std::exception e) {
        std::cerr << "Caught an exception while serializing:\\n"
            << e.what() << std::endl;
        return 1;
    }

    return 0;
}

''')


@icontract.ensure(lambda result: result.endswith("\n"))
def generate_parse_serialize(graph: mapry.Graph, cpp: mapry.Cpp) -> str:
    """
    Generate the main C++ file that parses and serializes back an input file.

    :param graph: mapry definition of the object graph
    :param cpp: C++ settings
    :return: generated code
    """
    return _PARSE_SERIALIZE_TPL.render(namespace=cpp.namespace, graph=graph)


@icontract.ensure(lambda result: result.endswith('\n'))
def generate_case_cmake(executable_name: str) -> str:
    """
    Generate the CMakeLists.txt corresponding to the given test case.

    :param executable_name:
        name of the executable that parses and serializes an input file.
    :return: generated cmake code
    """
    # Link all potentially needed libraries even if unused by the executable.
    #
    # This way we do not have to complicate the code unnecessarily and
    # check programmatically whether these libraries are really needed
    # by the executable.
    return textwrap.dedent(
        '''\
        add_executable({executable_name}
            parse_serialize.cpp
            types.h
            parse.h
            parse.cpp
            jsoncpp.h
            jsoncpp.cpp)
        target_link_libraries({executable_name}
            CONAN_PKG::jsoncpp
            CONAN_PKG::boost
            tz)
        '''.format(executable_name=executable_name))


_CMAKE_MAIN_TPL = mapry.cpp.jinja2_env.ENV.from_string(
    '''\
cmake_minimum_required(VERSION 3.5.1)
project(MapryLiveTest)

include(conan.cmake)
conan_cmake_run(REQUIRES
    jsoncpp/1.8.4@theirix/stable
    boost/1.66.0@conan/stable
    BASIC_SETUP CMAKE_TARGETS
    BUILD missing)

include_directories({{ test_dependencies_dir }}/cpp/optional/include)

set(USE_SYSTEM_TZ_DB ON CACHE BOOL
    "use System time zone database to avoid curl dependency")
add_subdirectory({{ test_dependencies_dir }}/cpp/date-2.4.1 date-2.4.1)

{% for test_rel_path in test_rel_paths %}
add_subdirectory({{ test_rel_path }})
{% endfor %}

''')


@icontract.ensure(lambda result: result.endswith('\n'))
def generate_main_cmake(
        test_dependencies_dir: pathlib.Path,
        test_rel_paths: Sequence[pathlib.Path]) -> str:
    """
    Generate the main CMakeLists.txt file.

    This file defines all the dependencies and includes the subdirectories
    corresponding to the test cases.

    :param test_dependencies_dir:
        path to the directory which contains third-party dependencies
        such as std::experimental::optional.
    :param test_rel_paths:
        relative paths to the subdirectories where source code of the test cases
        are generated
    :return: generated cmake code
    """
    return _CMAKE_MAIN_TPL.render(
        test_dependencies_dir=test_dependencies_dir,
        test_rel_paths=test_rel_paths)


class Case:
    """Represent a test schema with the examples."""

    @icontract.require(
        # yapf: disable
        lambda schema_path, example_paths: all(
            example_path.parent == schema_path.parent
            for example_path in example_paths),
        "Necessary since we need to re-use the test identifier "
        "for the example and the schemas")
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

        self.executable_name = "{}_parse_serialize".format(
            rel_path.as_posix().replace("/", "_"))


class Params:
    """Represent parsed command-line parameters."""

    def __init__(self, args: Any) -> None:
        """Parse command-line parameters."""
        # yapf: disable
        self.operation_dir = (
            pathlib.Path(args.operation_dir)
            if args.operation_dir is not None
            else None)
        # yapf: enable


def generate_all_case_files(case: Case, case_src_dir: pathlib.Path) -> None:
    """
    Generate all the files related to the given test case.

    :param case: definition of the test case
    :param case_src_dir:
        directory where C++ source files of the test case should be generated
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

    errors = mapry.cpp.validation.validate_schema(schema=schema)
    if len(errors) > 0:
        raise AssertionError(
            "Errors while validating the schema {}:\n{}".format(
                case.schema_path, "\n".join(str(error) for error in errors)))

    graph = schema.graph
    cpp = schema.cpp

    assert cpp is not None, \
        "Expected C++ settings to be specified in the schema {}".format(
            case.schema_path)

    ##
    # Generate the source files
    ##

    say("Generating the files in {} ...".format(case_src_dir))

    (case_src_dir).mkdir(exist_ok=True, parents=True)

    (case_src_dir / "types.h").write_text(
        mapry.cpp.generate.types_header.generate(graph=graph, cpp=cpp))

    (case_src_dir / "parse.h").write_text(
        mapry.cpp.generate.parse_header.generate(cpp=cpp))

    (case_src_dir / "parse.cpp").write_text(
        mapry.cpp.generate.parse_impl.generate(
            cpp=cpp, parse_header_path="parse.h"))

    (case_src_dir / "jsoncpp.h").write_text(
        mapry.cpp.generate.jsoncpp_header.generate(
            graph=graph,
            cpp=cpp,
            types_header_path='types.h',
            parse_header_path='parse.h'))

    (case_src_dir / "jsoncpp.cpp").write_text(
        mapry.cpp.generate.jsoncpp_impl.generate(
            graph=graph,
            cpp=cpp,
            types_header_path='types.h',
            parse_header_path='parse.h',
            jsoncpp_header_path='jsoncpp.h'))

    (case_src_dir / "parse_serialize.cpp").write_text(
        generate_parse_serialize(graph=graph, cpp=cpp))

    (case_src_dir / "CMakeLists.txt").write_text(
        generate_case_cmake(executable_name=case.executable_name))


def execute_case(case: Case, bin_dir: pathlib.Path) -> None:
    """
    Execute the generated parse/serialize binary and verify the output.

    :param case: definition of the test case
    :param bin_dir: directory where built binaries reside
    :return:
    """

    def say(message: str) -> None:
        """Write a message prefixed with the relative test path."""
        print("[{}] {}".format(case.rel_path, message))

    for example_pth in case.example_paths:
        example_id = example_pth.stem
        say("Running against the example: {}".format(example_id))

        expected_out_pth = (
            case.schema_path.parent / "cpp/live_test_generate_jsoncpp" /
            example_id / "expected.out")

        expected_err_pth = (
            case.schema_path.parent / "cpp/live_test_generate_jsoncpp" /
            example_id / "expected.err")

        # yapf: disable
        proc = subprocess.Popen(
            [(bin_dir / case.executable_name).as_posix(),
             example_pth.as_posix()],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
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
            # No error has been encountered.
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

    if subprocess.call(['which', 'conan'], stderr=subprocess.DEVNULL) != 0:
        raise RuntimeError(
            "Conan could not be found. Please make sure you have it installed "
            "in your virtual environment (pip3 install conan).")

    cases_dir = tests.path.REPO_DIR / 'test_cases'
    assert cases_dir.exists(), \
        "Expected the test cases directory in the repository: {}".format(
            cases_dir)

    ##
    # Collect test cases
    ##

    schema_pths = sorted(
        list(cases_dir.glob("general/**/schema.json")) +
        list(cases_dir.glob("cpp/**/schema.json")) +
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
        # Generate case files
        ##

        src_dir = base_operation_dir.path / "src"
        src_dir.mkdir(exist_ok=True)

        for case in cases:
            generate_all_case_files(
                case=case, case_src_dir=src_dir / case.rel_path)

        ##
        # Generate the main CMakeLists
        ##

        this_dir = pathlib.Path(os.path.realpath(__file__)).parent

        (src_dir / "conan.cmake").write_text(
            (this_dir / "conan.cmake").read_text())

        test_dependencies_dir = this_dir.parent.parent / "test_dependencies"

        (src_dir / "CMakeLists.txt").write_text(
            generate_main_cmake(
                test_dependencies_dir=test_dependencies_dir,
                test_rel_paths=[case.rel_path for case in cases]))

        ##
        # Build
        ##

        build_dir = base_operation_dir.path / "build"

        print("Compiling in: {}".format(build_dir))

        build_dir.mkdir(exist_ok=True)
        subprocess.check_call(['cmake', '../src', '-DCMAKE_BUILD_TYPE=Debug'],
                              cwd=build_dir.as_posix())
        subprocess.check_call(['make', 'all'], cwd=build_dir.as_posix())

        ##
        # Run
        ##

        print("Executing {} test case(s)...".format(len(cases)))
        for case in cases:
            execute_case(case=case, bin_dir=build_dir / 'bin')


if __name__ == "__main__":
    main()
