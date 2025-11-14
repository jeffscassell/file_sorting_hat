"""
processing_objects.py

The objects of files that are meant to be processed and moved.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from enum import Enum
from dataclasses import dataclass

from fs_helpers import cleanFilename, confirmFilename

from .extensions import Config



class MoveObject(ABC):
    source: Path
    destination: Path
    
    
    def __init__(self, path: str):
        self.source = Path(path)
        self._validatePath(self.source)
        self._build()
    
    def _validatePath(self, path: Path):
        if not path.exists():
            raise ValueError(f"Path does not exist: {path}")
    
    def _sanitizeFilename(self, filename: str) -> str:
        return cleanFilename(filename)
    
    @abstractmethod
    def _build(self): ...
    
    @abstractmethod
    def move(self): ...


videoOptions = {
    0: ("Live", "live"),
    1: ("3D", "3d"),
    2: ("Animated", "animated"),
}

class Video(MoveObject):

    def _validatePath(self, path: Path):
        super()._validatePath(path)
        
        if not path.is_file():
            raise TypeError(f"Path is not a file: {path}")


    def _build(self) -> None:
        oldName = self.source.stem
        newName = oldName
        ext = self.source.suffix
        print(f"Current file: {oldName}{ext}")
        print()
        
        tag = input("Author tag (optional): ") or None
        newName = input("Update name (optional): ") or newName
        print()
        
        if tag:
            newName = f"[{tag}] {newName}"

        santizedName = self._sanitizeFilename(newName)
        santizedName = confirmFilename(santizedName)
        finalName = f"{santizedName}{ext}"
        print()

        print("Categories:")
        for key, value in videoOptions.items():
            print(f"{key}: {value[0]}")
        print()

        category = None
        while category == None or category not in videoOptions.keys():
            try:
                category = int(input("Choose category #: "))
            except ValueError:
                category = None
        print()

        subdirectory = videoOptions[category][1]
        self.destination = Config.VIDEO_PATH / subdirectory / finalName


    def move(self) -> None:
        
        print(f"{self.source} -> {self.destination}")
        # try:
        #     with open(self.newPath, "xb") as outfile:
        #         outfile.write(self.oldPath.read_bytes())
        # except FileExistsError:
        #     raise
        # else:
        #     self.oldPath.unlink()


class Other(MoveObject):
    
    def _build(self) -> None:
        ...
    
    
    def move(self) -> None:
        ...


class MoveStatus(Enum):
    SUCCESS = "moved"
    DESTINATION_EXISTS = "destination exists"
    FILE_IN_USE = "file in use"
    OTHER_ERROR = "error"


@dataclass
class MoveResult:
    file: MoveObject
    status: MoveStatus
    exception: Exception | None = None
    
    def __str__(self) -> str:
        string = f"{self.file.destination.name}: {self.status.value}"
        if self.exception:
            string += f"\n\t{self.exception}"
        return string