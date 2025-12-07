import pytest
from unittest.mock import Mock, patch
from pathlib import Path


@pytest.fixture
def mock_genai():
    with patch('smart_qa.client.genai') as mock:
        mock_model = Mock()
        mock.GenerativeModel.return_value = mock_model
        yield mock, mock_model


@pytest.fixture
def sample_text():
    return "Python is a programming language created by Guido van Rossum in 1991."


@pytest.fixture
def sample_text_file(tmp_path):
    file_path = tmp_path / "test.txt"
    file_path.write_text("Python is a programming language created by Guido van Rossum in 1991.")
    return str(file_path)


@pytest.fixture
def mock_api_response():
    mock_response = Mock()
    mock_response.text = "This is a mock response from the API."
    return mock_response


@pytest.fixture
def mock_json_response():
    mock_response = Mock()
    mock_response.text = '{"People": ["Guido van Rossum"], "Dates": ["1991"], "Locations": ["Netherlands"]}'
    return mock_response


@pytest.fixture
def mock_json_response_with_markdown():
    mock_response = Mock()
    mock_response.text = '```json\n{"People": ["John Doe"], "Dates": ["2024"], "Locations": ["NYC"]}\n```'
    return mock_response


@pytest.fixture(autouse=True)
def cleanup_cache():
    yield
    cache_file = Path("cache.json")
    if cache_file.exists():
        cache_file.unlink()