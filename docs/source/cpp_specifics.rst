C++ Specifics
=============
Mapry produces a C++ runtime implementation with a simple interface for
de/serializing object graphs from
`Jsoncpp <https://github.com/open-source-parsers/jsoncpp>`_ values.

Settings
--------
You need to specify the C++ specific settings in a schema to instruct Mapry
how to generate the code. The following points needs to be defined:

``namespace``
    indicates the namespace of the generated code.

    For example, ``book::address``.

``path_as``
    defines the type of the paths in the generated code.

    Mapry supports: ``std::filesystem::path`` and ``boost::filesystem::path``.

``optional_as``
    defines the type of the optional properties in the generated code.

    Mapry supports: ``boost::optional``, ``std::optional`` and
    ``std::experimental::optional``.

``datetime_library``
    defines the library to use for date, datetime, time and time zone
    manipulation.

    Mapry supports: ``ctime`` and ``date.h`` (*i.e.*
    `Howard Hinnant's date library <https://howardhinnant.github.io/date/date.html>`_)

``idention``
    defines the indention of the generated code. Defaults to two spaces and
    can be omitted.

    For example, ``"    "`` (four spaces)

Generated Code
--------------
Mapry produces all the files in a single directory. The generated code lives
in the namespace indicated by C++ setting ``namespace`` in the schema.

Mapry generates the following files (in order of abstraction):

* ``types.h`` defines all the graph structures (embeddable structures,
  classes, object graph itself *etc.*).
* ``parse.h`` and ``parse.cpp`` define the structures used for parsing and
  implement their handling (such as parsing errors).
* ``jsoncpp.h`` and ``jsoncpp.cpp`` define and implement the de/serialization
  of the object graph from/to a
  `Jsoncpp <https://github.com/open-source-parsers/jsoncpp>`_ value.

The example of the generated code for the schema given in
:ref:`schema:Introductory Example` is available
`in the repository <https://github.com/Parquery/mapry/blob/master/test_cases/docs/schema/introductory_example/cpp/test_generate>`_.

Deserialization
---------------
The following snippet shows you how to deserialize the object graph from a
Jsoncpp value. We assume the schema as provided in
:ref:`schema:Introductory Example`.

.. code-block:: C++

    Json::Value value;
    // ... parse the value from a source, e.g., a file

    book::address::parse::Errors errors(1024);
    book::address::Pipeline pipeline;

    const std::string reference_path(
        "/path/to/the/file.json#");

    book::address::jsoncpp::pipeline_from(
        value,
        reference_path,
        &pipeline,
        &errors);

    if (not errors.empty()) {
        for (const auto& err : errors.get()) {
            std::cerr << err.ref << ": " << err.message << std::endl;
        }
        return 1;
    }

You can seamlessly access the properties and iterate over aggregated types:

.. code-block:: C++

    std::cout << "Maintainers are:" << std::endl;
    for (const book::address::Person& maintainer : pipeline.maintainers) {
        std::cout
            << maintainer.full_name
            << " (address: " << maintainer.address.text << ")"
            << std::endl;
    }


Serialization
-------------
You serialize the graph to a Jsoncpp value (assuming you predefined the variable
``pipeline``) simply with:

.. code-block:: C++

    const Json::Value value(
            book::address::jsoncpp::serialize_pipeline(
                pipeline));

Compilation
-----------
The generated code is *not* header-only. Since there is no standard C++ build
system and supporting the whole variety of build systems would have been overly
complex, we decided to simply let the user integrate the generated files into
their build system manually. For example, Mapry will *not* generate any CMake
files.

Here is an exerpt from a ``CMakeLists.txt`` (corresponding to the schema given
in :ref:`schema:Introductory Example`) that uses
`conan <https://conan.io/>`_ for managing dependencies:

