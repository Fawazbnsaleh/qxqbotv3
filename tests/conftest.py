import pytest
import sys
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

@pytest.fixture
def mock_config():
    return {"host": "localhost", "port": 8080}
