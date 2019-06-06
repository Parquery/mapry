Schema
======
The Mapry schema defines the properties and structures of the object graph in a
single JSON file. This file is parsed by Mapry to generate the
dedicated de/serialization code in the respective languages.

The schema is split in following sections:

 * graph name and description,
 * language-specific settings,
 * definition of composite structures (classes and embeddable structures,
   see below) and
 * definition of graph properties.

Introductory Example
--------------------
Before we dwell into the separate sections, let us present a brief example
of a schema to give you an overview:

.. code-block:: json

    {
      "name": "Pipeline",
      "description": "defines an address book.",
      "cpp": {
        "namespace": "book::address",
        "path_as": "boost::filesystem::path",
        "optional_as": "std::experimental::optional",
        "datetime_library": "ctime"
      },
      "go": {
        "package": "address"
      },
      "py": {
        "module_name": "book.address",
        "path_as": "pathlib.Path",
        "timezone_as": "pytz.timezone"
      },
      "classes": [
        {
          "name": "Person",
          "description": "defines a contactable person.",
          "properties": {
            "full_name": {
              "type": "string",
              "description": "gives the full name (including middle names)."
            },
            "address": {
              "type": "Address",
              "description": "notes where the person lives.",
            }
          }
        }
      ],
      "embeds": [
        {
          "name": "Address",
          "description": "defines an address.",
          "properties": {
            "text": {
              "type": "string",
              "description": "gives the full address."
            }
          }
        }
      ],
      "properties": {
        "maintainer": {
          "type": "Person",
          "description": "indicates the maintainer of the address book."
        }
      }
    }

Language-specific Settings
--------------------------
Language-specific settings instruct Mapry how to deal with non-standard
structures during code generation. For example, you need to instruct which path
library to use in Python to represent file system paths (``str`` or
``pathlib.Path``). Note that settings can be specified only for a subset of
languages. For example, you can omit C++ settings if you are going to generate
the code only in Go and Python.

The available settings are explained for each language in the
:doc:`cpp_specifics`, :doc:`go_specifics` and :doc:`py_specifics`, respectively.

Data Types
----------
Mapry defines three families of data types: primitive data types (*primitives*),
aggregated data types (*aggregated*) and composite data types (*composites*).

**Primitives** are the basic data types such as booleans and integers.

**Aggregated** represent data structures which contain other data structures as
values. Mapry provides two aggregated data types: arrays and maps.

**Composites** represent data structures which contain **properties**. Each
property of a composite has a name and a corresponding data type. Three types of
composites are available in Mapry: classes, embeddable structures and an object
graph.

The following subsections describe the data types, instruct you how to define
them in the schema and how to impose constraints to further specify them.
For implementation details in different languages, please consult:
:doc:`cpp_specifics`, :doc:`go_specifics` and :doc:`py_specifics`.

For a summary of how Mapry represents the data types described below,
see :ref:`schema:JSON Representation`.

Primitive Types
^^^^^^^^^^^^^^^
``boolean``
    designates a value can be either true or false.

    Booleans are represented in Mapry as JSON booleans.

``integer``
    defines an integer number.

    You can constrain integers by a minimum and maximum properties
    (``minimum`` and ``maximum``, respectively). Following JSON schema,
    Mapry assumes inclusive limits, unless you specify them otherwise
    with boolean ``exclusive_minimum`` and ``exclusive_maximum``
    properties.

    Integers are represented as JSON numbers.

    Note that different languages can represent different (and mutually
    possibly incompatible!) ranges of integers. See
    :ref:`cpp_specifics:Numbers`, :ref:`go_specifics:Numbers` and
    :ref:`py_specifics:Numbers` for more details.

``float``
    specifies a floating-point number.

    Analogous to integers, floating-point numbers can be further constrained
    by minimum and maximum properties (``minimum`` and ``maximum``,
    respectively). These limits are tacitly assumed inclusive. You can
    specify exclusive limits by setting ``exclusive_minimum`` and/or
    ``exclusive_maximum`` properties to true, respectively.

    Floating-point numbers are represented as JSON numbers.

    Note that different languages can represent different (and mutually
    possibly incompatible!) ranges of floating-point numbers. See
    :ref:`cpp_specifics:Numbers`, :ref:`go_specifics:Numbers` and
    :ref:`py_specifics:Numbers` for more details.

``string``
    denotes a string of characters.

    You can enforce a string to follow a regular expression by defining
    the ``pattern`` property.

    Mapry represents strings as JSON strings.

