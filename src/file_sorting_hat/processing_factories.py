"""
processing_factories.py

Contains the various factories necessary for creating file processing objects.
"""

from abc import ABC, abstractmethod

from .processing_objects import (
    MoveObject,
    Video,
    Other,
)



class MoveObjectFactory(ABC):
    
    @abstractmethod
    def makeMoveObject(self, path: str) -> MoveObject: ...


class VideoFactory(MoveObjectFactory):
    
    def makeMoveObject(self, path: str) -> Video:
        return Video(path)


class OtherFactory(MoveObjectFactory):
    
    def makeMoveObject(self, path: str) -> Other:
        return Other(path)


factoryOptions = {
    0: ("Video", VideoFactory),
    1: ("Other", OtherFactory),
}

class MoveObjectSuperFactory:
    
    @staticmethod
    def chooseFactory() -> MoveObjectFactory:
        
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
        
        return factoryOptions[choice][1]()
