import pytest
from pathlib import Path

from file_sorting_hat.move_objects import Video, Other



VIDEO_NAME = "video.txt"

@pytest.fixture
def sourceDir():
    path = Path(__file__).parent / "_resources" / "move_objects" / "source_dir"
    return path

@pytest.fixture
def destDir():
    path = Path(__file__).parent / "_resources" / "move_objects" / "dest_dir"
    return path

@pytest.fixture
def sourceVideoFile(sourceDir: Path, destDir: Path):
    source = sourceDir / VIDEO_NAME
    source.touch()
    yield source
    if source.is_file():
        source.unlink()
    dest = destDir / source.name
    if dest.is_file():
        dest.unlink()

@pytest.fixture
def destVideoFile(destDir: Path):
    destination = destDir / VIDEO_NAME
    destination.touch()
    yield destination
    if destination.is_file():
        destination.unlink()

@pytest.fixture
def video(sourceVideoFile, destDir):
    return Video(sourceVideoFile, destDir)

@pytest.fixture
def sourceOtherDir(sourceDir, destDir):
    ...

@pytest.fixture
def sourceOtherZip(sourceDir, destDir):
    ...

def other(sourceOtherFile, destDir):
    ...

### Tests ###

def test_video_move(video: Video, destDir: Path):
    assert video.source.is_file()
    destination = destDir / video.source.name
    video.setDestination(destination)
    video.move()
    assert destination.exists()

def test_video_overwrite(video: Video, destVideoFile: Path):
    assert video.source.is_file()
    assert destVideoFile.is_file()
    video.setDestination(destVideoFile)
    with pytest.raises(FileExistsError):
        video.move()
    video.overwrite()
    assert not video.source.is_file()
    assert video.destination.is_file()

def test_video_delete(video: Video):
    assert video.source.is_file()
    video.delete()
    assert not video.source.is_file()