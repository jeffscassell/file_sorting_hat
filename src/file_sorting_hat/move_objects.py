"""
move_objects.py

The objects of files that are meant to be processed and moved.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from enum import Enum
from dataclasses import dataclass
import shutil
from zipfile import ZipFile

from fs_helpers import cleanFilename, confirmFilename, size, unzip



class MoveObject(ABC):
    source: Path
    destination: Path
    directory: Path


    def __init__(self, source: str | Path, directory: str | Path):
        self.source = Path(source)
        self.directory = Path(directory)

    def validate(self):
        """ Make sure `source` at least exists on the filesystem. """
        if not self.source.exists():
            raise FileNotFoundError(f"Path does not exist: {self.source}")

    def _sanitizeFilename(self, filename: str) -> str:
        return cleanFilename(filename)

    def _destinationSafety(self) -> None:
        if not hasattr(self, "destination"):
            raise ValueError("Missing destination")
    
    def setDestination(self, path: str | Path) -> None:
        self.destination = Path(path)

    @abstractmethod
    def buildOptions(self): ...

    @abstractmethod
    def move(self): 
        """ Move object from source to destination. If destination exists,
        raise FileExistsError. """

    @abstractmethod
    def delete(self):
        """ Delete source file/directory, even if the directory is not
        empty. """

    @abstractmethod
    def overwrite(self):
        """ Move object from source to destination. If destination exists,
        overwrite. """

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


    def delete(self) -> None:
        self.validate()
        if self.source.exists():
            self.source.unlink()


    def move(self) -> None:
        if self.destination.is_file():
            raise FileExistsError(f"File exists: {self.destination}")

        self.overwrite()


    def overwrite(self) -> None:
        self.validate()
        self._destinationSafety()
        if self.destination.is_file():
            self.destination.unlink()
        
        shutil.move(self.source, self.destination)


class Other(MoveObject):
    
    unzippedDirectory: Path | None = None
    
    def validate(self) -> None:
        super().validate()  # `source` at least exists.
        
        if not self.source.is_dir():
            if not self.isZip():
                raise TypeError(f"Path must be a directory or ZIP file: "
                    f"{self.source}")
    
    def isZip(self) -> bool:
        if self.source.is_file() and\
            self.source.suffix == ".zip":
                return True
        return False
        
    def _tryUnzip(self) -> None:
        if not self.isZip():
            return

        extracted: Path = self.source.parent / self.source.stem
        if not extracted.is_dir():
            unzip(self.source, extracted)
        self.unzippedDirectory = extracted


    def _cleanup(self) -> None:
        """ Call after a `move()`/`overwrite()` operation to cleanup remnant
        files/directories. """
        if self.unzippedDirectory:
            if self.unzippedDirectory.is_dir(): self.unzippedDirectory.rmdir()
            if self.source.is_file(): self.source.unlink()
        if self.source.is_dir(): self.source.rmdir()


    def buildOptions(self) -> None:
        oldName = newName = self.source.stem
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

        destination = self.directory / finalName
        self.setDestination(destination)


    def delete(self) -> None:
        self.validate()
        if self.source.is_dir():
            shutil.rmtree(self.source)
        elif self.source.is_file():
            self.source.unlink()
        if self.unzippedDirectory:
            if self.unzippedDirectory.is_dir():
                shutil.rmtree(self.unzippedDirectory)


    def move(self) -> None:
        if self.destination.is_dir():
            raise IsADirectoryError(f"Destination directory already exists: "
                f"{self.destination}")

        self.overwrite()


    def overwrite(self) -> None:
        self.validate()
        self._destinationSafety()
        self._tryUnzip()

        if self.destination.is_dir():
            shutil.rmtree(self.destination)

        if self.unzippedDirectory:
            sourceDirectory = self.unzippedDirectory
        else:
            sourceDirectory = self.source

        # Source is already in the right place, but with the wrong name.
        if sourceDirectory.parent == self.destination.parent:
            shutil.move(self.source, self.destination.parent)
            return

        self.destination.mkdir()
        for path in sourceDirectory.iterdir():
            shutil.move(path, self.destination)

        self._cleanup()


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
        
        if len(prefix) > 50:
            prefix = prefix[:45] + "(...)"

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