``path``
    represents a path in a file system.

    Similar to strings, paths can also be restricted to comply to a
    regular expression by specifying the ``pattern`` property.

    Paths are represented as JSON strings in Mapry.

``date``
    designates a day in time.

    The time zone is not explicitly given, and needs to be assumed
    implicitly by the user or specified separately as a related
    time zone value (see below).

    The dates are represented as JSON strings and expected in ISO 8601
    format (*e.g.*, ``"2016-07-03"``). If your dates need to follow
    a different format, you need to specify the ``format`` property.
    Supported format directives are listed in :ref:`schema:Date/time Format`.

``time``
    ticks a time of day.

    Mapry represents time of day as JSON strings and assumes them by default
    in ISO 8601 format (*e.g.*, ``"21:07:34"``). However, you can change
    the format by setting the ``format`` property. For a list of available
    format directives, see :ref:`schema:Date/time Format`.

``datetime``
    fixes an instant (time of day + day in time).

    Parallel to ``date``, the datetime does not explicitly assume
    a time zone. The user either presumes the zone by a convention
    or specifies it as a separate time zone value (see below).

    Just as ``date`` and ``time`` so is ``datetime`` represented as
    JSON string in ISO 8601 format (*e.g.*, ``"2016-07-03T21:07:34Z"``)
    implicitly assuming
    `UTC time zone <https://en.wikipedia.org/wiki/Coordinated_Universal_Time>`_.
    If you want to have a datetime value in a different format, you have to set
    the ``format`` property. See :ref:`schema:Date/time Format` for a
    list of format directives.

``time_zone``
    pins a time zone.

    Time zone values are useful as companion values to date and
    datetimes.

    Mapry represents time zones as JSON strings, identified by entries
    in `IANA time zone database <https://www.iana.org/time-zones>`_.

    For example, ``"Europe/Zurich"``

``duration``
    measures a duration between two instants.

    The granularity and range of representable durations differs between
    languages (see :ref:`cpp_specifics:Durations`,
    :ref:`go_specifics:Durations` and :ref:`py_specifics:Durations`).

    Durations can be both positives and negatives. Following
    `C++ std::chrono library <https://en.cppreference.com/w/cpp/chrono/duration>`_,
    Mapry assumes a year as average year (365.2425 days) and a month as
    average month (30.436875 days). If a duration should denote actual months
    from a given starting date, you have to represent the duration as strings
    and manually parse them by a third-party library (*e.g.*,
    `isodate (Python) <https://pypi.org/project/isodate/>`_).

    For example, ``"P6M2.1DT3H54M12.54S"`` (6 months, 2.1 days, 3 hours,
    54 minutes and 12.54 seconds).

    Note that different languages can represent different (and mutually
    possibly incompatible!) granularities and ranges of durations. See
    :ref:`cpp_specifics:Durations`, :ref:`go_specifics:Durations` and
    :ref:`py_specifics:Durations` for more details.

Aggregated Types
^^^^^^^^^^^^^^^^
``array``
    lists an ordered sequence of values.

    Mapry arrays are strongly typed and you need to specify
    the type of the values as ``values`` property.

    The minimum and maximum size of the array (inclusive) can be
    further specified with the properties ``minimum_size`` and
    ``maximum_size``, respectively.

    If you need to capture tuples, you can define an array of both
    minimum and maximum size set to the same number.

    Arrays are represented as JSON arrays.

``map``
    projects strings to values (in other words, indexes values by strings).

    Map values are strongly typed in Mapry and need to be defined
    as ``values`` property.

    Mapry represents maps as JSON objects.

Composite Types
^^^^^^^^^^^^^^^
Primitive and aggregated data types are the building blocks of a Mapry schema.
They are further structured into **classes** and **embeddable structures**.
Think of these structures as floors or building units. The whole building
is further represented as an **object graph**, the encompassing data type.
Composite data types are defined by their **properties**. All composite data
types must be given names.

Mapry represents instances of composite data types as JSON objects where
properties of the JSON object correspond to the properties defined for the
composite data type.

Classes
    are referencable composite data types. Each instance of a class has a unique
    identity which serves as a reference.

    Classes are defined as a list of objects as ``classes`` property of the
    schema. The order of the definitions is mimicked in the generated code
    as much as possible.

    Each class needs to define the ``name`` and ``description``.
    The plural form of the class instances can be specified as ``plural``. If
    no plural is specified, Mapry infers the plural form using a heuristic.
    A class can define an ``id_pattern``, a regular expression, which mandates
    the pattern of the instance identifiers of the class.

    The properties of the class are specified as ``properties`` property of the
    class definition in the schema. See below how
    ``properties`` are defined. If a class defines no properties then
    ``properties`` can be omitted.

