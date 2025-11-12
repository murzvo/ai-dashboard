"""
Pytest configuration and fixtures for testing.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from bson import ObjectId
from datetime import datetime

# Import app after setting up mocks
from main import app

# Try to import TestClient - handle version differences
try:
    from fastapi.testclient import TestClient
except ImportError:
    from starlette.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    # Use starlette's TestClient directly to avoid version conflicts
    from starlette.testclient import TestClient as StarletteTestClient
    return StarletteTestClient(app)


@pytest.fixture
def mock_registration_token():
    """Mock registration token for testing."""
    return "test_registration_token_123"


@pytest.fixture
def mock_integration_token():
    """Mock integration token for testing."""
    return "test_integration_token_456"


@pytest.fixture
def mock_app_doc(mock_integration_token):
    """Mock app document."""
    return {
        "_id": ObjectId(),
        "app_name": "Test App",
        "integration_token": mock_integration_token,
        "registration_date": datetime.utcnow(),
        "created_at": datetime.utcnow()
    }


@pytest.fixture
def mock_widget_doc(mock_app_doc):
    """Mock widget document."""
    return {
        "_id": ObjectId(),
        "app_id": str(mock_app_doc["_id"]),
        "data": {"test": "data"},
        "render_prompt": "Test prompt",
        "generated_html": "<div>Test HTML</div>",
        "updated_at": datetime.utcnow(),
        "user_created": False
    }


@pytest.fixture
def mock_user_widget_doc():
    """Mock user-created widget document."""
    return {
        "_id": ObjectId(),
        "widget_name": "User Widget",
        "render_prompt": "User prompt",
        "generated_html": "<div>User HTML</div>",
        "created_at": datetime.utcnow(),
        "user_created": True
    }


@pytest.fixture
def mock_ai_response():
    """Mock AI generation response."""
    return "<div class='widget'>Generated Widget HTML</div>"


@pytest.fixture(autouse=True)
def mock_database_collections(mock_app_doc, mock_widget_doc, mock_user_widget_doc):
    """Mock database collections for all tests."""
    with patch('main.apps_collection') as mock_apps, \
         patch('main.widgets_collection') as mock_widgets, \
         patch('dependencies.apps_collection') as mock_apps_dep, \
         patch('dependencies.widgets_collection') as mock_widgets_dep:
        
        # Setup mock apps collection
        mock_apps.insert_one.return_value = Mock(inserted_id=mock_app_doc["_id"])
        mock_apps.find_one.return_value = mock_app_doc
        mock_apps.find.return_value = [mock_app_doc]
        mock_apps.delete_one.return_value = Mock(deleted_count=1)
        mock_apps.update_one.return_value = Mock(modified_count=1)
        
        # Setup mock widgets collection
        mock_widgets.find_one.return_value = mock_widget_doc
        mock_widgets.find.return_value = [mock_widget_doc, mock_user_widget_doc]
        mock_widgets.insert_one.return_value = Mock(inserted_id=mock_user_widget_doc["_id"])
        mock_widgets.update_one.return_value = Mock(modified_count=1)
        mock_widgets.delete_one.return_value = Mock(deleted_count=1)
        
        # Same for dependencies
        mock_apps_dep.find_one.return_value = mock_app_doc
        mock_widgets_dep.find_one.return_value = mock_widget_doc
        
        yield {
            "apps": mock_apps,
            "widgets": mock_widgets
        }


@pytest.fixture(autouse=True)
def mock_ai_generator(mock_ai_response):
    """Mock AI generator for all tests."""
    async def async_mock(*args, **kwargs):
        return mock_ai_response
    
    with patch('main.generate_widget_html', side_effect=async_mock) as mock_gen:
        yield mock_gen


@pytest.fixture(autouse=True)
def mock_config_settings(mock_registration_token):
    """Mock config settings for all tests."""
    with patch('config.settings') as mock_settings:
        mock_settings.registration_token = mock_registration_token
        mock_settings.widget_refresh_interval = 30000
        mock_settings.environment = "local"
        mock_settings.is_production = False
        yield mock_settings


@pytest.fixture(autouse=True)
def mock_database_client():
    """Mock database client for health check."""
    with patch('database.client') as mock_client:
        mock_client.admin.command.return_value = {"ok": 1}
        yield mock_client

