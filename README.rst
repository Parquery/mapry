.. image:: https://raw.githubusercontent.com/Parquery/mapry/master/logo-640x320.png
   :alt: Mapry

.. image:: https://travis-ci.com/Parquery/mapry.svg?branch=master
    :target: https://travis-ci.com/Parquery/mapry

.. image:: https://coveralls.io/repos/github/Parquery/mapry/badge.svg?branch=master
    :target: https://coveralls.io/github/Parquery/mapry

.. image:: https://readthedocs.org/projects/mapry/badge/?version=latest
    :target: https://mapry.readthedocs.io/en/latest/
    :alt: Documentation Status

.. image:: https://badge.fury.io/py/mapry.svg
    :target: https://pypi.org/project/mapry/
    :alt: PyPI - version

.. image:: https://img.shields.io/pypi/pyversions/mapry.svg
    :target: https://pypi.org/project/mapry/
    :alt: PyPI - Python Version

Mapry generates polyglot code for de/serializing object graphs from
JSONable structures.

**Story**. We needed a yet another domain-specific language for internal data
exchange and configuration of the system. The existing solutions mostly focused
on modeling the configuration as *object trees* in which the data is nested in
hierarchies with no **cross-references** between the objects.

For example, think of object trees as JSON objects or arrays. We found this
structure to be highly limiting for most of the complex messages and system
configurations. Our use cases required objects in the data to be referenced
among each other -- instead of object trees we needed **object graphs**.

Moreover, we wanted the serialization itself to be **readable** so that an
operator can edit it using a simple text editor. JSONable structure offered
itself as a good fit with a lot of existing tools (JSON and
YAML modules *etc*.).

However, JSON allows only a limited set of data types (numbers, strings, arrays
and objects/maps). We found that most of our data relied on
**a richer set of primitives** than provided by standard JSON. This
extended set includes:

* date,
* datetime,
* time of day,
* time zone,
* duration and
* path.

While there exist polyglot serializers of object trees (*e.g.*,
`Protocol Buffers <https://developers.google.com/protocol-buffers/>`_),
language-specific serializers of object graphs (*e.g.,*
`Gob in Go <https://golang.org/pkg/encoding/gob/>`_ or
`Pickle in Python <https://docs.python.org/3/library/pickle.html>`_) or polyglot
ones with a limited set of primitives (*e.g.,*
`Flatbuffers <https://google.github.io/flatbuffers/>`_), to the best of our
knowledge there is currently no serializer of **object graphs** that operates
with **readable representations** and provides a
**rich set of primitive data types** consistently **across multiple languages**.

Hence we developed Mapry, a generator of polyglot de/serialization code
for object graphs from JSONable structures.

The **schema** of the object graph is stored in a separate JSON file and defines
all the data types used in the object graph including the object graph itself.
The code is generated based on the schema. You define the schema once and
generate code in all supported languages automatically. Schemas can be
evolved and backward compatibility is supported through optional properties.

Supported languages
-------------------
Currently, Mapry implements the following language bindings:

* C++11, 
* Go 1 and 
* Python 3.

Since the serialization needs to operate in different languages, only the
intersection of language features is supported. For example, since Go does not
support inheritance or union types, they are not supported in Mapry either.

Workflow
--------
The following diagram illustrates the workflow.

.. image:: https://raw.githubusercontent.com/Parquery/mapry/master/diagram.png

Documentation
=============

This document gives only a brief summary of Mapry. The full documentation can be
found `here <https://mapry.readthedocs.io/en/latest/>`_.

Introduction
============

Let us introduce Mapry here by presenting a short example in order to give you a first
impression on how the generator can be used. To get the full picture, please consult the
`documentation <https://mapry.readthedocs.io/en/latest/>`__.

The schema starts with the name and a description, followed by the
language-specific settings (specifying the non-standard parts of the code
generation), the definition of the graph structure and finally the definition of the properties of
the object graph itself.