Embeddable structures
    are nested within other composite data types.

    Embeddable structures are given as a list of objects as ``embeds`` property
    of the schema. The order of the definitions matters, and Mapry tries to
    follow it when generating the code.

    Each embeddable structure needs to specify its ``name`` and ``description``.
    Properties, if any, are given as ``properties`` property of the definition.
    See below how ``properties`` are specified.

Graph object
    is the encompassing data type corresponding to the schema.

    The graph object needs to have a ``name`` and a ``description``.

    The properties of graph object itself, if available, are defined as
    ``properties`` property of the schema.

    The classes and embeddable structures are defined as ``classes`` and
    ``embeds`` properties of the schema, respectively.

Properties
    are the essence of composite data types. The ``properties`` of a composite
    type (be it class, embeddable structure or graph object) map property names
    to property definitions given as JSON objects in the schema.

    A property type can be either a primitive data type, an aggregated data
    type, a reference to a class or a nested embeddable structure. The type
    of the property is given as ``type`` property of the property definition.
    The ``type`` corresponds either to the name of the primitive, aggregated
    or composite type.

    Each property must have a ``description`` written as a JSON string in the
    property definition.

    Properties are assumed mandatory by default. You can specify that a property
    is optional by setting the ``optional`` to true in the property definition.
    Mapry will raise an error when parsing a JSONable object representing the
    composite which lacks a mandatory property. On the other side, optional
    properties can be simply omitted in the JSONable. If you need to evolve
    a schema over time, optional properties provide you a practical approach to
    handle different versions of a composite.

    Mapry uses a heuristic to determine the property name in the JSONable object
    representing the composite (see :ref:`schema:JSON Representation`).
    In most cases, you can leave Mapry decide the property names for you.
    However, you can specify a different property name of the respective
    JSONable by setting ``json`` property in the property definition if for some
    reason you need to evolve the name or need to follow an external convention
    incompatible with the heuristic.

    The additional constraints of primitive and aggregated types (such as
    minimum value of an integer or minimum size of an array) are given as
    additional properties in the property definition.


JSON Representation
^^^^^^^^^^^^^^^^^^^
Mapry represents an instance of an object graph as a JSON object. Properties
of the object graph are directly represented as properties of that JSON object.
While this works for unreferencable data types (primitive and aggregated
data types and embeddable structures), instances of the classes need a special
treatment.

Namely, instances of the classes are represented in an *instance registry* as
JSON objects. Each property of the instance registry corresponds to an instance
of the class: the identifier is the property name (*i.e.* a key), while the
instance is the property value given as a nested JSON object (*i.e.* a value,
with properties of that nested JSON object corresponding to the properties of
the class).

Each instance registry is given as an additional property of the object graph.
The name of the instance registries corresponds to the lowercase ``plural``
property of the class (if no ``plural`` is given, then the name of the instance
registry is inferred by a heuristic).

References to an instance of a class in an object graph are given as JSON
strings.

The following table summarizes how individual types are represented in
JSONables.

.. list-table::

    *   - Mapry Type
        - JSON Type
        - JSON Example
    *   - boolean
        - boolean
        - ``true``
    *   - integer
        - number
        - ``2016``
    *   - float
        - number
        - ``198.4``
    *   - string
        - string
        - ``"some text"``
    *   - path
        - string
        - ``"/a/path/to/somewhere"``
    *   - date
        - string
        - ``"2016-07-03"``
    *   - time
        - string
        - ``"21:07:34"``
    *   - datetime
        - string
        - ``"2016-07-03T21:07:34Z"``
    *   - time_zone
        - string
        - ``"Europe/Zurich"``
    *   - duration
        - string
        - ``"P2DT3H54M12.54S"``
    *   - array
        - array
        - ``[1, 2, 3]``
    *   - map
        - object
        - ``{"someKey": 1, "anotherKey": 3}``
    *   - embeddable structure
        - object
        - .. code-block:: json

            {
                "someProperty": 23,
                "anotherProperty": "some text"
            }

    *   - instance of a class
        - object
        - .. code-block:: json

            {
                "someProperty": 23,
                "anotherProperty": "some text"
            }

    *   - reference to an instance of a class
        - string
        - ``"some-id"``
    *   - object graph
        - object
        - .. code-block:: json

                {
                    "persons": {
                        "Alice": {
                            "birthday": "2016-07-03",
                            "bff": "Bob"
                        },
                        "Bob": {
                            "birthday": "2015-03-21"
                        },
                        "Chris": {
                            "birthday": "2016-11-15",
                            "bff": "Bob"
                        }
                    },
                    "maintainer": "Bob"
                }

