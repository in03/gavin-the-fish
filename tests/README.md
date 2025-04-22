# Gavin the Fish Tests

This directory contains tests for the Gavin the Fish project.

## Structure

- `unit/`: Unit tests for individual components
- `integration/`: Integration tests for API endpoints and job functionality
- `conftest.py`: Pytest configuration and fixtures

## Running Tests

To run all tests:

```bash
pytest
```

To run only unit tests:

```bash
pytest tests/unit
```

To run only integration tests:

```bash
pytest tests/integration
```

To run a specific test file:

```bash
pytest tests/integration/test_jobs_sync_threshold.py
```

## Environment Setup

The tests require a running instance of the Gavin the Fish server. Make sure the server is running on `http://localhost:8000` before running the integration tests.

The tests also require an API key, which should be defined in the `.env` file in the project root. The API key is loaded automatically by the test fixtures.

Example `.env` file:

```
API_KEY=your-api-key-here
```

## Test Coverage

To generate a test coverage report:

```bash
pytest --cov=src
```

To generate an HTML coverage report:

```bash
pytest --cov=src --cov-report=html
```

The HTML report will be generated in the `htmlcov` directory.
