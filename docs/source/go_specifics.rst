Go Specifics
============
Mapry generates a Go package with structures and several public functions for
de/serialization from/to JSONable objects given as `interface{}`.

Settings
--------
In order to generate the Go code, you need to specify the Go specific setting in
the schema:

``package``
   indicates the package name of the generated code.

Generated Code
--------------
All the files are generated in a single directory. The code lives in the
package indicated by the Go setting ``package`` of the schema.

Mapry writes the following files (in order of abstraction):

* ``types.go`` defines all the structures of the object graph (embeddable
  structures, classes, object graph itself *etc.*)

* ``parse.go`` defines general parsing structures and their handling (such as
  parsing errors).

* ``fromjsonable.go`` provides functions for parsing the object graph from a
  JSONable ``interface{}`` value.

* ``tojsonable.go`` gives you functions for serializing the object graph to a
  JSONable ``interface{}`` value.

The example of the generated code for the schema given in
:ref:`schema:Introductory Example` is available
`in the repository <https://github.com/Parquery/mapry/blob/master/test_cases/docs/schema/introductory_example/go/test_generate>`_.

Deserialization
---------------

Assuming the schema provided in :ref:`schema:Introductory Example`, you
deserialize the object graph from a JSONable ``interface{}`` as follows.

.. code-block:: Go

    var value interface{}
    // ... parse the value from a source, e.g., a file

    pipeline := &address.Pipeline{}
    errors := address.NewErrors(0)

    const referencePath = "/path/to/the/file.json#"

    address.PipelineFromJSONable(
        value,
        referencePath,
        pipeline,
        errors)

    if !errors.Empty() {
        ee := errors.Values()
        for i := 0; i < len(ee); i++ {
            fmt.Fprintf(
                os.Stderr, "%s: %s\n",
                ee[i].Ref, ee[i].Message)
        }
        return 1
    }

The access to the deserialized object graph ``pipeline`` is straight-forward:

.. code-block:: Go

    fmt.Println("Maintainers are:")
    for _, m := range pipeline.maintainers {
        fmt.Printf(
            "%s (address: %s)\n",
            m.full_name, m.address.text)
    }

Serialization
-------------
Assuming the deserialized ``pipeline``, you serialize it back into a JSONable
``map[string]interface{}``:

.. code-block:: Go

    var err error
    var jsonable map[string]interface{}
    jsonable, err = address.PipelineToJSONable(pipeline)

Implementation Details
----------------------
Representation
^^^^^^^^^^^^^^
Go representation of Mapry types tries to be as straight-forward as possible.
The following tables show how Mapry types are mapped to Go types in generated
Go code.

.. list-table:: Primitive types

    *   - Mapry type
        - Go type
    *   - Boolean
        - ``bool``
    *   - Integer
        - ``int64``
    *   - Float
        - ``float64``
    *   - String
        - ``string``
    *   - Path
        - ``string``
    *   - Date
        - ``time.Time``
    *   - Time
        - ``time.Time``
    *   - Datetime
        - ``time.Time``
    *   - Time zone
        - ``*time.Location``
    *   - Duration
        - ``time.Duration``

.. list-table:: Aggregated types (of a generic type T)

    *   - Mapry type
        - Go type
    *   - Array
        - ``[]T``
    *   - Map
        - ``map[string]T``

.. list-table:: Composite types

    *   - Mapry type
        - Go type
    *   - Reference to an instance of class T
        - ``*T``
    *   - Embeddable structure T
        - ``struct T``
    *   - Optional property of type T
        - ``*T``

.. list-table:: Graph-specific structures

    *   - Mapry type
        - Go type
    *   - Registry of instances of class T
        - ``map[string]*T``


Numbers
^^^^^^^
The standard `encoding/json <https://golang.org/pkg/encoding/json/>`_ package
uses double-precision floating-point numbers (``float64``) to represent both
floating-point and integral numbers. Mapry-generated Go code follows this
approach and assumes that all numbers are represented as ``float64``. This
assumption has various implications on what numbers can be represented.

The set of representable floating-point numbers equals thus that of
``float64``, namely -1.7976931348623157e+308 to 1.7976931348623157e+308 with the
smallest above zero being 2.2250738585072014e-308. Hence Mapry also represents
floating points as ``float64``.

