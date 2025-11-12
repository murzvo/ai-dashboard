# Test Suite Overview

This directory contains comprehensive unit tests for the AI Dashboard application.

## Test Files

- **`conftest.py`** - Shared fixtures and test configuration
- **`test_config.py`** - Configuration management tests
- **`test_dependencies.py`** - Dependency injection tests
- **`test_endpoints.py`** - API endpoint tests
- **`test_ai_generator.py`** - AI widget generation tests

## Quick Start

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_endpoints.py

# Run with coverage
pytest --cov=. --cov-report=html
```

## Test Coverage

### Configuration (`test_config.py`)
- ✅ Default values
- ✅ Environment variable loading
- ✅ Production detection
- ✅ Type conversions

### Dependencies (`test_dependencies.py`)
- ✅ Registration token verification
- ✅ Integration token verification
- ✅ Widget lookup functions
- ✅ Error handling

### Endpoints (`test_endpoints.py`)
- ✅ Health check (`/health`)
- ✅ App registration (`/register`)
- ✅ Data sharing (`/share-data`)
- ✅ Dashboard rendering (`/`)
- ✅ User widget CRUD operations
- ✅ App widget operations

### AI Generator (`test_ai_generator.py`)
- ✅ Missing API key handling
- ✅ User prompt generation
- ✅ App prompt generation
- ✅ Style preservation mode
- ✅ HTML cleaning

## Fixtures

All fixtures are defined in `conftest.py` and are automatically available to all tests:

- `client` - FastAPI TestClient
- `mock_registration_token` - Test registration token
- `mock_integration_token` - Test integration token
- `mock_app_doc` - Mock app document
- `mock_widget_doc` - Mock widget document
- `mock_user_widget_doc` - Mock user widget document
- `mock_ai_response` - Mock AI response
- `mock_database_collections` - Mocked database (auto-applied)
- `mock_ai_generator` - Mocked AI generator (auto-applied)
- `mock_config_settings` - Mocked config (auto-applied)
- `mock_database_client` - Mocked database client (auto-applied)

## Writing Tests

### Basic Test Structure

```python
def test_my_endpoint(client, mock_app_doc):
    """Test description."""
    response = client.post(
        "/endpoint",
        json={"key": "value"}
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
```

### Async Tests

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await my_async_function()
    assert result is not None
```

## Notes

- All database operations are mocked - no real database needed
- All external API calls (Anthropic) are mocked
- Tests are isolated and can run in any order
- Use fixtures for common test data

