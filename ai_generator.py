"""
AI widget generator - generates HTML/CSS from data and prompt using Claude 3.5 Sonnet.
"""

import json
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any
from anthropic import Anthropic
from config import ANTHROPIC_API_KEY

# Thread pool executor for running blocking Anthropic API calls
_executor = ThreadPoolExecutor(max_workers=5)


async def generate_widget_html(data: Dict[str, Any], render_prompt: str, is_user_prompt: bool = False) -> str:
    """
    Generate widget HTML/CSS using Claude 3.5 Sonnet based on data and render prompt.
    
    Args:
        data: The dataset to render
        render_prompt: Instructions on how to render the data
        
    Returns:
        HTML string for the widget (with embedded CSS in <style> tag)
    """
    # Check if API key is configured
    if not ANTHROPIC_API_KEY:
        return """
        <div class="widget-error" style="padding: 20px; color: #d32f2f; background: #ffebee; border-radius: 8px;">
            <h3>⚠️ Configuration Error</h3>
            <p>ANTHROPIC_API_KEY is not set. Please add it to your .env file.</p>
            <p>Get your API key from <a href="https://console.anthropic.com" target="_blank">console.anthropic.com</a></p>
        </div>
        """
    
    try:
        # Build the prompt based on whether it's a user prompt (no data) or app prompt (with data)
        if is_user_prompt or not data:
            # User prompt - direct request to AI, no data provided
            # Check if the prompt contains style preservation instructions
            has_style_preservation = "CRITICAL STYLE PRESERVATION" in render_prompt or "CURRENT WIDGET STYLES" in render_prompt
            
            if has_style_preservation:
                # Style preservation mode - emphasize keeping existing styles
                prompt = f"""Generate a complete, production-ready widget based on the following user request.

USER REQUEST:
{render_prompt}

CRITICAL INSTRUCTIONS:
- Follow the style preservation requirements EXACTLY as specified above
- If CSS styles are provided in the request, USE THEM EXACTLY or create very similar styles
- Preserve colors, fonts, spacing, layout, and all visual properties
- Only update the content/data, NOT the styling
- Keep the same visual appearance and design aesthetic

REQUIREMENTS:
- The widget should be visually appealing and fulfill the user's request
- Use modern CSS (flexbox/grid, responsive design)
- Ensure the widget is self-contained (all styles inline or in a <style> tag)
- Make it responsive and accessible
- Use semantic HTML
- The widget should be ready to inject into a dashboard
- CRITICAL: All CSS must be scoped to the widget content only - use class names that won't conflict with dashboard styles
- Avoid global styles, body/html selectors, or styles that affect elements outside the widget
- Use inline styles or scoped <style> tags within the widget HTML
- If the request requires real data (like weather, schedules, etc.), generate the widget with realistic/sample data that matches the request
- Make the widget functional and complete

IMPORTANT: 
- Return COMPLETE, FUNCTIONAL HTML code with ALL content elements (divs, spans, text, etc.)
- Include the full HTML structure with styles AND the actual content
- Do not include any explanatory text, descriptions, or notes before or after the HTML
- The HTML must be complete and display actual content
- PRESERVE THE STYLES AS SPECIFIED IN THE USER REQUEST

Return the complete widget HTML code now:"""
            else:
                # Normal generation mode
                prompt = f"""Generate a complete, production-ready widget based on the following user request.

USER REQUEST:
{render_prompt}

REQUIREMENTS:
- The widget should be visually appealing and fulfill the user's request
- Use modern CSS (flexbox/grid, responsive design)
- Ensure the widget is self-contained (all styles inline or in a <style> tag)
- Make it responsive and accessible
- Use semantic HTML
- The widget should be ready to inject into a dashboard
- CRITICAL: All CSS must be scoped to the widget content only - use class names that won't conflict with dashboard styles
- Avoid global styles, body/html selectors, or styles that affect elements outside the widget
- Use inline styles or scoped <style> tags within the widget HTML
- If the request requires real data (like weather, schedules, etc.), generate the widget with realistic/sample data that matches the request
- Make the widget functional and complete

IMPORTANT: 
- Return COMPLETE, FUNCTIONAL HTML code with ALL content elements (divs, spans, text, etc.)
- Include the full HTML structure with styles AND the actual content
- Do not include any explanatory text, descriptions, or notes before or after the HTML
- The HTML must be complete and display actual content

Return the complete widget HTML code now:"""
        else:
            # App prompt - with provided data
            # Check if the prompt contains style preservation instructions
            has_style_preservation = "CRITICAL STYLE PRESERVATION" in render_prompt or "CURRENT WIDGET STYLES" in render_prompt
            
            if has_style_preservation:
                # Style preservation mode - emphasize keeping existing styles
                prompt = f"""Generate a complete, production-ready widget based on the following data and rendering instructions.

DATA TO RENDER:
{json.dumps(data, indent=2)}

RENDERING INSTRUCTIONS:
{render_prompt}

CRITICAL INSTRUCTIONS:
- Follow the style preservation requirements EXACTLY as specified above
- If CSS styles are provided in the rendering instructions, USE THEM EXACTLY or create very similar styles
- Preserve colors, fonts, spacing, layout, and all visual properties
- Only update the content/data, NOT the styling
- Keep the same visual appearance and design aesthetic

REQUIREMENTS:
- The widget should be visually appealing and match the rendering instructions
- Use modern CSS (flexbox/grid, responsive design)
- Ensure the widget is self-contained (all styles inline or in a <style> tag)
- Make it responsive and accessible
- Use semantic HTML
- The widget should be ready to inject into a dashboard grid
- CRITICAL: All CSS must be scoped to the widget content only - use class names that won't conflict with dashboard styles
- Avoid global styles, body/html selectors, or styles that affect elements outside the widget
- Use inline styles or scoped <style> tags within the widget HTML

IMPORTANT: 
- Return COMPLETE, FUNCTIONAL HTML code with ALL content elements (divs, spans, text, etc.)
- Include the full HTML structure with styles AND the actual content displaying the data
- Do not include any explanatory text, descriptions, or notes before or after the HTML
- The HTML must display the actual data values, not just styles
- PRESERVE THE STYLES AS SPECIFIED IN THE RENDERING INSTRUCTIONS

Return the complete widget HTML code now:"""
            else:
                # Normal generation mode
                prompt = f"""Generate a complete, production-ready widget based on the following data and rendering instructions.

DATA TO RENDER:
{json.dumps(data, indent=2)}

RENDERING INSTRUCTIONS:
{render_prompt}

REQUIREMENTS:
- The widget should be visually appealing and match the rendering instructions
- Use modern CSS (flexbox/grid, responsive design)
- Ensure the widget is self-contained (all styles inline or in a <style> tag)
- Make it responsive and accessible
- Use semantic HTML
- The widget should be ready to inject into a dashboard grid
- CRITICAL: All CSS must be scoped to the widget content only - use class names that won't conflict with dashboard styles
- Avoid global styles, body/html selectors, or styles that affect elements outside the widget
- Use inline styles or scoped <style> tags within the widget HTML

IMPORTANT: 
- Return COMPLETE, FUNCTIONAL HTML code with ALL content elements (divs, spans, text, etc.)
- Include the full HTML structure with styles AND the actual content displaying the data
- Do not include any explanatory text, descriptions, or notes before or after the HTML
- The HTML must display the actual data values, not just styles

Return the complete widget HTML code now:"""

        # Run the blocking Anthropic API call in a thread pool to avoid blocking the event loop
        def call_anthropic_api():
            client = Anthropic(api_key=ANTHROPIC_API_KEY)
            
            # Call Claude API - try multiple models in order of preference
            # Note: Haiku models are faster and cheaper, good quality for widgets
            models_to_try = [
                "claude-3-5-haiku-20241022",    # Claude 3.5 Haiku (fast, good quality, available)
                "claude-3-haiku-20240307",      # Claude 3 Haiku (fallback)
                "claude-3-5-sonnet-20240620",   # Claude 3.5 Sonnet (best quality, if available)
                "claude-3-sonnet-20240229",     # Claude 3 Sonnet (alternative)
            ]
            
            message = None
            last_error = None
            
            for model_name in models_to_try:
                try:
                    message = client.messages.create(
                        model=model_name,
                        max_tokens=8192,  # Increased to ensure complete HTML generation
                        messages=[
                            {"role": "user", "content": prompt}
                        ]
                    )
                    # Success! Break out of loop
                    break
                except Exception as e:
                    last_error = e
                    # If it's a 404/not_found error, try next model
                    if "404" in str(e) or "not_found" in str(e) or "not_found_error" in str(e):
                        continue
                    else:
                        # For other errors, re-raise immediately
                        raise
            
            # If we tried all models and none worked
            if message is None:
                raise Exception(f"None of the available models worked. Last error: {last_error}")
            
            return message.content[0].text
        
        # Execute the blocking call in a thread pool executor
        loop = asyncio.get_event_loop()
        response_text = await loop.run_in_executor(_executor, call_anthropic_api)
        
        # Debug: Log response length (can be removed later)
        # print(f"AI Response length: {len(response_text)}")
        # print(f"AI Response preview: {response_text[:500]}")
        
        # Parse HTML from response - try multiple extraction methods
        
        def clean_html(html):
            """Clean HTML by removing DOCTYPE, html, head, body tags if present, but keep all content."""
            # Remove DOCTYPE
            html = re.sub(r'<!DOCTYPE[^>]*>', '', html, flags=re.IGNORECASE)
            # Remove <html> tags but keep content
            html = re.sub(r'<html[^>]*>', '', html, flags=re.IGNORECASE)
            html = re.sub(r'</html>', '', html, flags=re.IGNORECASE)
            # Extract content from <head> but keep <style> tags (move them out)
            # First, extract style tags from head
            head_style_match = re.search(r'<head[^>]*>(.*?)</head>', html, flags=re.IGNORECASE | re.DOTALL)
            if head_style_match:
                head_content = head_style_match.group(1)
                # Extract style tags
                style_tags = re.findall(r'<style[^>]*>.*?</style>', head_content, flags=re.IGNORECASE | re.DOTALL)
                # Remove head section
                html = re.sub(r'<head[^>]*>.*?</head>', '', html, flags=re.IGNORECASE | re.DOTALL)
                # Add style tags back at the beginning if they exist
                if style_tags:
                    html = '\n'.join(style_tags) + '\n' + html
            # Remove <body> tags but keep content
            html = re.sub(r'<body[^>]*>', '', html, flags=re.IGNORECASE)
            html = re.sub(r'</body>', '', html, flags=re.IGNORECASE)
            # Remove meta tags (we don't need them in widgets)
            html = re.sub(r'<meta[^>]*>', '', html, flags=re.IGNORECASE)
            html = re.sub(r'<title[^>]*>.*?</title>', '', html, flags=re.IGNORECASE | re.DOTALL)
            return html.strip()
        
        # Method 1: Extract from markdown code blocks (```html ... ```)
        markdown_match = re.search(r'```html\s*(.*?)\s*```', response_text, re.DOTALL | re.IGNORECASE)
        if markdown_match:
            widget_html = markdown_match.group(1).strip()
            # Remove any remaining explanatory text at the end (but be less aggressive)
            # Only split if there's a clear break (double newline or "Here's", etc.)
            split_match = re.search(r'\n\n\s*(?:Here\'s|This widget|The widget|The design|This|These)', widget_html, re.IGNORECASE)
            if split_match:
                widget_html = widget_html[:split_match.start()].strip()
            return clean_html(widget_html)
        
        # Method 2: Extract content between <html> tags
        html_match = re.search(r'<html[^>]*>(.*?)</html>', response_text, re.DOTALL | re.IGNORECASE)
        if html_match:
            widget_html = html_match.group(1).strip()
            # Remove any explanatory text
            widget_html = re.split(r'(?:Here\'s|This widget|The widget|The design)', widget_html, flags=re.IGNORECASE)[0].strip()
            return clean_html(widget_html)
        
        # Method 3: Extract from any code block (``` ... ```)
        code_block_match = re.search(r'```[a-z]*\s*(.*?)\s*```', response_text, re.DOTALL)
        if code_block_match:
            widget_html = code_block_match.group(1).strip()
            # Remove explanatory text
            widget_html = re.split(r'(?:Here\'s|This widget|The widget|The design)', widget_html, flags=re.IGNORECASE)[0].strip()
            # Check if it looks like HTML
            if '<' in widget_html and ('div' in widget_html.lower() or 'style' in widget_html.lower()):
                return clean_html(widget_html)
        
        # Method 4: Try to find HTML content in the response
        # Look for HTML tags and extract everything between first < and last >
        html_content_match = re.search(r'(<[^>]+>.*?</[^>]+>)', response_text, re.DOTALL)
        if html_content_match:
            widget_html = html_content_match.group(1).strip()
            # Remove any trailing explanatory text
            lines = widget_html.split('\n')
            # Find the last line that looks like HTML (contains tags)
            last_html_line = 0
            for i, line in enumerate(lines):
                if '<' in line and '>' in line and not line.strip().startswith('-'):
                    last_html_line = i
            
            widget_html = '\n'.join(lines[:last_html_line + 1]).strip()
            return widget_html
        
        # Method 5: If response looks like HTML (starts with <), extract it
        if response_text.strip().startswith('<'):
            # Find where HTML ends (before explanatory text)
            # Look for common patterns that indicate end of HTML
            html_end_patterns = [
                r'(?:Here\'s|This widget|The widget|The design|This|These)',
                r'\n\n(?:This|These|The|Here)',
            ]
            
            widget_html = response_text.strip()
            for pattern in html_end_patterns:
                match = re.search(pattern, widget_html, re.IGNORECASE | re.MULTILINE)
                if match:
                    widget_html = widget_html[:match.start()].strip()
                    break
            
            # Ensure it ends with a closing tag
            if widget_html and widget_html.rstrip().endswith('>'):
                return clean_html(widget_html)
        
        # Fallback: Return as-is if it contains HTML-like content
        if '<' in response_text and '>' in response_text:
            # Try to extract just the HTML portion
            # Remove lines that look like explanations (don't contain HTML tags)
            lines = response_text.split('\n')
            html_lines = []
            in_html = False
            for line in lines:
                if '<' in line:
                    in_html = True
                    html_lines.append(line)
                elif in_html:
                    if '>' in line or line.strip().startswith('<!--') or not line.strip():
                        html_lines.append(line)
                    else:
                        # Probably hit explanatory text, but continue if it looks like HTML
                        if any(tag in line.lower() for tag in ['<div', '</div', '<style', '</style', '<span', '<p', '<h']):
                            html_lines.append(line)
                        else:
                            break
            
            if html_lines:
                return clean_html('\n'.join(html_lines).strip())
        
        # Last resort: wrap in a div
        return f"""
        <div style="padding: 20px; font-family: system-ui;">
            {response_text}
        </div>
        """
    
    except Exception as e:
        # Return error widget
        return f"""
        <div class="widget-error" style="padding: 20px; color: #d32f2f; background: #ffebee; border-radius: 8px;">
            <h3>⚠️ Generation Error</h3>
            <p>Failed to generate widget: {str(e)}</p>
            <p>Please check your API key and network connection.</p>
        </div>
        """