Here is an example schema to give you an overview:

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
            "birthday": {
              "type": "date",
              "description": "indicates the birthday in UTC."
            },
            "address": {
              "type": "Address",
              "description": "notes where the person lives."
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

Once you generated the de/serialization code with Mapry, you can use it
to obtain the object graph from a JSONable.

For example, assume a JSONable stored in ``/path/to/the/file.json``:

.. code-block:: json

    {
      "persons": {
        "alice": {
          "full_name": "Alice Doe",
          "birthday": "1983-10-24",
          "address": {
            "text": "Some street 12, Some City, Some Country"
          }
        },
        "bob": {
          "full_name": "Bob Johnson",
          "birthday": "2016-07-03",
          "address": {
            "text": "Another street 36, Another City, Another Country"
          }
        }
      },
      "maintainer": "alice"
    } 

You can parse the object graph in, say, Python:

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

and access the object graph as ``pipeline``:

.. code-block:: Python

    print('Persons are:')
    for person in pipeline.persons:
        print('{} (full name: {}, address: {}, birthday: {})'.format(
            person.id,
            person.full_name,
            person.address.text,
            person.birthday.strftime("%d.%m.%Y")))

    print('The maintainer is: {}'.format(
        pipeline.maintainer.id))


The generated code for this schema can be downloaded for
`C++ <https://github.com/Parquery/mapry/blob/master/test_cases/docs/schema/introductory_example/cpp/test_generate>`_,
`Go <https://github.com/Parquery/mapry/blob/master/test_cases/docs/schema/introductory_example/py/test_generate>`_ and
`Python <https://github.com/Parquery/mapry/blob/master/test_cases/docs/schema/introductory_example/py/test_generate>`_.

Usage
=====

Mapry provides a single point-of-entry for all code generation through
``mapry-to`` command.

To generate the code in different languages, invoke:

For **C++**:

.. code-block:: bash

    mapry-to cpp \
        --schema /path/to/schema.json \
        --outdir /path/to/cpp/code

For **Go**:

.. code-block:: bash

    mapry-to go \
        --schema /path/to/schema.json \
        --outdir /path/to/go/code

For **Python**:

.. code-block:: bash

    mapry-to py \
        --schema /path/to/schema.json \
        --outdir /path/to/py/code

If the output directory does not exist, it will be created. Any existing
files will be silently overwritten.

Installation
============
We provide a prepackaged PEX file that can be readily downloaded and executed.
Please see the `Releases section <https://github.com/Parquery/mapry/releases>`_.

If you prefer to use Mapry as a library (*e.g.*, as part of your Python-based
build system), install it with pip:

.. code-block:: bash

    pip3 install mapry

Contributing
============
All contributions are highly welcome. Please consult this
`page <https://mapry.readthedocs.io/en/latest/contributing.html>`_
in the documentation to see how you can contribute.

Versioning
==========
We follow `Semantic Versioning <http://semver.org/spec/v1.0.0.html>`_.
We extended the standard semantic versioning with an additional format version.
The version W.X.Y.Z indicates:

* W is the format version (data representation is backward-incompatible),
* X is the major version (library interface is backward-incompatible),
* Y is the minor version (library interface is extended, but
  backward-compatible), and
* Z is the patch version (backward-compatible bug fix).

Related Projects
================
We compiled an extensive list of related projects and how they compare to Mapry
in the
`documentation <https://mapry.readthedocs.io/en/latest/related_projects.html>`__.

We present here only the most prominent projects and their main differences
to Mapry:

Standard JSON libraries
    support only object *trees*, not graphs. They usually lack a schema (*e.g.,*
    `json module in Python <https://docs.python.org/3/library/json.html>`_).

De/serializers based on annotations
    handle object graphs through custom logic (*e.g.,*
    `Jackson in Java <https://github.com/FasterXML/jackson>`_). Since they are
    based on annotations in source code, a polyglot code base would require
    a duplication across different languages which can be cumbersome and
    error-prone to keep synchronized.

Standard or widely used serialization libraries
    handle object graphs well and provide a rich set of primitives. However, the serialization
    format differs accross languagues (*e.g.*,
    `Boost.Serialization in C++ <https://www.boost.org/doc/libs/1_70_0/libs/serialization/doc/index.html>`_
    or `Pickle in Python <https://docs.python.org/3/library/pickle.html>`_
    would need to be supported in Go).

Popular serializers based on generated code
    usually do not de/serialize object graphs, but only object trees (*e.g.,*
    `Protocol Buffers <https://developers.google.com/protocol-buffers/>`_ or
    `Cap'n Proto <https://capnproto.org/>`_).

    `Flatbuffers <https://google.github.io/flatbuffers/>`_ being the exception
    handle object graphs natively, but lack support for sophisticated types such as
    maps and datetimes, durations *etc.*
