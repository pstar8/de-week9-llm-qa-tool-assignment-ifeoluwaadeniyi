# Smart Q&A Tool

A production-ready Python library for AI-powered text analysis using Google Gemini API. Built with caching, error handling, and structured data extraction.

## Features

- **Text Summarization**: Generate concise summaries of documents
- **Q&A System**: Answer questions based on provided context
- **Entity Extraction**: Extract people, dates, and locations as structured JSON
- **Smart Caching**: File-based caching to reduce API costs
- **Retry Logic**: Automatic retry with exponential backoff
- **CLI Interface**: Full command-line interface with argparse

## Installation

### Prerequisites

- Python 3.12+
- Poetry
- Google Gemini API key

### Setup

1. **Clone and navigate to project**
```bash
cd smart_qa_project
```

2. **Install dependencies with Poetry**
```bash
poetry install
```

3. **Configure API key**

Create a `.env` file in the project root:
```bash
GOOGLE_API_KEY=your_api_key_here
```

Get your API key from: https://aistudio.google.com/app/apikey

## Usage

### Command Line Interface

**Basic usage with file input:**
```bash
poetry run python main.py --file path/to/document.txt
```

**Save output to file:**
```bash
poetry run python main.py --file input.txt --save output.txt
```

**Clear cache before running:**
```bash
poetry run python main.py --clear-cache --file input.txt
```

**Interactive mode (paste text):**
```bash
poetry run python main.py
```

### Python API
```python
from smart_qa.client import LLMClient

client = LLMClient()

# Summarize text
summary = client.summarize("Your long text here...")
print(summary)

# Ask questions
context = "Python was created by Guido van Rossum in 1991."
answer = client.ask(context, "Who created Python?")
print(answer)

# Extract entities
entities = client.extract_entities("John met Sarah in New York on January 1, 2024.")
print(entities)
# Output: {"People": ["John", "Sarah"], "Dates": ["January 1, 2024"], "Locations": ["New York"]}

# Clear cache
LLMClient.clear_cache()
```

## Architecture

### Core Components

- **LLMClient**: Main client class with API interaction
- **file_cache**: Decorator for persistent caching
- **retry_on_failure**: Decorator for automatic retries with exponential backoff
- **LLMAPIError**: Custom exception for API errors

### Caching Strategy

The library uses file-based caching (`cache.json`) to store API responses. Cache keys are generated using MD5 hashes of function names and arguments. This:
- Reduces API costs
- Improves response time
- Persists across sessions

### Error Handling

- Automatic retry up to 3 attempts
- Exponential backoff (1s, 2s, 4s)
- Custom `LLMAPIError` exceptions
- Graceful degradation

## Testing

### Run all tests
```bash
poetry run pytest -v
```

### Check test coverage
```bash
poetry run pytest --cov=smart_qa --cov-report=term-missing
```

### Expected output
```
==================== 16 passed ====================
Coverage: 100%
```

### Test Structure
- `tests/conftest.py`: Pytest fixtures and mocks
- `tests/test_client.py`: Comprehensive unit tests
- `tests/data/sample.txt`: Sample test data

All tests use mocks to avoid actual API calls during testing.

## Project Structure
```
smart_qa_project/
├── smart_qa/
│   ├── __init__.py
│   ├── client.py              # Main LLMClient class
│   └── custom_exceptions.py   # Custom exceptions
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # Test fixtures
│   ├── test_client.py         # Unit tests
│   └── data/
│       └── sample.txt         # Test data
├── main.py                    # CLI application
├── pyproject.toml             # Poetry configuration
├── poetry.lock                # Locked dependencies
├── .env                       # API key (not in git)
├── .gitignore
└── README.md
```

## Dependencies

### Main
- `google-generativeai`: Google Gemini API client
- `python-dotenv`: Environment variable management

### Development
- `pytest`: Testing framework
- `pytest-mock`: Mocking utilities
- `pytest-cov`: Coverage reporting

## Configuration

### Environment Variables
- `GOOGLE_API_KEY`: Your Google Gemini API key (required)

### Cache Location
- Default: `cache.json` in project root
- Can be cleared with `--clear-cache` flag or `LLMClient.clear_cache()`

## Rate Limits

Google Gemini API free tier limits:
- 60 requests per minute
- Daily quota applies

The library automatically handles rate limit errors with retry logic.

## Troubleshooting

**Problem**: `GOOGLE_API_KEY not found`
- Ensure `.env` file exists in project root
- Check no spaces around `=` in `.env`
- Verify key is valid

**Problem**: `Quota exceeded`
- Wait for rate limit to reset
- Consider upgrading API plan
- Use caching to reduce requests

**Problem**: `Module not found`
- Run `poetry install`
- Activate environment with `poetry shell`

## Development

### Adding new features
1. Add method to `LLMClient` class
2. Add caching/retry decorators as needed
3. Write unit tests with mocks
4. Update README

### Running in development
```bash
poetry shell
python main.py --file tests/data/sample.txt
```

## License

This project is for educational purposes as part of the Data Epic Solutions capstone project.

## Authors

Built as a capstone project for Week 9 - Advanced AI Engineering curriculum.