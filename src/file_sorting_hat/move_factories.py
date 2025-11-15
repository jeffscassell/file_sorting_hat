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
    config: Config
    
    def __init__(self, config: Config):
        self.config = config
    
    @abstractmethod
    def makeMoveObject(self, file: str) -> MoveObject: ...


class VideoFactory(MoveObjectFactory):
    
    def makeMoveObject(self, file: str) -> Video:
        return Video(file, self.config.paths["VIDEO_PATH"])


class OtherFactory(MoveObjectFactory):
    
    def makeMoveObject(self, file: str) -> Other:
        return Other(file, self.config.paths["OTHER_PATH"])


factoryOptions = {
    0: ("Video", VideoFactory),
    1: ("Other", OtherFactory),
}

class MoveObjectSuperFactory:
    config: Config
    
    
    def __init__(self, config: Config):
        self.config = config
    
    def __createFactory(self, choice: int) -> MoveObjectFactory:
        if choice not in factoryOptions.keys():
            raise ValueError("Not a valid subdirectory")
        
        return factoryOptions[choice][1](self.config)
    
    def chooseFactory(self) -> MoveObjectFactory:
        
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
        
        return self.__createFactory(choice)
