"""
Unit tests for FastAPI dependencies.
"""

import pytest
from unittest.mock import patch
from fastapi import HTTPException
from bson import ObjectId
from datetime import datetime

from dependencies import (
    verify_registration_token,
    verify_integration_token,
    get_widget_by_id,
    get_app_widget_by_app_id
)
from models import RegisterRequest, ShareDataRequest


class TestVerifyRegistrationToken:
    """Tests for verify_registration_token dependency."""
    
    def test_valid_token(self, mock_registration_token):
        """Test with valid registration token."""
        with patch('dependencies.settings') as mock_settings:
            mock_settings.registration_token = mock_registration_token
            request = RegisterRequest(
                registration_token=mock_registration_token,
                app_name="Test App"
            )
            result = verify_registration_token(request)
            assert result == request
    
    def test_invalid_token(self, mock_config_settings):
        """Test with invalid registration token."""
        request = RegisterRequest(
            registration_token="wrong_token",
            app_name="Test App"
        )
        with pytest.raises(HTTPException) as exc_info:
            verify_registration_token(request)
        assert exc_info.value.status_code == 401
        assert "Invalid registration token" in str(exc_info.value.detail)


class TestVerifyIntegrationToken:
    """Tests for verify_integration_token dependency."""
    
    @pytest.mark.asyncio
    async def test_valid_integration_token(self, mock_app_doc):
        """Test with valid integration token."""
        with patch('dependencies.apps_collection') as mock_collection:
            mock_collection.find_one.return_value = mock_app_doc
            
            request = ShareDataRequest(
                integration_token="test_integration_token_456",
                data={"test": "data"},
                render_prompt="Test prompt"
            )
            
            result = await verify_integration_token(request)
            assert result == mock_app_doc
    
    @pytest.mark.asyncio
    async def test_invalid_integration_token(self):
        """Test with invalid integration token."""
        with patch('dependencies.apps_collection') as mock_collection:
            mock_collection.find_one.return_value = None
            
            request = ShareDataRequest(
                integration_token="invalid_token",
                data={"test": "data"},
                render_prompt="Test prompt"
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await verify_integration_token(request)
            assert exc_info.value.status_code == 401
            assert "Invalid integration token" in str(exc_info.value.detail)


class TestGetWidgetById:
    """Tests for get_widget_by_id dependency."""
    
    @pytest.mark.asyncio
    async def test_widget_found(self, mock_user_widget_doc):
        """Test finding widget by ID."""
        widget_id = str(mock_user_widget_doc["_id"])
        
        with patch('dependencies.widgets_collection') as mock_collection:
            mock_collection.find_one.return_value = mock_user_widget_doc
            
            result = await get_widget_by_id(widget_id, user_created=True)
            assert result == mock_user_widget_doc
    
    @pytest.mark.asyncio
    async def test_widget_not_found(self):
        """Test when widget is not found."""
        widget_id = str(ObjectId())
        
        with patch('dependencies.widgets_collection') as mock_collection:
            mock_collection.find_one.return_value = None
            
            with pytest.raises(HTTPException) as exc_info:
                await get_widget_by_id(widget_id, user_created=True)
            assert exc_info.value.status_code == 404
            assert "Widget not found" in str(exc_info.value.detail)


class TestGetAppWidgetByAppId:
    """Tests for get_app_widget_by_app_id dependency."""
    
    @pytest.mark.asyncio
    async def test_app_widget_found(self, mock_widget_doc):
        """Test finding app widget by app_id."""
        app_id = mock_widget_doc["app_id"]
        
        with patch('dependencies.widgets_collection') as mock_collection:
            mock_collection.find_one.return_value = mock_widget_doc
            
            result = await get_app_widget_by_app_id(app_id)
            assert result == mock_widget_doc
    
    @pytest.mark.asyncio
    async def test_app_widget_not_found(self):
        """Test when app widget is not found."""
        app_id = str(ObjectId())
        
        with patch('dependencies.widgets_collection') as mock_collection:
            mock_collection.find_one.return_value = None
            
            with pytest.raises(HTTPException) as exc_info:
                await get_app_widget_by_app_id(app_id)
            assert exc_info.value.status_code == 404
            assert "App widget not found" in str(exc_info.value.detail)

