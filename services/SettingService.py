import logging
import os

from constant.paths import BASE_DIR
from constant.settings import RELATIVE_TO_BASE_DIR
from repository.SettingRepository import SettingRepository
from services.DatabaseService import DatabaseService

logger = logging.getLogger(__name__)


class SettingNotFoundError(Exception):
    pass


class SettingService:
    """Reads and writes settings.

    There is no fallback to a value in code: a key that is missing or retired
    is an error, not a default. Call `initialise()` once, on app startup,
    before any get/set - it is not checked on every call.
    """

    def __init__(self, setting_repository=None):
        self.setting_repository = setting_repository or SettingRepository()
        self._cache = None

    def initialise(self):
        """Creates the table and seeds it if needed. Safe to call more than once."""
        self.setting_repository.initialise(DatabaseService.now())
        self.reload()

    def get(self, key):
        values = self.get_all()
        if key not in values:
            raise SettingNotFoundError(
                f"Setting '{key}' is not in the database. "
                f"Delete {self.setting_repository.db_path} to rebuild it from the seed."
            )
        return values[key]

    def get_int(self, key):
        value = self.get(key)
        try:
            return int(value)
        except ValueError:
            raise SettingNotFoundError(f"Setting '{key}' is not a number: {value!r}")

    def get_path(self, key):
        """Absolute path for a path setting, resolved against BASE_DIR."""
        value = self.get(key)
        if key in RELATIVE_TO_BASE_DIR and not os.path.isabs(value):
            return os.path.join(BASE_DIR, value)
        return value

    def get_all(self):
        if self._cache is None:
            self._cache = self.setting_repository.find_all_active()
        return self._cache

    def set(self, key, value):
        self.set_many({key: value})

    def set_many(self, values):
        """Writes every change in one transaction, then drops the cache."""
        if not values:
            return

        missing = self.setting_repository.update_values(values, DatabaseService.now())
        if missing:
            raise SettingNotFoundError(
                f"Not in the database, nothing was saved: {', '.join(missing)}"
            )

        logger.info(f"Updated settings: {', '.join(values)}")
        self.reload()

    def reload(self):
        self._cache = None


# Shared instance - the cache means the services can read settings per file
# without hitting the database every time.
settingService = SettingService()
