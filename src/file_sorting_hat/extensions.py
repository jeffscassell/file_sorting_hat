"""
extensions.py

Validation and config.
"""

from dotenv import load_dotenv
from os import getenv
from pathlib import Path
from sys import argv



class Config:
    settings: dict[str, str]
    paths: dict[str, Path]
    isLoaded = False


    @classmethod
    def setSetting(cls, name: str, setting: str) -> None:
        if not hasattr(cls, "settings"):
            cls.settings = dict()

        cls.settings[name] = setting
    
    @classmethod
    def setPath(cls, name: str, path: Path) -> None:
        if not hasattr(cls, "paths"):
            cls.paths = dict()

        cls.paths[name] = path

    @classmethod
    def load(cls, path: str | Path | None = None) -> None:
        """ Call once at startup to load .env variables into environment. """

        if cls.isLoaded:
            return

        load_dotenv(path) if path else load_dotenv()
        cls.isLoaded = True

    @classmethod
    def validatePath(cls, key: str, isFile: bool = False) -> None:
        """ Confirm the key was loaded into the environment, validate it,
        and add it into the config's paths store if so. """

        path = getenv(key)

        if not path:
            raise ValueError(f"Could not find {key} in environment")
        
        path = Path(path)

        if not path.exists():
            raise OSError(f"{path} does not exist.")

        if isFile:
            if not path.is_file():
                raise TypeError(f"{path} is not a file")
        else:
            if not path.is_dir():
                raise TypeError(f"{path} is not a directory")

        cls.setPath(key, Path(path))


def validateSession(config: Config) -> None:
    if len(argv) == 1:
        raise ValueError("This script requires file arguments to function.")

    config.load()
    config.validatePath("VIDEO_PATH")
    config.validatePath("OTHER_PATH")