Date/time Format
----------------
Representation of date/times in Mapry matches ISO 8601 by default
(``"2016-07-03"``, ``"21:07:34"`` and ``"2016-07-03T21:07:34Z"``). This works
perfectly fine for cases where you control the data and can assume that the
reference time zone is
`UTC <https://en.wikipedia.org/wiki/Coordinated_Universal_Time>`_.
Yet when you do not control the data, *e.g*, when it comes from external
sources, you need to adapt the expected date/time format.

Mapry allows you to specify the format of a date/time through ``format``
constraint consisting of widely-used strptime/strftime directives (*e.g.*, see
`strftime and strptime behavior in Python <https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior>`_
and
`ctime strftime in C++ <http://www.cplusplus.com/reference/ctime/strftime/>`_).
Since code needs to be generated in multiple languages and not all languages
support all the directives, only a subset of the directives are available:

.. list-table::

    *   - Diractive
        - Description
    *   - ``%a``
        - The abbreviated weekday name ("Sun")
    *   - ``%A``
        - The full weekday name ("Sunday")
    *   - ``%b``
        - The abbreviated month name ("Jan")
    *   - ``%B``
        - The full month name ("January")
    *   - ``%d``
        - Day of the month (01..31)
    *   - ``%e``
        - Day of the month with a leading blank instead of zero ( 1..31)
    *   - ``%m``
        - Month of the year (01..12)
    *   - ``%y``
        - Year without a century (00..99)
    *   - ``%Y``
        - Year with century
    *   - ``%H``
        - Hour of the day, 24-hour clock (00..23)
    *   - ``%I``
        - Hour of the day, 12-hour clock (01..12)
    *   - ``%l``
        - Hour of the day, 12-hour clock without a leading zero (1..12)
    *   - ``%M``
        - Minute of the hour (00..59)
    *   - ``%P``
        - Meridian indicator ("am" or "pm")
    *   - ``%p``
        - Meridian indicator ("AM" or "PM")
    *   - ``%S``
        - Second of the minute (00..60)
    *   - ``%z``
        - Time zone hour and minute offset from UTC
    *   - ``%Z``
        - Time zone name
    *   - ``%%``
        - Literal ``%`` character

For example, you can match month/day/year format with ``%m/%d/%Y`` or
day.month.year. hours:minutes:seconds with ``%d. %m. %Y %H:%M:%S``.

Mapry-generated code will use the standard date/time libraries (unless
otherwise specified in the language-specific settings). This means that the
implementation of the library determines how the directives are interpreted,
which could be sometimes ambiguous or not straight-forward to understand. For
example, time zone information (``%z`` and ``%Z`` directives) might be handled
differently by different implementations.

Additionally, due to lack of escaping in Go standard package ``time``, certain
formats can not be handled. See
:ref:`Go Date/time Format Directives <go_specifics:Date/time Format Directives>`
for details.

Conventions
-----------
Since Mapry needs to generate code in different languages, parts of the schema
such as property names and class descriptions need to follow certain conventions
to comply with the readability and style rules of the corresponding languages.

**Names of the object graph, classes and embeddable structures** are expected
as ``Sanke_case``. Abbreviations are expected as upper-case, *e.g.*,
``Some_IDs`` or ``Some_URLs``.

**Property names** are generally expected in ``snake_case`` with first word
lower-cased. Abbreviations are expected in upper-case even at the beginning
of a property name:
``some_IDs``, ``some_URLs``, ``IDs_to_store``, ``URLs_to_fetch``.

**Descriptions** should all end with a dot and start with a lower-case. The
descriptions should start with a lower-case verb in present tense, *e.g.*,
``indicates the maintainer of the address book.``

Further Examples
----------------
The brief example presented in :ref:`schema:Introductory Example` gives
you only an overview and lacks a comprehensive collection of use cases. To
further demonstrate how to define the object graphs and how they are represented
as JSONables in many different scenarios, we provide
the following table with links to examples.

