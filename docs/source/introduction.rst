Introduction
============
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
itself as a good fit there with a lot of existing assistance tools (JSON and
YAML modules *etc*.).

However, JSON allows only a limited set of data types (numbers, strings, arrays
and objects/maps). We found that most of our data relied on
**a richer set of primitives** than was provided by a standard JSON. This
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
The code is generated based on the schema. You define schema once and
generate code in all the supported languages automatically. Schemas can be
evolved and backward compatibility is supported through optional properties.

Supported languages
-------------------
Currently, Mapry speaks:

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
