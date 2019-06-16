Python Specifics
================
Mapry generates a Python module which defines structures
and several de/serialization functions translating from/to JSONable ``Any``
values.

Settings
--------
Mapry needs you to specify the following Python-specific settings in the schema:

``module_name``
    specifies the fully qualified base module name of the generated code.

    For example, ``book.address``.

``path_as``
    defines the type of the paths in the generated code.

    Mapry supports: ``str`` and ``pathlib.Path``.

``timezone_as``
    defines the type of the time zones in the generated code.

    Mapry supports: ``str`` and ``pytz.timezone``.

``indention``
    defines the indention of the generated code. Defaults to four spaces and
    can be omitted.

    For example, ``"  "`` (two spaces)

Generated Code
--------------
All the files live in a single directory. The module intra-dependencies are
referenced using the fully qualified base module name given as ``module_name``
in the schema.

Here is the overview of the generated files (in order of abstraction).

* ``__init__.py`` defines the general structures of the object graph (embeddable
  structures, classes, object graph itself *etc.*).
* ``parse.py`` defines general parsing structures such as parsing errors.
* ``fromjsonable.py`` defines parsing of the object graph from a JSONable
  dictionary.
* ``tojsonable.py`` defines serialization of the object graph to a JSONable
  dictionary.

The example of the generated code for the schema given in
:ref:`schema:Introductory Example` is available
`in the repository <https://github.com/Parquery/mapry/blob/master/test_cases/docs/schema/introductory_example/py/test_generate>`_.

Deserialization
---------------
Given the schema provided in :ref:`schema:Introductory Example` and assuming you obtained
the JSONable value using, *e.g.*, ``json`` module from the
standard library, you deserialize it to an object graph as follows.

.. code-block:: Python

    # Obtain a JSONable
    pth = '/path/to/the/file.json'
    with open(pth, 'rt') as fid:
        value = json.load(fid)

    # Parse the JSONable
    errors = book.address.parse.Errors(cap=10)

    pipeline = book.address.fromjsonable.pipeline_from(
        value=value,
        ref=pth + '#',
        errors=errors)

    if not errors.empty():
        for error in errors.values():
            print("{}: {}".format(error.ref, error.message), file=sys.stderr)

        return 1

You can now access the object graph ``pipeline``:

.. code-block:: Python

    print('Maintainers are:')
    for maintainer in pipeline.maintainers:
        print('{} (address: {})'.format(
            maintainer.full_name,
            maintainer.address.text))

Serialization
-------------
You serialize back the object graph ``pipeline`` into a JSONable by:

.. code-block:: Python

    jsonable = book.address.tojsonable.serialize_pipeline(
        pipeline,
        ordered=True)

The ``jsonable`` can be further serialized to a string by ``json.dumps(.)``
from the standard library:

.. code-block:: Python

    text = json.dumps(jsonable)

Implementation Details
----------------------
Representation
^^^^^^^^^^^^^^
Mapry directly maps its types to corresponding Python types. The mapping is
presented in The following tables.

.. list-table:: Primitive types

    *   - Mapry type
        - Python type
    *   - Boolean
        - ``bool``
    *   - Integer
        - ``int``
    *   - Float
        - ``float``
    *   - String
        - ``str``
    *   - Path
        - ``str`` or ``pathlib.Path``

          (depending on ``path_as`` setting)
    *   - Date
        - ``datetime.date``
    *   - Time
        - ``datetime.time``
    *   - Datetime
        - ``datetime.datetime``
    *   - Time zone
        - ``str`` or ``datetime.tzinfo``

          (depending on ``timezone_as`` setting)
    *   - Duration
        - ``datetime.timedelta``

.. list-table:: Aggregated types (of a generic type T)

    *   - Mapry type
        - Python type
    *   - Array
        - ``typing.List[T]``
    *   - Map
        - ``typing.MutableMapping[str, T]``

.. list-table:: Composite types

    *   - Mapry type
        - Python type
    *   - Reference to an instance of class T
        - ``T``
    *   - Optional property of type T
        - ``typing.Optional[T]``


.. list-table:: Graph-specific structures

    *   - Mapry type
        - Python type
    *   - Registry of instances of class T
        - ``typing.MutableMapping[str, T]``

