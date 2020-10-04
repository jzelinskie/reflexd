import logging
from base64 import b64encode
from pathlib import Path
from time import sleep
from typing import Tuple

import yaml
from bencode3 import BencodeError, bdecode
from deluge_client import DelugeRPCClient
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer

from reflexd import config


def _valid_torrent_file(path: Path) -> bool:
    try:
        bdecode(path.read_bytes())
        return True
    except BencodeError:
        pass  # We might be racing the process writing to the filesystem.

    sleep(1)  # This is literally killing kittens.

    try:
        bdecode(path.read_bytes())
        return True
    except BencodeError:
        return False


class AddTorrentEventHandler(PatternMatchingEventHandler):
    def __init__(
        self,
        deluge_args: Tuple[str, int, str, str],
        dir_config: dict,
        **kwargs,
    ):
        self._deluge_args = deluge_args
        self._dir_config = dir_config
        super(AddTorrentEventHandler, self).__init__(**kwargs)

    def on_created(self, event):
        logging.debug(f"witnessed the creation of {event.src_path}")

        filepath = Path(event.src_path)
        if not _valid_torrent_file(filepath):
            logging.warning(f"ignored invalid torrent file: {event.src_path}")
            return

        with DelugeRPCClient(*self._deluge_args) as client:
            logging.debug(f"connected to deluge: {self._deluge_args}")

            for field in ("download_location", "move_completed_path"):
                if field not in self._dir_config["options"]:
                    continue
                field_value = self._dir_config["options"][field]
                self._dir_config["options"][field] = field_value.format(
                    FILE=str(filepath),
                    FILE_PARENT=str(filepath.parent),
                )

            try:
                client.core.add_torrent_file(
                    filepath.name,
                    b64encode(filepath.read_bytes()),
                    self._dir_config["options"],
                )
            except:
                logging.exception(f"failed to add torrent file: {event.src_path}")
        logging.info(f"added torrent {event.src_path}")


class ReloadConfigEventHandler(PatternMatchingEventHandler):
    def __init__(
        self,
        config_dir: Path,
        deluge_args: Tuple[str, int, str, str],
        observer: Observer,
    ):
        self._config_dir = config_dir
        self._config_file = config_dir.joinpath(config.FILENAME)
        self._deluge_args = deluge_args
        self._observer = observer
        self._watches = []

        self._reload_config()

        super(ReloadConfigEventHandler, self).__init__(
            patterns=[config.FILENAME],
            ignore_patterns=[],
            ignore_directories=True,
            case_sensitive=True,
        )

    def _reload_config(self):
        try:
            config_dict = yaml.load(
                self._config_file.read_bytes(),
                Loader=yaml.SafeLoader,
            )
            config.validate_dict(config_dict)
        except (config.SchemaValidationError, yaml.YAMLError):
            logging.warning(
                f"attempted to reload invalid config file: {self._config_file}"
            )
            return

        if len(self._watches) > 0:
            while len(self._watches) > 0:
                watch = self._watches.pop()
                self._observer.unschedule(watch)

        for dir_config in config_dict["reflexd"]["v1"]["directories"]:
            watch = self._observer.schedule(
                AddTorrentEventHandler(
                    deluge_args=self._deluge_args,
                    dir_config=dir_config,
                    patterns=["*.torrent"],
                    ignore_patterns=[".*"],
                    ignore_directories=True,
                    case_sensitive=False,
                ),
                dir_config["path"],
                recursive=dir_config["recursive"],
            )
            self._watches.append(watch)

    def on_modified(self, event):
        logging.debug(f"witnessed the modification of {event.src_path}")
        assert Path(event.src_path) == self._config_file
        self._reload_config()
        logging.info("reloaded config")
