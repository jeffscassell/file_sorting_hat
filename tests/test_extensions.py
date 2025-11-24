import pytest
from pathlib import Path

from file_sorting_hat.extensions import Config



@pytest.fixture
def config(resources: Path) -> Config:
    file = resources / "config"
    config = Config()
    config.load(file)
    return config


def test_config_env(config: Config):
    assert config.isLoaded

def test_config_validation(config: Config):
    with pytest.raises(OSError):
        config.validatePath("INVALID")

def test_config_paths(config: Config):
    path = Path.cwd()
    config.setPath("test", path)
    assert path == config.paths.get("test")

def test_config_settings(config: Config):
    setting = "setting"
    config.setSetting("test", setting)
    assert setting == config.settings.get("test")