Unlike floating-point numbers, which are simply mirroring internal and JSONable
representation, Mapry represents integers as ``int64`` which conflicts with
JSONable representation of numbers as ``float64``. Namely, according to
`IEEE 754 standard <https://ieeexplore.ieee.org/document/4610935>`_, ``float64``
use 53 bits to represent digits and  11 bits for the exponent. This means that
you can represent all the integers in the range [-2^53, 2^53] (2^53 ==
9,007,199,254,740,992) without a loss of precision. However, as you cross 2^53,
you lose precision and the set of representable integers becomes sparse. For
example, 2^53 + 7 is 9,007,199,254,740,999 while it will be represented as
9,007,199,254,741,000.0 (2^53 + 8) in ``float64``. Hence, you can precisely
represent 2^53 + 8, but not 2^53 + 7, in your JSONable.

Unfortunately, most JSON-decoding packages (*e.g.,*
`encoding/json <https://golang.org/pkg/encoding/json/>`_) will silently ignore
this loss of precision. For example, assume you supply a string encoding a JSON
object containing an integer property set to 2^53 + 7. You pass this string
through ``encoding/json`` to obtain a JSONable and then pass it on to Mapry for
further parsing. Since Mapry does not directly operate on the string, but on an
intermediate JSONable representation (which represents numbers as ``float64``),
your Mapry structure ends up with integer representations that diverges from the
original string.

Note that this is a practical problem and not merely a theoretical one. For
example, unique identifiers are often encoded as 64-bit integers. If they are
generated randomly (or use 64-bits to encode extra information *etc.*) you
should represent them in JSON as strings and not numbers. Otherwise, you will
get an invalid unique identifier once you decode the JSON.

Furthermore, Mapry representation of integers with 64-bits restricts the range
of representable integers to [-2^64, 2^64 - 1] (-9,223,372,036,854,775,808 to
9,223,372,036,854,775,807). In contrast, JSONable representation uses
``float64`` and hence can represent the above-mentioned wider range of
``float64`` (-1.8e+308 to 1.8e+308). Due to this difference in representations,
Mapry-generated code will raise an error if a number needs to be parsed into an
integer that is out of 64-bit range.

Date/time Format Directives
^^^^^^^^^^^^^^^^^^^^^^^^^^^
Go standard package ``time`` diverges from many other languages (including
C++ and Python) in that it does not support strftime/strptime directives, but
a special (american-centered) date/time format of its own (see
`time.Format <https://golang.org/pkg/time/#Time.Format>`_). Such format causes
a couple of repercussions:

 * First, fractions of seconds are not supported (akin to
   C/C++ ``ctime`` library).
 * Second, certain parts of the format, while unproblematic in strftime
   directives, cause conflicts in Go. For example, the format
   ``"Sun goes up: %Y-%m-%d %H:%M:%S"`` will be misinterpreted since ``Sun``
   will be understood as abbreviated weekday in Go. Mapry detects such conflicts
   as soon as you try to generate Go code and raise an error. However, we leave
   it to the user to decide to generate code in other languages even though
   Go code can not be generated.

   Unfortunately, escape codes are not supported in ``time`` package and this
   problem can not be resolved.

Durations
^^^^^^^^^
Go represents durations as ``time.Duration`` which in fact counts the
nanoseconds as ``int64`` (see
`time.Duration <https://golang.org/pkg/time/#Duration>`_).

Mapry will parse the duration strings into ``time.Duration``. Similar to
problems in C++ generated code (see :ref:`cpp_specifics:Durations`),
``time.Duration`` can not capture all the strings representable by ISO 8601
period strings. Number of nanoseconds are limited by the range of ``int64`` and
can not span periods as short as 300 years (``PY300``). Furthermore, periods
at finer granularity than nanoseconds are impossible to parse either (*e.g.*,
``PT0.00000000004``). If you need to specify such durations, you need to specify
the value as string and parse them manually.

Mind that durations in other language might introduce additional constraints.
For example, Python represents durations as microseconds (see
:ref:`Durations in Python <py_specifics:Durations>`).
