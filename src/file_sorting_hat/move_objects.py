"""
move_objects.py

The objects of files that are meant to be processed and moved.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from enum import Enum
from dataclasses import dataclass
import shutil

from fs_helpers import cleanFilename, confirmFilename, size



class MoveObject(ABC):
    source: Path
    destination: Path
    directory: Path


    def __init__(self, file: str, directory: str | Path):
        self.source = Path(file)
        self.directory = Path(directory)

    def validate(self):
        if not self.source.exists():
            raise ValueError(f"Path does not exist: {self.source}")

    def _sanitizeFilename(self, filename: str) -> str:
        return cleanFilename(filename)
    
    def setDestination(self, path: str | Path) -> None:
        self.destination = Path(path)

    def _destinationSafety(self) -> None:
        ...

    @abstractmethod
    def buildOptions(self): ...

    @abstractmethod
    def move(self): 
        """ Move object from source to destination. If destination exists,
        raises OSError. """

    @abstractmethod
    def delete(self):
        """ Delete source file. """

    @abstractmethod
    def overwrite(self): ...


subDirectories = {
    0: ("Live", "live"),
    1: ("3D", "3d"),
    2: ("Animated", "animated"),
}

class Video(MoveObject):

    def validate(self):
        super().validate()

        if not self.source.is_file():
            raise TypeError(f"Path is not a file: {self.source}")


    def buildOptions(self) -> None:
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
        for key, value in subDirectories.items():
            print(f"{key}: {value[0]}")
        print()

        category = None
        while category == None or category not in subDirectories.keys():
            try:
                category = int(input("Choose category #: "))
            except ValueError:
                category = None
        print()

        subdirectory = subDirectories[category][1]
        destination = self.directory / subdirectory / finalName
        self.setDestination(destination)


    def move(self) -> None:
        if self.destination.is_file():
            raise FileExistsError(f"File exists: {self.destination}")

        shutil.move(self.source, self.destination)


    def delete(self) -> None:
        if self.source.exists():
            self.source.unlink()


    def overwrite(self) -> None:
        if self.destination.is_file():
            self.destination.unlink()
        
        shutil.move(self.source, self.destination)


class Other(MoveObject):

    def buildOptions(self) -> None:
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
    DELETE_FAILURE = "can't delete source"
    OTHER_ERROR = "error"
    DELETED = "deleted source"
    OVERWRITTEN = "overwritten"
    PROCESSED = "processed"


recoverableErrors = (
    MoveStatus.DUPLICATE,
    MoveStatus.DELETE_FAILURE,
)

goodStates = (
    MoveStatus.SUCCESS,
    MoveStatus.DELETED,
    MoveStatus.OVERWRITTEN,
)


@dataclass
class MoveResult:
    file: MoveObject
    status: MoveStatus
    exception: BaseException | None = None

    def __str__(self) -> str:
        maxLength = 80
        prefix = self.file.destination.name
        suffix = self.status.value

        if self.status in goodStates:
            fillChar = "."
        else:
            fillChar = "_"

        filledLength = len(prefix) + len(suffix)
        emptyLength = maxLength - filledLength
        string = prefix + fillChar * emptyLength + suffix

        match self.status:
            case MoveStatus.DUPLICATE:
                source = size(self.file.source)
                destination = size(self.file.destination)
                string += f"\n\tsource: {source}, dest: {destination}"
            case MoveStatus.OTHER_ERROR:
                string += f"\n\t{self.exception}"

        return string

    def delete(self) -> None:
        self.file.delete()
        self.__clear(MoveStatus.DELETED)

    def overwrite(self) -> None:
        self.file.overwrite()
        self.__clear(MoveStatus.OVERWRITTEN)

    def move(self) -> None:
        self.file.move()
        self.__clear(MoveStatus.SUCCESS)

    def __clear(self, status: MoveStatus) -> None:
        self.status = status
        self.exception = None