.. code-block:: cmake

    add_executable(some_executable
        some_executable.cpp
        book/address/types.h
        book/address/parse.h
        book/address/parse.cpp
        book/address/jsoncpp.h
        book/address/jsoncpp.cpp)

    target_link_libraries(some_executable
        CONAN_PKG::jsoncpp
        CONAN_PKG::boost)

Implementation Details
----------------------
Representation
^^^^^^^^^^^^^^
Mapry represents the types defined in the schema as closely as possible
in C++. The following tables list how different types are represented in
generated C++ code.

.. list-table:: Primitive types

    *   - Mapry type
        - C++ type
    *   - Boolean
        - ``bool``
    *   - Integer
        - ``int64_t``
    *   - Float
        - ``double``
    *   - String
        - ``std::string``
    *   - Path
        - ``std::filesystem::path`` or ``boost::filesystem::path``

          (depending on ``path_as`` setting)
    *   - Date
        - ``struct tm`` or ``date::local_days``

          (depending on ``datetime_library`` setting)
    *   - Time
        - ``struct tm`` or ``date::time_of_day<std::chrono::seconds>``

          (depending on ``datetime_library`` setting)
    *   - Datetime
        - ``struct tm`` or ``date::local_seconds``

          (depending on ``datetime_library`` setting)
    *   - Time zone
        - ``std::string`` or ``const date::time_zone*``

          (depending on ``datetime_library`` setting)
    *   - Duration
        - ``std::chrono::nanoseconds``

.. list-table:: Aggregated types (of a generic type T)

    *   - Mapry type
        - C++ type
    *   - Array
        - ``std::vector<T>``
    *   - Map
        - ``std::map<std::string, T>``

.. list-table:: Composite Types

    *   - Mapry type
        - C++ type
    *   - Reference to an instance of class T
        - ``T*``
    *   - Embeddable structure T
        - ``struct T``
    *   - Optional property of type T
        - ``boost::optional<T>``,

          ``std::optional<T>`` or

          ``std::experimental::optional<T>``

          (depending on ``optional_as`` setting)

.. list-table:: Graph-specific structures

    *   - Mapry type
        - C++ type
    *   - Registry of instances of class T
        - ``std::map<std::string, T>``

Numbers
^^^^^^^
Mapry depends on the underlying JSON library for the representation of numbers.
How the library deals with numbers has implications on the ranges and precision
of the numbers that you can represent and can lead to unexpected overflows.

While `JSON standard <https://www.json.org/>`_ does not distinguishes between
integers and floats and treat all numbers equally,
`Jsoncpp <https://github.com/open-source-parsers/jsoncpp>`_ indeed distinguishes
between the integers (represented internally as 64-bit integers) and floats
(represented internally as double-precision floats).

Based on the internal representation, C++ deserialization can represent integers
in the range of 64-bit integers (-9,223,372,036,854,775,808 to
9,223,372,036,854,775,807) and floats in the rage of double-precision (
-1.7976931348623157e+308 to 1.7976931348623157e+308).

However, note that deserialization in other languages might impose stricter
constraints. For example, Go does not distinguish between integers and floats
when parsing JSON (see :ref:`Numbers in Go <go_specifics:Numbers>`), so the
overall range that you can represent is smaller if you need Go and C++
de/serialization to inter-operate.

Time Libraries
^^^^^^^^^^^^^^
Mapry generates the code that uses either the standard
`ctime <http://www.cplusplus.com/reference/ctime/>`_ library
or
`Howard Hinnant's date library (date.h) <https://howardhinnant.github.io/date/date.html>`_
to manipulate the dates, datetimes, times of the day and time zones based on
``datetime_library`` in C++ settings section of the schema.

Since ``ctime`` does not support a time zone registry, the time zones are parsed
as strings and are not further validated. For example, you can specify an
incorrect time zone such as ``Neverland/Magic`` and the deserialization code
will not complain.

On the other hand, since Howard Hinnant's date library (date.h) supports a
registry of IANA time zones, the time zones are in fact checked at
deserialization and an error will be raised if the time zone is invalid.

