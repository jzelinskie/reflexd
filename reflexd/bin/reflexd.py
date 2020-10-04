"""
reflexd: automate your torrent client based on the filesystem

Usage:
  reflexd watch [--verbose , --debug, --config=config_directory]
  reflexd (-h | --help)
  reflexd (-V | --version)

Options:
  -h --help                   Show usage info
  -V --version                Output binary version
  -v --verbose                Verbose logging output
  -D --debug                  Debug mode
  --config=config_directory   Path to config directory [default: /etc/reflexd]
"""

import logging
import signal
import sys
from os import getenv
from os.path import expanduser, expandvars
from pathlib import Path
from typing import Any, Callable, Tuple

import yaml
from deluge_client import DelugeRPCClient
from docopt import docopt
from watchdog.observers import Observer

from reflexd import __version__, config
from reflexd.handlers import ReloadConfigEventHandler


def expand_path(path: str) -> Path:
    return Path(expandvars(expanduser(path)))


def validate_envvar(var: str, cast: Callable = None) -> Any:
    value = getenv(var, None)
    if value is None:
        raise Exception(f"missing required environment variable: {var}")

    if cast is not None:
        try:
            value = cast(value)
        except ValueError:
            raise Exception(f"invalid required environment variable: {var}")

    return value


def validate_config(config_path: Path) -> Path:
    config_file = config_path.joinpath("config.yaml")
    try:
        config.validate_dict(
            yaml.load(config_file.read_bytes(), Loader=yaml.SafeLoader)
        )
    except (config.SchemaValidationError, yaml.YAMLError):
        logging.exception(f"attempted to load invalid config file: {config_file}")
        raise
    return config_path


def validate_deluge(
    deluge_args: Tuple[str, int, str, str]
) -> Tuple[str, int, str, str]:
    try:
        logging.debug(f"testing connection to deluge: {deluge_args}")
        with DelugeRPCClient(*deluge_args):
            pass
    except Exception as e:
        raise Exception(f"failed to connect to deluge: {e.message}")

    return deluge_args


def watch_cmd(config_path: Path, deluge_args: Tuple[str, int, str, str]):
    observer = Observer()
    observer.schedule(
        ReloadConfigEventHandler(config_path, deluge_args, observer),
        str(config_path),
        recursive=False,
    )
    observer.start()

    def interrupt_handler(sig, frame):
        logging.info("received sigint interrupt")
        observer.stop()
        observer.join()
        sys.exit(0)

    signal.signal(signal.SIGINT, interrupt_handler)
    signal.pause()


def main():
    args = docopt(__doc__, version=__version__)

    log_level = logging.DEBUG if args["--verbose"] else logging.INFO
    logging.basicConfig(level=log_level)
    logging.getLogger("deluge_client.client").setLevel(logging.WARN)
    logging.debug(f"docopt args: {args}")

    if args["watch"]:
        watch_cmd(
            validate_config(expand_path(args["--config"])),
            validate_deluge(
                (
                    validate_envvar("REFLEXD_DELUGE_HOST"),
                    validate_envvar("REFLEXD_DELUGE_PORT", cast=int),
                    validate_envvar("REFLEXD_DELUGE_USERNAME"),
                    validate_envvar("REFLEXD_DELUGE_PASSWORD"),
                )
            ),
        )
    else:
        raise NotImplementedError(
            f"tried to handle unimplemented command with args: {args}"
        )


if __name__ == "__main__":
    main()
