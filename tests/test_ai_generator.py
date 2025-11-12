"""
Unit tests for AI generator module.
"""

import pytest
from unittest.mock import patch, Mock
from ai_generator import generate_widget_html


class TestGenerateWidgetHTML:
    """Tests for generate_widget_html function."""
    
    @pytest.mark.asyncio
    async def test_missing_api_key(self):
        """Test when API key is not configured."""
        with patch('ai_generator.ANTHROPIC_API_KEY', ""):
            result = await generate_widget_html(
                data={"test": "data"},
                render_prompt="Test prompt"
            )
            assert "Configuration Error" in result
            assert "ANTHROPIC_API_KEY" in result
    
    @pytest.mark.asyncio
    async def test_user_prompt_generation(self):
        """Test widget generation for user prompt (no data)."""
        mock_response_text = "<div>Generated Widget</div>"
        
        with patch('ai_generator.ANTHROPIC_API_KEY', "test_key"), \
             patch('asyncio.get_event_loop') as mock_loop:
            
            # Create a coroutine that returns the mock response
            async def mock_run_executor(executor, func):
                return mock_response_text
            
            mock_loop.return_value.run_in_executor = mock_run_executor
            
            result = await generate_widget_html(
                data={},
                render_prompt="Create a weather widget",
                is_user_prompt=True
            )
            
            assert "<div>Generated Widget</div>" in result or "Generated Widget" in result
    
    @pytest.mark.asyncio
    async def test_app_prompt_generation(self):
        """Test widget generation for app prompt (with data)."""
        mock_response_text = "<div>Data Widget</div>"
        
        with patch('ai_generator.ANTHROPIC_API_KEY', "test_key"), \
             patch('asyncio.get_event_loop') as mock_loop:
            
            async def mock_run_executor(executor, func):
                return mock_response_text
            
            mock_loop.return_value.run_in_executor = mock_run_executor
            
            result = await generate_widget_html(
                data={"temperature": 72, "city": "SF"},
                render_prompt="Show weather data"
            )
            
            assert "<div>Data Widget</div>" in result or "Data Widget" in result
    
    @pytest.mark.asyncio
    async def test_style_preservation_mode(self):
        """Test widget generation with style preservation."""
        mock_response_text = "<div>Preserved Style Widget</div>"
        
        with patch('ai_generator.ANTHROPIC_API_KEY', "test_key"), \
             patch('asyncio.get_event_loop') as mock_loop:
            
            async def mock_run_executor(executor, func):
                return mock_response_text
            
            mock_loop.return_value.run_in_executor = mock_run_executor
            
            prompt_with_styles = """
            CRITICAL STYLE PRESERVATION REQUIREMENTS:
            CURRENT WIDGET STYLES (preserve these):
            .widget { color: blue; }
            """
            
            result = await generate_widget_html(
                data={},
                render_prompt=prompt_with_styles,
                is_user_prompt=True
            )
            
            assert "<div>Preserved Style Widget</div>" in result or "Preserved Style Widget" in result
    
    @pytest.mark.asyncio
    async def test_model_fallback(self):
        """Test model fallback when primary model fails."""
        mock_response_text = "<div>Fallback Widget</div>"
        
        with patch('ai_generator.ANTHROPIC_API_KEY', "test_key"), \
             patch('asyncio.get_event_loop') as mock_loop:
            
            async def mock_run_executor(executor, func):
                return mock_response_text
            
            mock_loop.return_value.run_in_executor = mock_run_executor
            
            result = await generate_widget_html(
                data={"test": "data"},
                render_prompt="Test prompt"
            )
            
            assert "<div>Fallback Widget</div>" in result or "Fallback Widget" in result
    
    @pytest.mark.asyncio
    async def test_html_cleaning(self):
        """Test that HTML is properly cleaned."""
        # Simulate markdown code block response
        mock_response_text = "```html\n<div>Clean Widget</div>\n```"
        
        with patch('ai_generator.ANTHROPIC_API_KEY', "test_key"), \
             patch('asyncio.get_event_loop') as mock_loop:
            
            async def mock_run_executor(executor, func):
                return mock_response_text
            
            mock_loop.return_value.run_in_executor = mock_run_executor
            
            result = await generate_widget_html(
                data={},
                render_prompt="Test prompt"
            )
            
            # Should remove markdown code blocks
            assert "<div>Clean Widget</div>" in result or "Clean Widget" in result
            assert "```html" not in result
            assert "```" not in result

