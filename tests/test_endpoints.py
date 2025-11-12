"""
Unit tests for FastAPI endpoints.
"""

import pytest
from unittest.mock import Mock, patch
from fastapi import status
from bson import ObjectId
from datetime import datetime


class TestHealthCheck:
    """Tests for health check endpoint."""
    
    def test_health_check_success(self, client, mock_database_client):
        """Test successful health check."""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "environment" in data
        assert "database" in data
    
    def test_health_check_database_failure(self, client):
        """Test health check when database is unavailable."""
        with patch('database.client') as mock_client:
            mock_client.admin.command.side_effect = Exception("Connection failed")
            response = client.get("/health")
            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            data = response.json()
            assert data["status"] == "unhealthy"


class TestRegisterApp:
    """Tests for app registration endpoint."""
    
    def test_register_app_success(self, client, mock_registration_token, mock_app_doc):
        """Test successful app registration."""
        with patch('dependencies.settings') as mock_settings, \
             patch('main.settings') as mock_main_settings:
            mock_settings.registration_token = mock_registration_token
            mock_main_settings.registration_token = mock_registration_token
            
            response = client.post(
                "/register",
                json={
                    "registration_token": mock_registration_token,
                    "app_name": "Test App"
                }
            )
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "integration_token" in data
            assert "app_id" in data
            assert len(data["integration_token"]) > 0
    
    def test_register_app_invalid_token(self, client):
        """Test registration with invalid token."""
        response = client.post(
            "/register",
            json={
                "registration_token": "wrong_token",
                "app_name": "Test App"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid registration token" in response.json()["detail"]
    
    def test_register_app_missing_fields(self, client):
        """Test registration with missing required fields."""
        response = client.post(
            "/register",
            json={
                "registration_token": "test_token"
                # Missing app_name
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestShareData:
    """Tests for share-data endpoint."""
    
    def test_share_data_success(self, client, mock_integration_token, mock_app_doc, mock_ai_response):
        """Test successful data sharing."""
        response = client.post(
            "/share-data",
            json={
                "integration_token": mock_integration_token,
                "data": {"test": "data"},
                "render_prompt": "Create a test widget"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "message" in data
    
    def test_share_data_invalid_token(self, client):
        """Test data sharing with invalid integration token."""
        with patch('dependencies.apps_collection') as mock_collection:
            mock_collection.find_one.return_value = None
            
            response = client.post(
                "/share-data",
                json={
                    "integration_token": "invalid_token",
                    "data": {"test": "data"},
                    "render_prompt": "Create a test widget"
                }
            )
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Invalid integration token" in response.json()["detail"]


class TestDashboard:
    """Tests for dashboard endpoint."""
    
    def test_dashboard_success(self, client, mock_widget_doc, mock_user_widget_doc):
        """Test successful dashboard rendering."""
        with patch('main.apps_collection') as mock_apps, \
             patch('main.widgets_collection') as mock_widgets:
            
            mock_apps.find.return_value = []
            mock_widgets.find.return_value = [mock_user_widget_doc]
            
            response = client.get("/")
            assert response.status_code == status.HTTP_200_OK
            assert "text/html" in response.headers["content-type"]
            assert "dashboard" in response.text.lower()


class TestUserWidgets:
    """Tests for user widget endpoints."""
    
    def test_create_user_widget_success(self, client, mock_user_widget_doc, mock_ai_response):
        """Test successful user widget creation."""
        widget_id = str(mock_user_widget_doc["_id"])
        
        with patch('main.widgets_collection') as mock_collection:
            mock_collection.insert_one.return_value = Mock(inserted_id=mock_user_widget_doc["_id"])
            
            response = client.post(
                "/api/user-widgets/create",
                json={
                    "prompt": "Create a weather widget",
                    "widget_name": "Weather"
                }
            )
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert "widget_id" in data
    
    def test_edit_user_widget_success(self, client, mock_user_widget_doc, mock_ai_response):
        """Test successful user widget edit."""
        widget_id = str(mock_user_widget_doc["_id"])
        
        with patch('main.widgets_collection') as mock_collection:
            mock_collection.find_one.return_value = mock_user_widget_doc
            mock_collection.update_one.return_value = Mock(modified_count=1)
            
            response = client.post(
                "/api/user-widgets/edit",
                json={
                    "widget_id": widget_id,
                    "prompt": "Updated prompt"
                }
            )
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
    
    def test_delete_user_widget_success(self, client, mock_user_widget_doc):
        """Test successful user widget deletion."""
        widget_id = str(mock_user_widget_doc["_id"])
        
        with patch('main.widgets_collection') as mock_collection:
            mock_collection.find_one.return_value = mock_user_widget_doc
            mock_collection.delete_one.return_value = Mock(deleted_count=1)
            
            response = client.post(
                "/api/user-widgets/delete",
                json={
                    "widget_id": widget_id
                }
            )
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
    
    def test_refresh_user_widget_success(self, client, mock_user_widget_doc, mock_ai_response):
        """Test successful user widget refresh."""
        widget_id = str(mock_user_widget_doc["_id"])
        
        with patch('main.widgets_collection') as mock_collection:
            mock_collection.find_one.return_value = mock_user_widget_doc
            mock_collection.update_one.return_value = Mock(modified_count=1)
            
            response = client.post(f"/api/user-widgets/{widget_id}/refresh")
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "html" in data


class TestAppWidgets:
    """Tests for app widget endpoints."""
    
    def test_refresh_app_widget_success(self, client, mock_app_doc, mock_widget_doc, mock_ai_response):
        """Test successful app widget refresh."""
        app_id = str(mock_app_doc["_id"])
        
        with patch('main.widgets_collection') as mock_collection:
            mock_collection.find_one.return_value = mock_widget_doc
            mock_collection.update_one.return_value = Mock(modified_count=1)
            
            response = client.post(f"/api/app-widgets/{app_id}/refresh")
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert "html" in data
    
    def test_full_refresh_app_widget_success(self, client, mock_app_doc, mock_widget_doc, mock_ai_response):
        """Test successful app widget full refresh."""
        app_id = str(mock_app_doc["_id"])
        
        with patch('main.widgets_collection') as mock_collection:
            mock_collection.find_one.return_value = mock_widget_doc
            mock_collection.update_one.return_value = Mock(modified_count=1)
            
            response = client.post(f"/api/app-widgets/{app_id}/full-refresh")
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
    
    def test_delete_app_widget_success(self, client, mock_app_doc, mock_widget_doc):
        """Test successful app widget deletion."""
        app_id = str(mock_app_doc["_id"])
        
        with patch('main.apps_collection') as mock_apps, \
             patch('main.widgets_collection') as mock_widgets:
            
            mock_widgets.find_one.return_value = mock_widget_doc
            mock_widgets.delete_one.return_value = Mock(deleted_count=1)
            mock_apps.delete_one.return_value = Mock(deleted_count=1)
            
            response = client.delete(f"/api/app-widgets/{app_id}")
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True