We would recommend you to use Howard Hinnant's date library (date.h) instead of
the standard ``ctime`` though it comes with an extra effort of installing the
dependenciy. In our opinion, the sophistication, the easy and the clarity Howard
Hinnant's library enforces on date/time manipulations pay off in long term.

The following table gives you a comparison of the generated codes:

Date
    ``ctime``:
    `schema <https://github.com/Parquery/mapry/blob/master/test_cases/general/primitive_type/date/schema.json>`__
    and
    `code <https://github.com/Parquery/mapry/tree/master/test_cases/general/primitive_type/date/cpp/test_generate>`__

    ``date.h``:
    `schema <https://github.com/Parquery/mapry/blob/master/test_cases/cpp/datetime_library_date/date/schema.json>`__
    and
    `code <https://github.com/Parquery/mapry/tree/master/test_cases/cpp/datetime_library_date/date/cpp/test_generate>`__

Datetime
    ``ctime``:
    `schema <https://github.com/Parquery/mapry/blob/master/test_cases/general/primitive_type/datetime/schema.json>`__
    and
    `code <https://github.com/Parquery/mapry/tree/master/test_cases/general/primitive_type/datetime/cpp/test_generate>`__

    ``date.h``:
    `schema <https://github.com/Parquery/mapry/blob/master/test_cases/cpp/datetime_library_date/datetime/schema.json>`__
    and
    `code <https://github.com/Parquery/mapry/tree/master/test_cases/cpp/datetime_library_date/datetime/cpp/test_generate>`__

Time of day
    ``ctime``:
    `schema <https://github.com/Parquery/mapry/blob/master/test_cases/general/primitive_type/time/schema.json>`__
    and
    `code <https://github.com/Parquery/mapry/tree/master/test_cases/general/primitive_type/time/cpp/test_generate>`__

    ``date.h``:
    `schema <https://github.com/Parquery/mapry/blob/master/test_cases/cpp/datetime_library_date/time/schema.json>`__
    and
    `code <https://github.com/Parquery/mapry/tree/master/test_cases/cpp/datetime_library_date/time/cpp/test_generate>`__

Time zone
    ``ctime``:
    `schema <https://github.com/Parquery/mapry/blob/master/test_cases/general/primitive_type/time_zone/schema.json>`__
    and
    `code <https://github.com/Parquery/mapry/tree/master/test_cases/general/primitive_type/time_zone/cpp/test_generate>`__

    ``date.h``:
    `schema <https://github.com/Parquery/mapry/blob/master/test_cases/cpp/datetime_library_date/time_zone/schema.json>`__
    and
    `code <https://github.com/Parquery/mapry/tree/master/test_cases/cpp/datetime_library_date/time_zone/cpp/test_generate>`__

Durations
^^^^^^^^^
Mapry uses standard
`std::chrono::nanoseconds <http://www.cplusplus.com/reference/chrono/nanoseconds/>`_
to represent durations. According to the standard, this implies that beneath the
hub a signed integral type of at least 64 bits is used to represent the count.

Since integral numbers of finite size are used for representation, the generated
code can only deal with a finite range of durations. In contrast, Mapry
durations are given as strings and thus can represent a much larger range of
durations (basically bounded only on available memory space).

In fact, the problem is very practical and you have to account for it when
you deal with long or fine-grained durations. For example, a duration specified
as ``P300Y`` already leads to an overflow since 300 years *can not* be
represented as nanoseconds with finite integral numbers of 64 bits.
Analogously, ``PT0.0000000001`` can not be represent either since the
precision of the duration goes beyond nanoseconds.

Note also that other languages impose stricter constraints. For example, Python
uses microseconds to represent durations (see
:ref:`Durations in Python <py_specifics:Durations>`) and
hence you need to restrict your durations to microsecond granularity if both
Python and C++ de/serializations are needed.
