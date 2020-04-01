"""Generate the code implementing the general parse structures."""

import textwrap

from icontract import ensure

import mapry
import mapry.cpp.generate
import mapry.indention


@ensure(lambda result: not result.endswith('\n'))
def _parse_errors() -> str:
    """
    Generate the implementation of the error container.

    :return: generated code
    """
    return textwrap.dedent(
        '''\
        Errors::Errors(size_t cap) : cap_(cap) {}

        void Errors::reserve(size_t expected_errors) {
            errors_.reserve(expected_errors);
        }

        void Errors::add(const std::string& ref, const std::string& message) {
            if (errors_.size() < cap_) {
                errors_.emplace_back(Error{ref, message});
            }
        }

        bool Errors::full() const {
            return errors_.size() == cap_;
        }

        bool Errors::empty() const {
            return errors_.empty();
        }

        const std::vector<Error>& Errors::get() const {
            return errors_;
        }''')


@ensure(lambda result: result.endswith('\n'))
def generate(cpp: mapry.Cpp, parse_header_path: str) -> str:
    """
    Generate the implementation file of the parsing structures.

    :param cpp: C++ settings
    :param parse_header_path:
        path to the header file that defines the general parsing structures
    :return: content of the implementation file
    """
    blocks = [
        mapry.cpp.generate.WARNING, '#include "{}"'.format(parse_header_path),
        textwrap.dedent(
            '''\
            #include <string>
            #include <vector>''')
    ]

    namespace_parts = cpp.namespace.split('::')
    if namespace_parts:
        # yapf: disable
        namespace_opening = '\n'.join(
            ['namespace {} {{'.format(namespace_part)
             for namespace_part in namespace_parts])
        # yapf: enable
        blocks.append(namespace_opening)

    blocks.append("namespace parse {")

    blocks.append(_parse_errors())

    blocks.append("}  // namespace parse")

    if namespace_parts:
        # yapf: disable
        namespace_closing = '\n'.join(
            ['}}  // namespace {}'.format(namespace_part)
             for namespace_part in reversed(namespace_parts)])
        # yapf: enable
        blocks.append(namespace_closing)

    blocks.append(mapry.cpp.generate.WARNING)

    return mapry.indention.reindent(
        text='\n\n'.join(blocks) + '\n', indention=cpp.indention)
