Related Projects
================

We give here a non-comprehensive list of related de/serialization projects. We
indicate how they differ from Mapry and explain why we took pains to develop
(and maintain!) our own tool instead of using an existing one.

* Standard JSON libraries all support object trees, but not object graphs.
  Moreover, they do not support data based on a schema. While this is handy
  when the structure of your data is unknown at runtime, it makes code
  unnecessarily more difficult to maintain when the structure is indeed
  known in advance.

* There is a large ecosystem around structured objects and their serialization
  based on property annotations (*e.g.*,
  `Rapidschema (C++) <https://github.com/ledergec/rapidschema>`_,
  `encoding/json (Go) <https://golang.org/pkg/encoding/json/>`_ or
  `Jackson (Java) <https://github.com/FasterXML/jackson>`_). While some of them
  support handling object graphs (usually through custom logic), we found the
  lack of polyglot support (and resulting maintenance effort required by
  synchronization of custom de/serialization rules across languages)
  a high barrier-to-usage.

* Standard or widely used serialization libraries such as
  `Boost.Serialization (C++) <https://www.boost.org/doc/libs/1_70_0/libs/serialization/doc/index.html>`_,
  `Gob (Go) <https://golang.org/pkg/encoding/gob/>`_ or
  `Pickle (Python) <https://docs.python.org/3/library/pickle.html>`_
  serialize object graphs out-of-the-box and handle impedance mismatch well.
  However, the representation of the serialized data is barely human-readable
  and difficult to get right in a polyglot setting due to a lack of common
  poly-language libraries (*e.g.*, reading pickled data structures in C++).
  We deemed it a Herculean task to maintain the corresponding de/serializations
  accross different languages.

* Popular serializers such as
  `Protocol Buffers <https://developers.google.com/protocol-buffers/>`_ or
  `Cap'n Proto <https://capnproto.org/>`_
  support only object trees. If you need to work with cross-references in the
  serialized message, you need to dereference instances yourself. We found
  manual dereferencing in code to be error prone and lead to a substantial
  code bloat.

* `Flatbuffers <https://google.github.io/flatbuffers/>`_ handle object graphs
  natively, but exhibit a great deal of impedance mismatch through lack
  of maps and sophisticated data types such as date/time, duration *etc.*

* Language-specific serializers such as
  `ThorSerializer (C++) <https://github.com/Loki-Astari/ThorsSerializer>`_,
  `JavaScript Object Graph (Javascript) <https://github.com/jsog/jsog>`_,
  `Serializr (Javascript) <https://github.com/mobxjs/serializr>`_ and
  `Flexjson (Java) <http://flexjson.sourceforge.net/>`_
  serialize object graphs with satisfying, but varying degree of structure
  enforcement and readability. Most approaches require the developer to
  annotate the structures with decorators which the libraries use to parse
  and serialize data. As long as you use a single-language setting and
  care about the data being readable, these solutions work well. However,
  it is not clear how they can be adapted to a multi-language setting where
  system components written in different languages need to inter-operate.

* `JSON for Linking Data <https://json-ld.org/>`_ and
  `JSON Graph <netflix.github.io/falcor/documentation/jsongraph.html>`_ are
  conventions to provide a systematic approach to modeling the object graphs in
  JSON. While these conventions look promising, we found the existing
  libraries lacking for production-ready code. On a marginal note,
  the JSON representations seem unnecessarily verbose when representing
  references.

* `JVM serializers <https://github.com/eishay/jvm-serializers/wiki>`_ presents
  a report on different object serializers running on top of Java Virtual
  Machine. The serializers are evaluated based on their run time and size.
