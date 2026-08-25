"""Puts the services' log lines into a run's console.

The services already say what they are doing through `logging` - which file is
being downloaded, which image was read, what the totals were. This turns those
records into the (time, LEVEL, message, source) tuples the console renders, so
a real run reads the way the scripted one did and every line says which module
it came from.

Refreshes are throttled: a full rebuild logs a line per file, and repainting
the console for each one would make the run slower than the work it reports.
"""

import logging
import time

LEVEL_NAMES = {
    logging.DEBUG: "INFO",
    logging.INFO: "INFO",
    logging.WARNING: "WARN",
    logging.ERROR: "ERROR",
    logging.CRITICAL: "ERROR",
}


class ServiceLogHandler(logging.Handler):
    """Appends `services.*` log records to a list, refreshing now and then.

    `refresh` is whatever puts the list on screen - the screen hands it the
    call that appends to the console standing on the page, so the log keeps
    where it is scrolled to while a run writes underneath it.

    Use it as a context manager so the handler is always removed again, even
    when the run raises:

        with ServiceLogHandler(state.sync_log, self._stream_log):
            library_reset_service.start_reset(...)
    """

    #: Seconds between refreshes while a run is logging.
    REFRESH_INTERVAL = 0.5

    #: Lines kept. A rebuild logs thousands; the console only shows the tail.
    MAX_LINES = 400

    def __init__(self, log_lines, refresh, logger_name="services"):
        super().__init__(level=logging.INFO)
        self.log_lines = log_lines
        self.refresh = refresh
        self.logger_name = logger_name
        self._last_refresh = 0.0

    def emit(self, record):
        self.log_lines.append((
            time.strftime("%H:%M:%S", time.localtime(record.created)),
            LEVEL_NAMES.get(record.levelno, "INFO"),
            record.getMessage(),
            # Which file wrote the line - "docx_file", "file_embedder_service".
            # Several services log the same wording ("Entering folder"), so
            # without this a line does not say who is talking.
            record.module,
        ))
        del self.log_lines[:-ServiceLogHandler.MAX_LINES]

        now = time.monotonic()
        is_due = now - self._last_refresh >= ServiceLogHandler.REFRESH_INTERVAL
        if is_due:
            self._last_refresh = now
            self.refresh()

    def __enter__(self):
        service_logger = logging.getLogger(self.logger_name)
        service_logger.addHandler(self)
        # Nothing configures logging in the app yet, so without this the
        # records never reach a handler at all.
        if service_logger.level == logging.NOTSET or service_logger.level > logging.INFO:
            service_logger.setLevel(logging.INFO)
        return self

    def __exit__(self, exception_type, exception, traceback):
        logging.getLogger(self.logger_name).removeHandler(self)
        return False
