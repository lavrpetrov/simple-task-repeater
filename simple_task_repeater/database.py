import os
import time
from pathlib import Path
from threading import RLock

from calmlib import get_personal_logger
from calmlib import load_json, dump_json
from calmlib import run_bg
from calmlib.autocast import autocast_args
from calmlib.dropbox_utils import DropboxSharedFolder

logger = get_personal_logger(__name__)
DEFAULT_SYNC_PERIOD = 5


def synced(func):
    func.synced = None
    return func


class DatabaseMeta(type):
    def __new__(meta, name, bases, dct):
        def synced(func):
            def wrapper(self, *args, **kwargs):
                func(self, *args, **kwargs)
                self.sync()

            return wrapper

        for key, value in dct.items():
            if hasattr(value, 'synced'):
                dct[key] = synced(value)
        return super(DatabaseMeta, meta).__new__(meta, name, bases, dct)


class Database(metaclass=DatabaseMeta):
    def __enter__(self):
        self.launch_syncer()

    def __exit__(self, *exc_details):
        self.syncer_flag = False
        if self._last_update_timestamp > self._last_sync_timestamp:
            self._sync()

    def load_data(self):
        if os.path.exists(self.data_path):
            return load_json(self.data_path)
        else:
            return {}

    def dump_data(self):
        dump_json(self.data, self.data_path)

    @autocast_args
    def __init__(self, path: Path, dropbox_token, dropbox_subpath=None, sync_period=None):
        self.sync_period = sync_period or DEFAULT_SYNC_PERIOD
        timestamp = time.time()
        self._last_sync_timestamp = timestamp
        self._last_update_timestamp = timestamp
        self._lock = RLock()
        self._syncer_thread = None
        self._syncer_flag = True
        self.dropbox_syncer = DropboxSharedFolder(token=dropbox_token, path=path,
                                                  subpath=dropbox_subpath or self.__class__.__name__)
        self.dropbox_syncer.sync()
        self.data_path = path / 'data.json'
        self.data = self.load_data()
        logger.info(f"Initializing Database at {path.absolute()}")

    def sync(self):
        with self._lock:
            timestamp = time.time()
            # check that sync thread is alive
            if not self.check_syncer_is_alive():
                logger.warning("It seems database sync thread is not alive. "
                               "Please launch it with Database.launch_syncer().")
            self._last_update_timestamp = timestamp

    def _sync(self):
        # dump all data on disk.
        self.dump_data()
        # call dropbox sync
        self.dropbox_syncer.sync()

    def _syncer(self):
        while self.syncer_flag:
            with self._lock:
                timestamp = time.time()
                if self._last_update_timestamp > self._last_sync_timestamp:
                    self._sync()
                self._last_sync_timestamp = timestamp
            time.sleep(self.sync_period)

    def check_syncer_is_alive(self):
        with self._lock:
            timestamp = time.time()
            return self._syncer_thread is not None and self._syncer_thread.is_alive() and \
                   self._last_sync_timestamp > timestamp - 4 * self.sync_period

    def launch_syncer(self):
        if not self.check_syncer_is_alive():
            self.syncer_flag = True
            self._syncer_thread = run_bg(self._syncer)
        else:
            logger.warning("The syncer is already alive and won't be re-launched")

    @property
    def syncer_flag(self):
        with self._lock:
            return self._syncer_flag

    @syncer_flag.setter
    def syncer_flag(self, syncer_flag):
        with self._lock:
            self._syncer_flag = syncer_flag
