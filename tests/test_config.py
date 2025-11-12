"""
Unit tests for configuration management.
"""

import pytest
import os
from unittest.mock import patch
from pydantic import ValidationError

from config import Settings, settings


class TestSettings:
    """Tests for Settings class."""
    
    def test_default_values(self):
        """Test that default values are set correctly."""
        with patch.dict(os.environ, {}, clear=True):
            test_settings = Settings()
            assert test_settings.environment == "local"
            assert test_settings.mongodb_db_name == "ai_dashboard"
            assert test_settings.widget_refresh_interval == 30000
    
    def test_environment_variable_loading(self):
        """Test loading from environment variables."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "MONGODB_URI": "mongodb://test:27017/",
            "REGISTRATION_TOKEN": "test_token_123",
            "ANTHROPIC_API_KEY": "test_key",
            "WIDGET_REFRESH_INTERVAL": "60000"
        }, clear=True):
            test_settings = Settings()
            assert test_settings.environment == "production"
            assert test_settings.mongodb_uri == "mongodb://test:27017/"
            assert test_settings.registration_token == "test_token_123"
            assert test_settings.anthropic_api_key == "test_key"
            assert test_settings.widget_refresh_interval == 60000
    
    def test_is_production_property(self):
        """Test is_production property."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=True):
            test_settings = Settings()
            assert test_settings.is_production is True
        
        with patch.dict(os.environ, {"ENVIRONMENT": "local"}, clear=True):
            test_settings = Settings()
            assert test_settings.is_production is False
        
        # Test auto-detection via DYNO
        with patch.dict(os.environ, {"DYNO": "web.1"}, clear=True):
            test_settings = Settings()
            assert test_settings.is_production is True
    
    def test_mongodb_uri_normalized(self):
        """Test MongoDB URI normalization."""
        with patch.dict(os.environ, {"MONGODB_URI": "mongodb://test:27017/"}, clear=True):
            test_settings = Settings()
            assert test_settings.mongodb_uri_normalized == "mongodb://test:27017"
        
        with patch.dict(os.environ, {"MONGODB_URI": "mongodb://test:27017"}, clear=True):
            test_settings = Settings()
            assert test_settings.mongodb_uri_normalized == "mongodb://test:27017"
    
    def test_widget_refresh_interval_type_conversion(self):
        """Test that widget_refresh_interval is converted to int."""
        with patch.dict(os.environ, {"WIDGET_REFRESH_INTERVAL": "45000"}, clear=True):
            test_settings = Settings()
            assert isinstance(test_settings.widget_refresh_interval, int)
            assert test_settings.widget_refresh_interval == 45000