.. list-table::

    *   - Description
        - Schema
        - Example representation
    *   - boolean
        - `schema <https://github.com/Parquery/mapry/blob/master/test_cases/general/primitive_type/boolean/schema.json>`__
        - `JSON file <https://github.com/Parquery/mapry/blob/master/test_cases/general/primitive_type/boolean/example_ok.json>`__
    *   - integer
        - `schema <https://github.com/Parquery/mapry/blob/master/test_cases/general/primitive_type/integer/schema.json>`__
        - `JSON file <https://github.com/Parquery/mapry/blob/master/test_cases/general/primitive_type/float/example_ok.json>`__
    *   - float
        - `schema <https://github.com/Parquery/mapry/blob/master/test_cases/general/primitive_type/float/schema.json>`__
        - `JSON file <https://github.com/Parquery/mapry/blob/master/test_cases/general/primitive_type/float/example_ok.json>`__
    *   - string
        - `schema <https://github.com/Parquery/mapry/blob/master/test_cases/general/primitive_type/string/schema.json>`__
        - `JSON file <https://github.com/Parquery/mapry/blob/master/test_cases/general/primitive_type/string/example_ok.json>`__
    *   - path
        - `schema <https://github.com/Parquery/mapry/blob/master/test_cases/general/primitive_type/path/schema.json>`__
        - `JSON file <https://github.com/Parquery/mapry/blob/master/test_cases/general/primitive_type/path/example_ok.json>`__
    *   - date
        - `schema <https://github.com/Parquery/mapry/blob/master/test_cases/general/primitive_type/date/schema.json>`__
        - `JSON file <https://github.com/Parquery/mapry/blob/master/test_cases/general/primitive_type/date/example_ok.json>`__
    *   - time
        - `schema <https://github.com/Parquery/mapry/blob/master/test_cases/general/primitive_type/time/schema.json>`__
        - `JSON file <https://github.com/Parquery/mapry/blob/master/test_cases/general/primitive_type/time/example_ok.json>`__
    *   - datetime
        - `schema <https://github.com/Parquery/mapry/blob/master/test_cases/general/primitive_type/datetime/schema.json>`__
        - `JSON file <https://github.com/Parquery/mapry/blob/master/test_cases/general/primitive_type/datetime/example_ok.json>`__
    *   - time_zone
        - `schema <https://github.com/Parquery/mapry/blob/master/test_cases/general/primitive_type/time_zone/schema.json>`__
        - `JSON file <https://github.com/Parquery/mapry/blob/master/test_cases/general/primitive_type/time_zone/example_ok.json>`__
    *   - duration
        - `schema <https://github.com/Parquery/mapry/blob/master/test_cases/general/primitive_type/duration/schema.json>`__
        - `JSON file <https://github.com/Parquery/mapry/blob/master/test_cases/general/primitive_type/duration/example_ok.json>`__
    *   - array
        - `schema <https://github.com/Parquery/mapry/blob/master/test_cases/general/array/of/boolean/schema.json>`__
        - `JSON file <https://github.com/Parquery/mapry/blob/master/test_cases/general/array/of/boolean/example_ok.json>`__
    *   - map
        - `schema <https://github.com/Parquery/mapry/blob/master/test_cases/general/map/schema.json>`__
        - `JSON file <https://github.com/Parquery/mapry/blob/master/test_cases/general/map/example_ok.json>`__
    *   - embeddable structure
        - `schema <https://github.com/Parquery/mapry/blob/master/test_cases/general/embed/schema.json>`__
        - `JSON file <https://github.com/Parquery/mapry/blob/master/test_cases/general/embed/example_ok.json>`__
    *   - class instances
        - `schema <https://github.com/Parquery/mapry/blob/master/test_cases/general/class/schema.json>`__
        - `JSON file <https://github.com/Parquery/mapry/blob/master/test_cases/general/class/example_ok.json>`__
    *   - optional property
        - `schema <https://github.com/Parquery/mapry/blob/master/test_cases/general/optional_in_graph/schema.json>`__
        - `JSON file <https://github.com/Parquery/mapry/blob/master/test_cases/general/optional_in_graph/example_ok.json>`__
    *   - differing JSON property
        - `schema <https://github.com/Parquery/mapry/blob/master/test_cases/general/json_property/schema.json>`__
        - `JSON file <https://github.com/Parquery/mapry/blob/master/test_cases/general/json_property/example_ok.json>`__

For yet more examples, please see
`the remainder of the test cases <https://github.com/Parquery/mapry/blob/master/test_cases>`_.
Each test case consists of a schema (``schema.json``),
generated code (``{language}/test_generate`` subdirectory) and
example JSON representations (``example_ok.json``, ``example_ok_*.json`` and
``example_fail_*.json``).