Unordered and Ordered Mappings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
When parsing a JSONable, Mapry inspects the types of the mappings to decide
whether to keep or ignore the order of the keys. Namely, if the mapping
is an instance of ``collections.OrderedDict``, the corresponding Mapry
representation will also be ``collections.OrderedDict``. Analogously for an
unordered mapping, if the JSONable mapping is given as ``dict``, Mapry will also
represent it as ``dict``. This distinction is applied both to Mapry maps as well
as registries of class instances.

When you serialize a Mapry structure to a JSONable, it is up to you to decide
whether you want the mappings ordered or not. This is specified with the
``ordered`` argument. For example, consider a function generated to serialize
the graph from :ref:`schema:Introductory Example`:

.. code-block:: Python

    def serialize_pipeline(
            instance: book.address.Pipeline,
            ordered: bool = False
    ) -> typing.MutableMapping[str, typing.Any]:
        """
        serializes an instance of Pipeline to a JSONable.

        :param instance: the instance of Pipeline to be serialized
        :param ordered:
            If set, represents the instance properties and class registries
            as a ``collections.OrderedDict``.
            Otherwise, they are represented as a ``dict``.
        :return: JSONable representation
        """
        if ordered:
            target = (
                collections.OrderedDict()
            )  # type: typing.MutableMapping[str, typing.Any]
        else:
            target = dict()

        ...

        return target

Numbers
^^^^^^^
Python 3 represents integer numbers as an unbounded ``int`` (see
`stdtypes <https://docs.python.org/3/library/stdtypes.html#typesnumeric>`_),
unlike C++ or Go (*e.g.*, see :ref:`Numbers in C++ <cpp_specifics:Numbers>` or
:ref:`Numbers in Go <go_specifics:Numbers>`, respectively) which represents
numbers with bounded 64-bits integers. Since Mapry also relies on ``int`` to
represent integers, this means that you can use unbounded integer representation
in generated Python code as long as this code does not need to work with other
languages.

This is particularly important when you serialize Mapry structures into
JSONables. As soon as you need interoperability with, say, C++ or Go, the
resulting JSONable will fail to parse. This is a limitation that Mapry does not
check for at the moment. We leave it to the user of the generated code to decide
how it will be used and what extra checks need to be performed since the
JSONable is valid from the point-of-view of the Python 3 code.

In contrast to integers, Python 3 represents floating-point numbers (``float``)
with a bounded 64-bit double-precision numbers (according to
`IEEE 754 <https://ieeexplore.ieee.org/document/4610935>`_). This
representation is also used by Mapry. This limits the range of representable
numbers from -1.7976931348623157e+308 to 1.7976931348623157e+308. Note also that
the closer you get to the range bounds, the sparser the representable numbers
due to how floating-point numbers are represented by IEEE 754.

Durations
^^^^^^^^^
Durations are given in Python 3 as ``datetime.timedelta``, a structured
normalized representation of days, seconds and microseconds (see
`datetime.timedelta <https://docs.python.org/3/library/datetime.html#timedelta-objects>`_)
between two instants.

The internal representation introduces the following limits:

 * 0 <= microseconds < 1000000
 * 0 <= seconds < 3600*24 (the number of seconds in one day)
 * -999999999 <= days <= 999999999

When fraction of microseconds are specified:

.. pull-quote::

    If any argument is a float and there are fractional microseconds, the
    fractional microseconds left over from all arguments are combined and their
    sum is rounded to the nearest microsecond using round-half-to-even
    tiebreaker. If no argument is a float, the conversion and normalization
    processes are exact (no information is lost).

Such internal timedelta structures can pose problems when you are de/serializing
from JSONables coming from the code generated in other languages. You face
a mismatch in granularity and range (see
:ref:`Durations in C++ <cpp_specifics:Durations>` and
:ref:`Durations in Go <go_specifics:Durations>`).

Mapry generates C++ and Go code which uses nanoseconds to specify durations.
The durations of nanosecond granularity can not be captured in
Python 3 since Python 3 stores only microseconds and not nanoseconds. This can
cause silent hard-to-trace truncation since Python 3 stores microseconds.

Second, ``datetime.timedelta`` spans a practically inexhaustible time frame
which can not be fit into 64-bit integers use to represent nanoseconds in C++
and Go and can lead to overflows. For example, you can represent ``PY300``
without problems as duration in Mapry-generated Python 3 code, but it will
overflow in C++ and Go code.

If you need to handle fine-grained and/or long durations in different languages,
you better pick either a custom string or integer representation that aligns
better with your particular use case.
