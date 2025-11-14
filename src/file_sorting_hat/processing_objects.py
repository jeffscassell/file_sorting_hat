"""
processing_objects.py

The objects of files that are meant to be processed and moved.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from enum import Enum
from dataclasses import dataclass
import shutil

from fs_helpers import cleanFilename, confirmFilename, formatFileSize



class MoveObject(ABC):
    source: Path
    destination: Path
    saveLocation: Path


    def __init__(self, file: str, location: str | Path):
        self.source = Path(file)
        self.saveLocation = Path(location)
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
    def move(self): 
        """ Move object from source to destination. If destination exists,
        raises OSError. """

    @abstractmethod
    def delete(self):
        """ Delete source file. """

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
        self.destination = self.saveLocation / subdirectory / finalName


    def move(self) -> None:
        if self.destination.exists():
            raise FileExistsError

        shutil.move(self.source, self.destination)


    def delete(self) -> None:
        if self.source.exists():
            self.source.unlink()


    def overwrite(self) -> None:
        if self.source.exists()\
            and self.destination.exists()\
            and self.source != self.destination\
        :
            self.source.replace(self.destination)
            # self.destination.unlink()
            # with open(self.destination, "wb") as outfile:
            #     outfile.write(self.source.read_bytes())
            # self.source.unlink()


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
                source = formatFileSize(file=self.file.source)
                destination = formatFileSize(file=self.file.destination)
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
