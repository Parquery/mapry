"""Generate the header of the general parsing structures."""
import textwrap

from icontract import ensure

import mapry
import mapry.cpp.generate
import mapry.indention


@ensure(lambda result: not result.endswith('\n'))
def _parse_definitions() -> str:
    """
    Generate the code that defines the general parsing structures.

    :return: generated code
    """
    return textwrap.dedent(
        '''\
        /**
         * represents an error occurred while parsing.
         */
        struct Error {
            // references the cause (e.g., a reference path).
            const std::string ref;

            // describes the error.
            const std::string message;
        };

        /**
         * collects errors capped at a certain quantity.
         *
         * The space for the errors will not be reserved.
         * Make sure you reserve the necessary space by calling reserve()
         * at the initialization.
         */
        class Errors {
        public:
            explicit Errors(size_t cap);

            /**
             * reserves the space for the errors.
             *
             * You need to reserve the space only if you think there will
             * be an excessive amount of errors (e.g., >1000).
             */
             void reserve(size_t expected_errors);

            /**
             * adds an error to the container.
             *
             * If the container is already full, the error is ignored.
             */
            void add(const std::string& ref, const std::string& message);

            /**
             * @return true when there are exactly cap errors.
             */
            bool full() const;

            /**
             * @return true when there are no errors.
             */
            bool empty() const;

            const std::vector<Error>& get() const;

        private:
            const size_t cap_;
            std::vector<Error> errors_;
        };''')


@ensure(lambda result: result.endswith('\n'))
def generate(cpp: mapry.Cpp) -> str:
    """
    Generate the header file defining the parsing structures.

    :param cpp: C++ settings
    :return: content of the header file
    """
    blocks = [
        "#pragma once", mapry.cpp.generate.WARNING,
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

    blocks.append(_parse_definitions())

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
