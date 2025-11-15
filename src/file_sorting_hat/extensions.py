"""
extensions.py

Validation and config.
"""

from dotenv import load_dotenv
from os import getenv
from pathlib import Path
from sys import argv

        

__errorExists = None


def setError(message: str) -> None:
    global __errorExists
    __errorExists = 1
    print(message)


def validatePath(path: Path) -> None:
    if not path.exists():
        setError(f"{path} does not exist.")

    if not path.is_dir():
        setError(f"{path} is not a directory")


class Config:
    settings: dict[str, str]
    paths: dict[str, Path]
    __loaded = False


    @classmethod
    def setSetting(cls, name: str, setting: str) -> None:
        cls.settings[name] = setting
    
    @classmethod
    def setPath(cls, name: str, path: Path) -> None:
        cls.paths[name] = path

    @classmethod
    def load(cls) -> None:
        """ Call once at startup to load environment variables. """

        if cls.__loaded:
            return

        load_dotenv()
        videoPath = str(getenv("VIDEO_PATH"))
        otherPath = str(getenv("OTHER_PATH"))

        cls.setPath("VIDEO_PATH", Path(videoPath))
        cls.setPath("OTHER_PATH", Path(otherPath))

        cls.__loaded = True

    @classmethod
    def validate(cls) -> None:
        validatePath(cls.paths["VIDEO_PATH"])
        validatePath(cls.paths["OTHER_PATH"])


def validateSession(config: Config) -> None:
    if len(argv) == 1:
        setError("This script requires file arguments to function.")

    config.load()
    config.validate()

    if __errorExists:
        exit(1)
