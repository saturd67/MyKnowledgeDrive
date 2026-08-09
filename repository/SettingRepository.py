"""Every SQL statement that touches the setting table.

Nothing above this layer writes SQL: SettingService handles caching, path
resolution and errors, and calls in here for the data.
"""

import logging

from constant.settings import SETTING_DEFAULT_VALUES
from services.DatabaseService import DatabaseService

logger = logging.getLogger(__name__)


class SettingRepository:

    def __init__(self, database_service=None):
        self.database_service = database_service or DatabaseService()

    @property
    def db_path(self):
        return self.database_service.db_path

    def initialise(self, created_at):
        """Creates the table if absent and seeds any key that has never existed."""
        with self.database_service.connection() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS setting (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    key        TEXT    NOT NULL UNIQUE,
                    value      TEXT    NOT NULL,
                    created_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
                    updated_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
                    is_active  INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1))
                )
            """)
            self._set_default_value_if_not_exist(connection, created_at)

    def find_all_active(self):
        with self.database_service.connection() as connection:
            rows = connection.execute(
                "SELECT key, value FROM setting WHERE is_active = 1"
            ).fetchall()
        return {row["key"]: row["value"] for row in rows}

    def update_values(self, values, updated_at):
        """Applies every change in one transaction, or none at all.

        Returns the keys that matched no active row; when that list is not
        empty nothing has been written.
        """
        with self.database_service.connection() as connection:
            active = {
                row["key"]
                for row in connection.execute("SELECT key FROM setting WHERE is_active = 1")
            }
            missing = [key for key in values if key not in active]
            if missing:
                return missing

            for key, value in values.items():
                connection.execute(
                    "UPDATE setting SET value = ?, updated_at = ? WHERE key = ? AND is_active = 1",
                    (str(value), updated_at, key),
                )

        return []

    def _set_default_value_if_not_exist(self, connection, created_at):
        """Deactivated keys count as existing, so retiring one is not undone."""
        existing = {row["key"] for row in connection.execute("SELECT key FROM setting")}
        missing = [(key, value) for key, value in SETTING_DEFAULT_VALUES if key not in existing]
        if not missing:
            return

        connection.executemany(
            "INSERT INTO setting (key, value, created_at, updated_at) VALUES (?, ?, ?, ?)",
            [(key, value, created_at, created_at) for key, value in missing],
        )
        logger.info(f"Seeded settings: {', '.join(key for key, _ in missing)}")
