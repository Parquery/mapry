"""Generate the code to test serializing object graphs to JSONables."""

import textwrap
from typing import Set  # pylint: disable=unused-import

from icontract import ensure

import mapry
import mapry.go.generate
import mapry.go.jinja2_env
import mapry.indention


@ensure(lambda result: not result.endswith('\n'))
def _imports(graph: mapry.Graph) -> str:
    """
    Generate the import declaration.

    :param graph: mapry definition of the object graph
    :return: generated code
    """
    import_set = set()  # type: Set[str]

    if mapry.needs_type(a_type=graph, query=mapry.Duration):
        import_set.add('fmt')
        import_set.add('time')

    return mapry.go.generate.import_declarations(import_set)


@ensure(lambda result: not result.endswith('\n'))
def _example_duration_to_string() -> str:
    """
    Generate the code to test serializing durations to strings.

    :return: generated code
    """
    return textwrap.dedent(
        '''\
    func ExampleDurationToString_oneYear() {
        d := 365 * 24 * time.Hour
        s := durationToString(d)
        fmt.Println(s)
        // Output: P365D
    }

    func ExampleDurationToString_negativeYear() {
        d := -365 * 24 * time.Hour
        s := durationToString(d)
        fmt.Println(s)
        // Output: -P365D
    }

    func ExampleDurationToString_hoursMinutesSeconds() {
        d := time.Hour + 2 * time.Minute + 3 * time.Second
        s := durationToString(d)
        fmt.Println(s)
        // Output: PT1H2M3S
    }

    func ExampleDurationToString_daysHoursMinutesSeconds() {
        d := 24 * time.Hour + 2 * time.Hour + 3 * time.Minute + 4 * time.Second
        s := durationToString(d)
        fmt.Println(s)
        // Output: P1DT2H3M4S
    }

    func ExampleDurationToString_secondsNanoseconds() {
        d := 1 * time.Second + time.Nanosecond
        s := durationToString(d)
        fmt.Println(s)
        // Output: PT1.000000001S
    }

    func ExampleDurationToString_secondsManyNanoseconds() {
        d := 1 * time.Second + 1000 * time.Nanosecond
        s := durationToString(d)
        fmt.Println(s)
        // Output: PT1.000001S
    }

    func ExampleDurationToString_nanoseconds() {
        d := 1 * time.Nanosecond
        s := durationToString(d)
        fmt.Println(s)
        // Output: PT0.000000001S
    }''')


@ensure(lambda result: result.endswith('\n'))
def generate(graph: mapry.Graph, go: mapry.Go) -> str:
    """
    Generate the source file to test serializing to a JSONable.

    :param graph: mapry definition of the object graph
    :param go: Go settings
    :return: content of the source file
    """
    blocks = [
        'package {}'.format(go.package),
        mapry.go.generate.WARNING,
    ]

    import_decl = _imports(graph=graph)
    if len(import_decl) > 0:
        blocks.append(import_decl)

    if mapry.needs_type(a_type=graph, query=mapry.Duration):
        blocks.append(_example_duration_to_string())

    blocks.append(mapry.go.generate.WARNING)

    return mapry.indention.reindent(
        text='\n\n'.join(blocks) + '\n', indention='\t')
