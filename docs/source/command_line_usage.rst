Command-Line Usage
==================
Mapry provides a single point-of-entry for all the code generation through
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
