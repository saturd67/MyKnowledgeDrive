import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from constant.paths import DB_PATH

logger = logging.getLogger(__name__)


class DatabaseService:
    """Connection handling only - the SQL lives in repository/.

    The audit timestamps are stamped by BaseRepository, which is what knows
    when each column is written.
    """

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    @contextmanager
    def connection(self):
        """Commits on success, rolls back on error, always closes."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA busy_timeout = 5000")
        try:
            with connection:
                yield connection
        finally:
            connection.close()
