Contributing
============

We are very grateful for and welcome contributions: be it opening of the issues,
discussing future features or submitting pull requests.

To submit a pull request:

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

* Implement your changes.

* Run `precommit.py` to execute pre-commit checks locally.

Live tests
----------

We also provide live tests that generate, compile and run the de/serialization
code on a series of tests cases. These live tests depend on build tools of
the respective languages (*e.g.*, gcc and CMake for C++ and go compiler for Go,
respectively).

You need to install manually the build tools. Afterwards, create a separate
virtual environment for the respective language and install Python dependencies
for the respective language (*e.g.*, Conan in case of C++) given as ``test*``
requirements in
`setup.py <https://github.com/Parquery/mapry/blob/master/setup.py>`_.

The workflow for C++ looks as follows:

.. code-block:: bash

    # Create a separate virtual environment
    python3 -m venv venv-cpp

    # Activate it
    . venv-cpp/bin/activate

    # Install the dependencies of C++ live tests
    pip3 install -e .[testcpp]

    # Run the live tests
    ./tests/cpp/live_test_generate_jsoncpp.py

For Go:

.. code-block:: bash

    python3 -m venv venv-go
    . venv-go/bin/activate
    pip3 install -e .[testgo]
    ./tests/go/live_test_generate_jsonable.py

For Python:

.. code-block:: bash

    python3 -m venv venv-py
    . venv-py/bin/activate
    pip3 install -e .[testpy]./p
    ./tests/py/live_test_generate_jsonable.py
