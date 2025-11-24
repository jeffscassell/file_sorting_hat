import pytest
from pathlib import Path



@pytest.fixture
def resources():
    return Path(__file__).parent / "_resources"