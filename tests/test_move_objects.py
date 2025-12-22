import pytest
from pathlib import Path
import shutil

from fs_helpers import zipDirectory

from file_sorting_hat.move_objects import Video, Other, MoveObject



@pytest.fixture
def sourceDir(resources: Path):
    return resources / "move_objects" / "source_dir"

@pytest.fixture
def destDir(resources: Path):
    return resources / "move_objects" / "dest_dir"


class TestClassMethods:
    def testTagExtraction(self):
        assert MoveObject._extractTag("[one_tag]_name") == \
            "one_tag"
        assert MoveObject._extractTag("[one tag] name") == \
            "one_tag"
        assert MoveObject._extractTag("name") == \
            None
        assert MoveObject._extractTag("[one_tag,two_tag] name") == \
            "one_tag,two_tag"
        assert MoveObject._extractTag("[one tag, two tag] name") == \
            "one_tag,two_tag"
        assert MoveObject._extractTag("[one_tag, two_tag] name") == \
            "one_tag,two_tag"
    
    def testNameExtraction(self):
        assert MoveObject._extractName("[one_tag]_name") == \
            "name"
        assert MoveObject._extractName("[one tag] name") == \
            "name"
        assert MoveObject._extractName("[one tag]-name") == \
            "name"
        assert MoveObject._extractName("name") == \
            "name"

        with pytest.raises(ValueError):
            MoveObject._extractName("[one_tag]")


class TestVideo:

    VIDEO_NAME = "video.txt"
    
    @pytest.fixture
    def sourceFilePath(self, sourceDir: Path):
        return sourceDir / self.VIDEO_NAME
    
    @pytest.fixture
    def destinationFilePath(self, destDir: Path):
        return destDir / self.VIDEO_NAME

    @pytest.fixture
    def sourceFile(self, sourceFilePath: Path):
        sourceFilePath.write_text("source")
        return sourceFilePath

    @pytest.fixture
    def destinationFile(self, destinationFilePath: Path):
        destinationFilePath.write_text("destination")
        return destinationFilePath

    @pytest.fixture
    def video(self, sourceFile: Path, destDir: Path):
        return Video(sourceFile, destDir)

    @pytest.fixture(autouse=True)
    def cleanup(self, sourceFilePath: Path, destinationFilePath: Path):
        yield
        if sourceFilePath.exists():
            sourceFilePath.unlink()
        if destinationFilePath.exists():
            destinationFilePath.unlink()


    def test_video_validate(self, sourceFilePath: Path, destDir: Path):
        assert not sourceFilePath.exists()
        video = Video(sourceFilePath, destDir)
        with pytest.raises(FileNotFoundError):
            video.validate()
        sourceFilePath.touch()
        assert sourceFilePath.is_file()
        video.validate()
        
        assert destDir.is_dir()
        wrongType = Video(destDir, destDir)
        with pytest.raises(TypeError):
            wrongType.validate()

    def test_video_move(self, video: Video, destinationFilePath: Path):
        assert video.source.is_file()
        assert not destinationFilePath.exists()
        video.setDestination(destinationFilePath)
        video.move()
        assert destinationFilePath.exists()

    def test_video_overwrite(self, video: Video, destinationFile: Path):
        assert video.source.read_text() == "source"
        assert destinationFile.read_text() == "destination"
        video.setDestination(destinationFile)
        with pytest.raises(FileExistsError):
            video.move()
        video.overwrite()
        assert not video.source.is_file()
        assert video.destination.read_text() == "source"

    def test_video_delete(self, video: Video):
        assert video.source.is_file()
        video.delete()
        assert not video.source.exists()


class TestOther:

    OTHER_NAME = "other_dir"

    @pytest.fixture
    def sourceOtherPath(self, sourceDir: Path):
        source = sourceDir / self.OTHER_NAME
        return source

    @pytest.fixture
    def destOtherPath(self, destDir: Path):
        destination = destDir / self.OTHER_NAME
        return destination
    
    @pytest.fixture
    def sourceOtherDir(self, sourceOtherPath: Path):
        self._buildTree(sourceOtherPath, "source")
        return sourceOtherPath

    @pytest.fixture
    def sourceOtherZip(self, sourceOtherDir: Path):
        return zipDirectory(sourceOtherDir)
    
    @pytest.fixture
    def destOtherDir(self, destOtherPath: Path):
        self._buildTree(destOtherPath, "destination")
        return destOtherPath

    @pytest.fixture(autouse=True)
    def other(self, sourceOtherDir: Path, destDir: Path):
        return Other(sourceOtherDir, destDir)

    @pytest.fixture(autouse=True)
    def otherZip(self, sourceOtherZip: Path, destDir: Path):
        return Other(sourceOtherZip, destDir)

    @pytest.fixture(autouse=True)
    def cleanup(self, sourceOtherPath: Path, destOtherPath: Path):
        yield
        if sourceOtherPath.is_dir():
            shutil.rmtree(sourceOtherPath)
        if sourceOtherPath.with_suffix(".zip").is_file():
            sourceOtherPath.with_suffix(".zip").unlink()
        if destOtherPath.is_dir():
            shutil.rmtree(destOtherPath)


    def _buildTree(self, path: Path, contents: str):
        fileEnds = ("1", "2")
        path.mkdir()
        subdir = path / "subdir"
        subdir.mkdir()
        for ending in fileEnds:
            name = f"file_{ending}.txt"
            file = path / name
            subfile = subdir / name
            file.write_text(contents)
            subfile.write_text(contents)

    def _validateTree(self, path: Path, contents: str):
        fileEnds = ("1", "2")
        subdir = path / "subdir"
        for ending in fileEnds:
            name = f"file_{ending}.txt"
            file = path / name
            subfile = subdir / name
            assert file.read_text() == contents
            assert subfile.read_text() == contents


    def test_other_move_zip(self, otherZip: Other, destOtherPath):
        assert otherZip.source.is_file()
        assert not destOtherPath.is_dir()
        otherZip.setDestination(destOtherPath)
        otherZip.move()
        assert not otherZip.source.is_file()
        assert destOtherPath.is_dir()

    def test_other_delete_zip(self, otherZip: Other):
        assert otherZip.source.is_file()
        otherZip.delete()
        assert not otherZip.source.is_file()

    def test_other_move(self, other: Other, destOtherPath: Path):
        assert other.source.is_dir()
        self._validateTree(other.source, "source")
        assert not destOtherPath.exists()
        other.setDestination(destOtherPath)
        other.move()
        assert not other.source.exists()
        self._validateTree(destOtherPath, "source")

    def test_other_overwrite(self, other: Other, destOtherDir: Path):
        assert other.source.is_dir()
        self._validateTree(other.source, "source")
        assert destOtherDir.exists()
        self._validateTree(destOtherDir, "destination")
        
        other.setDestination(destOtherDir)
        with pytest.raises(IsADirectoryError):
            other.move()
        other.overwrite()
        assert not other.source.exists()
        self._validateTree(destOtherDir, "source")

    def test_other_delete(self, other: Other):
        assert other.source.is_dir()
        self._validateTree(other.source, "source")
        other.delete()
        assert not other.source.exists()
