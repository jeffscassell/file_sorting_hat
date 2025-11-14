"""
processing_objects.py

The objects of files that are meant to be processed and moved.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from enum import Enum
from dataclasses import dataclass

from fs_helpers import cleanFilename, confirmFilename, formatFileSize

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
    
    @abstractmethod
    def delete(self): ...
    
    @abstractmethod
    def overwrite(self): ...


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
        try:
            with open(self.destination, "xb") as outfile:
                outfile.write(self.source.read_bytes())
        except FileExistsError:
            raise
        else:
            self.source.unlink()
    
    
    def delete(self) -> None:
        if self.source.exists():
            self.source.unlink()
    
    
    def overwrite(self) -> None:
        if self.source.exists() and self.destination.exists():
            self.destination.unlink()
            with open(self.source, "rb") as infile:
                with open(self.destination, "wb") as outfile:
                    outfile.write(infile.read())


class Other(MoveObject):
    
    def _build(self) -> None:
        ...
    
    
    def move(self) -> None:
        ...
    
    
    def delete(self) -> None:
        ...
    
    
    def overwrite(self) -> None:
        ...


class MoveStatus(Enum):
    SUCCESS = "moved"
    DUPLICATE = "destination exists"
    FILE_IN_USE = "file in use"
    OTHER_ERROR = "error"
    DELETED = "deleted"
    OVERWRITTEN = "overwritten"
    PROCESSED = "processed"


recoverableErrors = (
    MoveStatus.DUPLICATE,
    MoveStatus.FILE_IN_USE,
)


@dataclass
class MoveResult:
    file: MoveObject
    status: MoveStatus
    exception: BaseException | None = None
    
    def __str__(self) -> str:
        string = f"{self.file.destination.name}: {self.status.value}"
        
        match self.status:
            case MoveStatus.DUPLICATE:
                source = formatFileSize(file=self.file.source)
                destination = formatFileSize(file=self.file.destination)
                string += f"\n\tsource: {source}, dest: {destination}"
            case MoveStatus.OTHER_ERROR:
                string += f"\n\t{self.exception}"
        return string
    
    def delete(self) -> None:
        self.file.delete()
        self.status = MoveStatus.DELETED
        self.clearException()
    
    def overwrite(self) -> None:
        self.file.overwrite()
        self.status = MoveStatus.OVERWRITTEN
        self.clearException()
    
    def move(self) -> None:
        self.file.move()
        self.status = MoveStatus.SUCCESS
        self.clearException()
        
    def clearException(self) -> None:
        self.exception = None