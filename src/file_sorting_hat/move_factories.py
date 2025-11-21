"""
move_factories.py

Contains the various factories necessary for creating MoveObjects.
"""

from abc import ABC, abstractmethod

from .move_objects import (
    MoveObject,
    Video,
    Other,
)
from .extensions import Config



class MoveObjectFactory(ABC):
    
    @abstractmethod
    def makeMoveObject(self, file: str) -> MoveObject: ...


class VideoFactory(MoveObjectFactory):
    
    def makeMoveObject(self, file: str) -> Video:
        directory = Config.paths.get("VIDEO_PATH")
        if not directory:
            raise ValueError(f"Missing VIDEO_PATH from Config")

        return Video(file, directory)


class OtherFactory(MoveObjectFactory):
    
    def makeMoveObject(self, file: str) -> Other:
        directory = Config.paths.get("OTHER_PATH")
        if not directory:
            raise ValueError(f"Missing VIDEO_PATH from Config")

        return Other(file, directory)


factoryOptions = {
    0: ("Video", VideoFactory),
    1: ("Other", OtherFactory),
}

class MoveObjectSuperFactory:
    
    @classmethod
    def __createFactory(cls, choice: int) -> MoveObjectFactory:
        return factoryOptions[choice][1]()

    @classmethod
    def chooseFactory(cls) -> MoveObjectFactory:
        
        print("File type to be processed:")
        for key, value in factoryOptions.items():
            print(f"{key}: {value[0]}")
        print()
        
        choice = None
        while choice == None or choice not in factoryOptions.keys():
            try:
                choice = int(input("Selection #: "))
            except ValueError:
                choice = None
        print()
        
        return cls.__createFactory(choice)
