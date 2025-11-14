from dotenv import load_dotenv
from os import getenv
from pathlib import Path
from sys import argv

        

__errorExists = None


def __setError(message: str) -> None:
    global __errorExists
    __errorExists = 1
    print(message)


def __validatePath(path: Path) -> None:
    if not path.exists():
        __setError(f"{path} does not exist.")
    
    if not path.is_dir():
        __setError(f"{path} is not a directory")


def validateSession() -> None:
    if len(argv) == 1:
        __setError("This script requires file arguments to function.")

    Config.load()
    Config.validate()

    if __errorExists:
        exit(1)


class Config:
    VIDEO_PATH: Path
    OTHER_PATH: Path
    __loaded = False
    
    
    @classmethod
    def load(cls) -> None:
        """ Call once at startup to load environment variables. """
        
        if cls.__loaded:
            return
        
        load_dotenv()
        videoPath = str(getenv("VIDEO_PATH"))
        otherPath = str(getenv("OTHER_PATH"))

        cls.VIDEO_PATH = Path(videoPath)
        cls.OTHER_PATH = Path(otherPath)
        
        cls.__loaded = True
    
    
    @classmethod
    def validate(cls) -> None:
        assert cls.__loaded
        
        __validatePath(cls.VIDEO_PATH)
        __validatePath(cls.OTHER_PATH)