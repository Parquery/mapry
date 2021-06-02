"""Link to ``mapry.main`` so that you can execute it with ``python`` CLI."""

import sys

import mapry.main

if __name__ == "__main__":
    sys.exit(mapry.main.run(prog="mapry"))
