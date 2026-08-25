"""Unit tests.

Run them all from the project root:

    python -m unittest discover -s tests -t .

Nothing here reaches Google Drive, and nothing loads the embedding model: the
Drive resource, the media download and the embedding function are stood in for
by the fakes in this package, so the suite runs offline in a few seconds.
"""

import logging

# Several tests walk a path the services log about on purpose - a download that
# fails, an image that cannot be read, a duplicate id. Those lines are the
# behaviour under test, not something to read, and they bury the real output.
logging.disable(logging.CRITICAL)
