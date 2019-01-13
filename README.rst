Mapry
=====

!!! THIS IS WORK IN PROGRESS. PLEASE DO NOT USE YET !!!

Mapry generates polyglot code for de/serializing object graphs in JSON format.

**Use case**. We needed a yet another domain-specific language for system configuration. The existing solutions
mostly focused on modeling the configuration as *object trees* in which the configuration is structured hierarchically
with no cross-references between the objects. We found this structure to be hihgly limiting for most of the complex
system configuration which required objects to be referenced among each other.

We wanted the serialization itself to be readable so that an operator can edit it using a simple text editor. JSON
offered itself as a good fit there with a lot of existing assistance tools.

We decided against a NoSQL database as these add an administration burden which is justifyable for dynamic system, but
we found that burden completely unnecessary for rather static structures such as configuration.

Hence we developed a generator that produces code to de/serialize **object graphs** from **readable JSON files**.

**Maintainability**. We wanted to facilitate maintainability of the system through static checks so that most errors
in the object graphs are registered prior to the deployment in the production. These checks include strong typing,
dangling references and certain value checks (*e.g.*, range checks, minimum number of elements in containers *etc*.).

The **schema** of the object graph is stored in a separate JSON file and defines all the data types used in the object
graph including the object graph itself.

**Code readability over speed**. We wanted the generated code to be rather readable than fast.
Though the users do not care about the implementation details most of the time, newcomers really like to peek under
the hub. We found that its much easier for them to get up to speed when the generated code is well-readable.

This is particularly important when the code serialization tool permeates most of your system components.

**Supported languages**. Currently, Mapry speaks C++, Python and Go.


We were not happy with the existing de/serializers:

* Proto3 and Cap'n proto can not handle object graphs (only object trees).
* Flatbuffers do not handle JSON.
* Boost serialization does not handle JSON nicely. Additionally, its XML format is not really human-readable.
* ThorsSerializer produces unreadable JSON files.

Installation
============

* Create a virtual environment:

.. code-block:: bash

    python3 -m venv venv3

* Activate it:

.. code-block:: bash

    source venv3/bin/activate

* Install mapry with pip:

.. code-block:: bash

    pip3 install mapry

Development
===========

* Check out the repository.

* In the repository root, create the virtual environment:

.. code-block:: bash

    python3 -m venv venv3

* Activate the virtual environment:

.. code-block:: bash

    source venv3/bin/activate

* Install the development dependencies:

.. code-block:: bash

    pip3 install -e .[dev]

* Run `precommit.py` to execute pre-commit checks locally.
