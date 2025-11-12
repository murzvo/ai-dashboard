from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from jinja2 import Environment, FileSystemLoader
import secrets
import logging
from datetime import datetime
from typing import Annotated

from models import (
    RegisterRequest, RegisterResponse, ShareDataRequest, ShareDataResponse,
    CreateUserWidgetRequest, CreateUserWidgetResponse,
    EditUserWidgetRequest, EditUserWidgetResponse,
    DeleteUserWidgetRequest, DeleteUserWidgetResponse,
    RefreshAppWidgetResponse, DeleteAppWidgetResponse
)
from database import apps_collection, widgets_collection
from config import settings
from ai_generator import generate_widget_html
from dependencies import (
    verify_registration_token,
    verify_integration_token,
    get_widget_by_id,
    get_app_widget_by_app_id
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app with metadata
app = FastAPI(
    title="AI Dashboard",
    description="AI-powered dashboard for aggregating 3rd party app widgets",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware (best practice for APIs)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Jinja2 templates
templates = Environment(loader=FileSystemLoader("templates"))


# Health check endpoint (best practice)
@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint for monitoring.
    Returns 200 if the service is healthy.
    """
    try:
        # Quick database connectivity check
        import asyncio
        loop = asyncio.get_event_loop()
        def ping_db():
            from database import client
            client.admin.command('ping')
        
        await loop.run_in_executor(None, ping_db)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "healthy",
                "environment": settings.environment,
                "database": "connected"
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


@app.post("/register", response_model=RegisterResponse, tags=["apps"])
async def register_app(
    request: Annotated[RegisterRequest, Depends(verify_registration_token)]
):
    """
    Register a new 3rd party app.
    Requires registration token.
    Returns integration token.
    """
    import asyncio
    loop = asyncio.get_event_loop()
    
    # Token verification handled by dependency
    
    # Generate integration token
    integration_token = secrets.token_urlsafe(32)
    
    # Save app to database (run in executor to avoid blocking)
    def save_app():
        app_doc = {
            "app_name": request.app_name,
            "integration_token": integration_token,
            "registration_date": datetime.utcnow(),
            "created_at": datetime.utcnow()
        }
        result = apps_collection.insert_one(app_doc)
        return str(result.inserted_id)
    
    app_id = await loop.run_in_executor(None, save_app)
    
    return RegisterResponse(
        integration_token=integration_token,
        app_id=app_id
    )


@app.post("/share-data", response_model=ShareDataResponse, tags=["apps"])
async def share_data(
    request: ShareDataRequest,
    app: Annotated[dict, Depends(verify_integration_token)]
):
    """
    Share data and render prompt from 3rd party app.
    Triggers AI generation and caches the result.
    """
    import asyncio
    loop = asyncio.get_event_loop()
    
    # App verification handled by dependency
    app_id = str(app["_id"])
    
    logger.info(f"Sharing data for app: {app.get('app_name', 'Unknown')}")
    
    # Generate widget HTML using AI (now non-blocking)
    widget_html = await generate_widget_html(request.data, request.render_prompt)
    
    # Save/update widget in database (run in executor to avoid blocking)
    def save_widget():
        widget_doc = {
            "app_id": app_id,
            "data": request.data,
            "render_prompt": request.render_prompt,
            "generated_html": widget_html,
            "updated_at": datetime.utcnow()
        }
        widgets_collection.update_one(
            {"app_id": app_id},
            {"$set": widget_doc},
            upsert=True
        )
    
    await loop.run_in_executor(None, save_widget)
    
    return ShareDataResponse(
        success=True,
        message="Data shared and widget generated successfully"
    )


@app.get("/", response_class=HTMLResponse, tags=["dashboard"])
async def dashboard():
    """
    Main dashboard page - renders all widgets in flexbox layout.
    User widgets appear first (newest first), then app widgets.
    """
    import asyncio
    loop = asyncio.get_event_loop()
    
    def get_widgets_data():
        widgets_data = []
        
        try:
            # Get user-created widgets (newest first)
            # Use max_time_ms to limit query time
            user_widgets = list(widgets_collection.find({"user_created": True}).sort("created_at", -1).max_time_ms(2000))
            for widget in user_widgets:
                widgets_data.append({
                    "widget_id": str(widget["_id"]),
                    "app_id": None,  # No app ID for user widgets
                    "app_name": widget.get("widget_name", "User Widget"),
                    "is_user_created": True,
                    "prompt": widget.get("render_prompt", ""),
                    "html": widget.get("generated_html", "<div>No data yet</div>")
                })
        except Exception as e:
            print(f"Error fetching user widgets: {e}")
            # Continue with empty list if error
        
        try:
            # Get app-registered widgets (sorted by registration date)
            # Use max_time_ms to limit query time
            apps = list(apps_collection.find().sort("registration_date", 1).max_time_ms(2000))
            for app in apps:
                app_id = str(app["_id"])
                widget = widgets_collection.find_one({"app_id": app_id, "user_created": {"$ne": True}}, max_time_ms=2000)
                
                widgets_data.append({
                    "widget_id": None,
                    "app_id": app_id,
                    "app_name": app.get("app_name", "Unknown"),
                    "is_user_created": False,
                    "html": widget.get("generated_html", "<div>No data yet</div>") if widget else "<div>No data yet</div>"
                })
        except Exception as e:
            print(f"Error fetching app widgets: {e}")
            # Continue with existing widgets if error
        
        return widgets_data
    
    try:
        widgets_data = await loop.run_in_executor(None, get_widgets_data)
    except Exception as e:
        # If database connection fails, show error page
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Database Connection Error</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 40px; background: #f5f5f5; }}
                .error-box {{ background: white; padding: 30px; border-radius: 8px; max-width: 600px; margin: 0 auto; }}
                h1 {{ color: #d32f2f; }}
                code {{ background: #f5f5f5; padding: 2px 6px; border-radius: 4px; }}
            </style>
        </head>
        <body>
            <div class="error-box">
                <h1>⚠️ Database Connection Error</h1>
                <p>Unable to connect to MongoDB Atlas. Please check:</p>
                <ol>
                    <li><strong>Network Access:</strong> Go to MongoDB Atlas → Network Access → Add IP Address → Allow access from anywhere (0.0.0.0/0)</li>
                    <li><strong>Connection String:</strong> Verify MONGODB_URI is set correctly in Heroku config</li>
                    <li><strong>Database User:</strong> Ensure the database user has proper permissions</li>
                </ol>
                <p><strong>Error:</strong> <code>{str(e)[:200]}</code></p>
                <p>Check Heroku logs for more details: <code>heroku logs --tail</code></p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=error_html, status_code=503)
    
    # Render template (fast operation, can stay in async context)
    template = templates.get_template("dashboard.html")
    html_content = template.render(
        widgets=widgets_data,
        refresh_interval=settings.widget_refresh_interval
    )
    return HTMLResponse(content=html_content)


@app.get("/widget/{app_id}/refresh")
async def refresh_widget(app_id: str):
    """
    Refresh a specific widget (returns cached HTML, no AI regeneration).
    """
    widget = widgets_collection.find_one({"app_id": app_id})
    
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")
    
    return {"html": widget.get("generated_html", "<div>No data yet</div>")}


@app.post("/api/user-widgets/create", response_model=CreateUserWidgetResponse)
async def create_user_widget(request: CreateUserWidgetRequest):
    """
    Create a user widget from a prompt (no data provided).
    """
    import asyncio
    
    loop = asyncio.get_event_loop()
    
    try:
        # Generate widget HTML using AI (prompt only, no data)
        widget_html = await generate_widget_html({}, request.prompt, is_user_prompt=True)
    except Exception as e:
        print(f"Error generating widget HTML: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate widget: {str(e)}"
        )
    
    # Save user widget to database
    def save_user_widget():
        try:
            widget_doc = {
                "app_id": None,  # No app ID for user widgets
                "user_created": True,
                "widget_name": request.widget_name or "User Widget",
                "data": {},  # No data for user widgets
                "render_prompt": request.prompt,
                "generated_html": widget_html,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            result = widgets_collection.insert_one(widget_doc)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error saving widget to database: {e}")
            raise
    
    try:
        widget_id = await loop.run_in_executor(None, save_user_widget)
    except Exception as e:
        error_msg = str(e)
        if "SSL handshake" in error_msg or "ServerSelectionTimeout" in error_msg:
            raise HTTPException(
                status_code=503,
                detail="Database connection failed. Please check MongoDB Atlas Network Access settings and ensure IP 0.0.0.0/0 is whitelisted."
            )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save widget: {error_msg}"
        )
    
    return CreateUserWidgetResponse(
        success=True,
        widget_id=widget_id,
        message="User widget created successfully"
    )


@app.post("/api/user-widgets/edit", response_model=EditUserWidgetResponse)
async def edit_user_widget(request: EditUserWidgetRequest):
    """
    Edit a user widget's prompt and regenerate it.
    """
    import asyncio
    
    loop = asyncio.get_event_loop()
    
    # Find widget
    def find_widget():
        try:
            from bson import ObjectId
            return widgets_collection.find_one({"_id": ObjectId(request.widget_id), "user_created": True})
        except Exception as e:
            print(f"Error finding widget: {e}")
            raise
    
    try:
        widget = await loop.run_in_executor(None, find_widget)
    except Exception as e:
        error_msg = str(e)
        if "SSL handshake" in error_msg or "ServerSelectionTimeout" in error_msg:
            raise HTTPException(
                status_code=503,
                detail="Database connection failed. Please check MongoDB Atlas Network Access settings."
            )
        raise HTTPException(status_code=500, detail=f"Database error: {error_msg}")
    
    if not widget:
        raise HTTPException(status_code=404, detail="User widget not found")
    
    try:
        # Regenerate widget HTML with new prompt
        widget_html = await generate_widget_html({}, request.prompt, is_user_prompt=True)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate widget: {str(e)}"
        )
    
    # Update widget
    def update_widget():
        try:
            from bson import ObjectId
            widgets_collection.update_one(
                {"_id": ObjectId(request.widget_id)},
                {
                    "$set": {
                        "render_prompt": request.prompt,
                        "generated_html": widget_html,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
        except Exception as e:
            print(f"Error updating widget: {e}")
            raise
    
    try:
        await loop.run_in_executor(None, update_widget)
    except Exception as e:
        error_msg = str(e)
        if "SSL handshake" in error_msg or "ServerSelectionTimeout" in error_msg:
            raise HTTPException(
                status_code=503,
                detail="Database connection failed. Please check MongoDB Atlas Network Access settings."
            )
        raise HTTPException(status_code=500, detail=f"Failed to update widget: {error_msg}")
    
    return EditUserWidgetResponse(
        success=True,
        message="User widget updated successfully"
    )


@app.post("/api/user-widgets/delete", response_model=DeleteUserWidgetResponse)
async def delete_user_widget(request: DeleteUserWidgetRequest):
    """
    Delete a user widget.
    """
    import asyncio
    
    loop = asyncio.get_event_loop()
    
    def delete_widget():
        try:
            from bson import ObjectId
            result = widgets_collection.delete_one({"_id": ObjectId(request.widget_id), "user_created": True})
            return result.deleted_count
        except Exception as e:
            print(f"Error deleting widget: {e}")
            raise
    
    try:
        deleted_count = await loop.run_in_executor(None, delete_widget)
    except Exception as e:
        error_msg = str(e)
        if "SSL handshake" in error_msg or "ServerSelectionTimeout" in error_msg:
            raise HTTPException(
                status_code=503,
                detail="Database connection failed. Please check MongoDB Atlas Network Access settings."
            )
        raise HTTPException(status_code=500, detail=f"Database error: {error_msg}")
    
    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="User widget not found")
    
    return DeleteUserWidgetResponse(
        success=True,
        message="User widget deleted successfully"
    )


@app.post("/api/user-widgets/{widget_id}/refresh")
async def refresh_user_widget(widget_id: str):
    """
    Refresh a user widget - re-generate with same prompt but keep similar styles.
    Extracts styles from current HTML and tells AI to reuse them.
    """
    import asyncio
    import re
    
    loop = asyncio.get_event_loop()
    
    def find_widget():
        try:
            from bson import ObjectId
            return widgets_collection.find_one({"_id": ObjectId(widget_id), "user_created": True})
        except Exception as e:
            print(f"Error finding widget: {e}")
            raise
    
    try:
        widget = await loop.run_in_executor(None, find_widget)
    except Exception as e:
        error_msg = str(e)
        if "SSL handshake" in error_msg or "ServerSelectionTimeout" in error_msg:
            raise HTTPException(
                status_code=503,
                detail="Database connection failed. Please check MongoDB Atlas Network Access settings."
            )
        raise HTTPException(status_code=500, detail=f"Database error: {error_msg}")
    
    if not widget:
        raise HTTPException(status_code=404, detail="User widget not found")
    
    # Extract styles from current HTML
    current_html = widget.get("generated_html", "")
    style_tags = re.findall(r'<style[^>]*>(.*?)</style>', current_html, re.DOTALL | re.IGNORECASE)
    
    # Build prompt that strongly emphasizes preserving styles
    original_prompt = widget.get("render_prompt", "")
    
    style_instruction = "\n\nCRITICAL STYLE PRESERVATION REQUIREMENTS:\n"
    style_instruction += "You MUST preserve the EXACT visual appearance and styling of the current widget.\n"
    style_instruction += "- Keep the SAME colors, fonts, spacing, borders, shadows, and all visual properties\n"
    style_instruction += "- Use the SAME CSS classes and styling patterns\n"
    style_instruction += "- Maintain the SAME layout structure and component arrangement\n"
    style_instruction += "- Preserve the SAME design aesthetic and visual hierarchy\n"
    style_instruction += "- DO NOT change colors, sizes, or styling unless absolutely necessary\n"
    
    if style_tags:
        style_instruction += f"\nCURRENT WIDGET STYLES (preserve these):\n"
        style_instruction += "```css\n"
        for style_content in style_tags:
            style_instruction += style_content.strip() + "\n"
        style_instruction += "```\n"
        style_instruction += "\nIMPORTANT: Use these exact styles or very similar ones. Match the color scheme, typography, spacing, and visual design.\n"
    
    enhanced_prompt = f"{original_prompt}{style_instruction}"
    
    try:
        # Regenerate with enhanced prompt (keeps styles)
        widget_html = await generate_widget_html({}, enhanced_prompt, is_user_prompt=True)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate widget: {str(e)}"
        )
    
    def update_widget():
        try:
            from bson import ObjectId
            widgets_collection.update_one(
                {"_id": ObjectId(widget_id)},
                {
                    "$set": {
                        "generated_html": widget_html,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
        except Exception as e:
            print(f"Error updating widget: {e}")
            raise
    
    try:
        await loop.run_in_executor(None, update_widget)
    except Exception as e:
        error_msg = str(e)
        if "SSL handshake" in error_msg or "ServerSelectionTimeout" in error_msg:
            raise HTTPException(
                status_code=503,
                detail="Database connection failed. Please check MongoDB Atlas Network Access settings."
            )
        raise HTTPException(status_code=500, detail=f"Failed to update widget: {error_msg}")
    
    return {"html": widget_html}


@app.post("/api/user-widgets/{widget_id}/full-refresh")
async def full_refresh_user_widget(widget_id: str):
    """
    Full refresh a user widget - re-generate with original prompt (new design).
    """
    import asyncio
    
    loop = asyncio.get_event_loop()
    
    def find_widget():
        try:
            from bson import ObjectId
            return widgets_collection.find_one({"_id": ObjectId(widget_id), "user_created": True})
        except Exception as e:
            print(f"Error finding widget: {e}")
            raise
    
    try:
        widget = await loop.run_in_executor(None, find_widget)
    except Exception as e:
        error_msg = str(e)
        if "SSL handshake" in error_msg or "ServerSelectionTimeout" in error_msg:
            raise HTTPException(
                status_code=503,
                detail="Database connection failed. Please check MongoDB Atlas Network Access settings."
            )
        raise HTTPException(status_code=500, detail=f"Database error: {error_msg}")
    
    if not widget:
        raise HTTPException(status_code=404, detail="User widget not found")
    
    try:
        # Regenerate with original prompt (full refresh)
        widget_html = await generate_widget_html({}, widget.get("render_prompt", ""), is_user_prompt=True)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate widget: {str(e)}"
        )
    
    def update_widget():
        try:
            from bson import ObjectId
            widgets_collection.update_one(
                {"_id": ObjectId(widget_id)},
                {
                    "$set": {
                        "generated_html": widget_html,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
        except Exception as e:
            print(f"Error updating widget: {e}")
            raise
    
    try:
        await loop.run_in_executor(None, update_widget)
    except Exception as e:
        error_msg = str(e)
        if "SSL handshake" in error_msg or "ServerSelectionTimeout" in error_msg:
            raise HTTPException(
                status_code=503,
                detail="Database connection failed. Please check MongoDB Atlas Network Access settings."
            )
        raise HTTPException(status_code=500, detail=f"Failed to update widget: {error_msg}")
    
    return {"html": widget_html}


@app.post("/api/app-widgets/{app_id}/refresh", response_model=RefreshAppWidgetResponse)
async def refresh_app_widget(app_id: str):
    """
    Refresh an app widget - re-generate with same data but keep similar styles.
    Extracts styles from current HTML and tells AI to reuse them.
    """
    import asyncio
    import re
    
    loop = asyncio.get_event_loop()
    
    def find_widget():
        try:
            from bson import ObjectId
            return widgets_collection.find_one({"app_id": app_id, "user_created": {"$ne": True}})
        except Exception as e:
            print(f"Error finding widget: {e}")
            raise
    
    try:
        widget = await loop.run_in_executor(None, find_widget)
    except Exception as e:
        error_msg = str(e)
        if "SSL handshake" in error_msg or "ServerSelectionTimeout" in error_msg:
            raise HTTPException(
                status_code=503,
                detail="Database connection failed. Please check MongoDB Atlas Network Access settings."
            )
        raise HTTPException(status_code=500, detail=f"Database error: {error_msg}")
    
    if not widget:
        raise HTTPException(status_code=404, detail="App widget not found")
    
    # Extract styles from current HTML
    current_html = widget.get("generated_html", "")
    style_tags = re.findall(r'<style[^>]*>(.*?)</style>', current_html, re.DOTALL | re.IGNORECASE)
    
    # Build prompt that strongly emphasizes preserving styles
    data = widget.get("data", {})
    original_prompt = widget.get("render_prompt", "")
    
    style_instruction = "\n\nCRITICAL STYLE PRESERVATION REQUIREMENTS:\n"
    style_instruction += "You MUST preserve the EXACT visual appearance and styling of the current widget.\n"
    style_instruction += "- Keep the SAME colors, fonts, spacing, borders, shadows, and all visual properties\n"
    style_instruction += "- Use the SAME CSS classes and styling patterns\n"
    style_instruction += "- Maintain the SAME layout structure and component arrangement\n"
    style_instruction += "- Preserve the SAME design aesthetic and visual hierarchy\n"
    style_instruction += "- DO NOT change colors, sizes, or styling unless absolutely necessary\n"
    
    if style_tags:
        style_instruction += f"\nCURRENT WIDGET STYLES (preserve these):\n"
        style_instruction += "```css\n"
        for style_content in style_tags:
            style_instruction += style_content.strip() + "\n"
        style_instruction += "```\n"
        style_instruction += "\nIMPORTANT: Use these exact styles or very similar ones. Match the color scheme, typography, spacing, and visual design.\n"
    
    enhanced_prompt = f"{original_prompt}{style_instruction}"
    
    try:
        # Regenerate with same data but enhanced prompt
        widget_html = await generate_widget_html(data, enhanced_prompt, is_user_prompt=False)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate widget: {str(e)}"
        )
    
    def update_widget():
        try:
            widgets_collection.update_one(
                {"app_id": app_id},
                {
                    "$set": {
                        "generated_html": widget_html,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
        except Exception as e:
            print(f"Error updating widget: {e}")
            raise
    
    try:
        await loop.run_in_executor(None, update_widget)
    except Exception as e:
        error_msg = str(e)
        if "SSL handshake" in error_msg or "ServerSelectionTimeout" in error_msg:
            raise HTTPException(
                status_code=503,
                detail="Database connection failed. Please check MongoDB Atlas Network Access settings."
            )
        raise HTTPException(status_code=500, detail=f"Failed to update widget: {error_msg}")
    
    return RefreshAppWidgetResponse(
        success=True,
        html=widget_html,
        message="Widget refreshed successfully"
    )


@app.post("/api/app-widgets/{app_id}/full-refresh", response_model=RefreshAppWidgetResponse)
async def full_refresh_app_widget(app_id: str):
    """
    Full refresh an app widget - re-generate with original prompt and data.
    This creates a completely new widget design.
    """
    import asyncio
    
    loop = asyncio.get_event_loop()
    
    def find_widget():
        try:
            from bson import ObjectId
            return widgets_collection.find_one({"app_id": app_id, "user_created": {"$ne": True}})
        except Exception as e:
            print(f"Error finding widget: {e}")
            raise
    
    try:
        widget = await loop.run_in_executor(None, find_widget)
    except Exception as e:
        error_msg = str(e)
        if "SSL handshake" in error_msg or "ServerSelectionTimeout" in error_msg:
            raise HTTPException(
                status_code=503,
                detail="Database connection failed. Please check MongoDB Atlas Network Access settings."
            )
        raise HTTPException(status_code=500, detail=f"Database error: {error_msg}")
    
    if not widget:
        raise HTTPException(status_code=404, detail="App widget not found")
    
    # Regenerate with original prompt and data
    data = widget.get("data", {})
    original_prompt = widget.get("render_prompt", "")
    
    try:
        widget_html = await generate_widget_html(data, original_prompt, is_user_prompt=False)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate widget: {str(e)}"
        )
    
    def update_widget():
        try:
            widgets_collection.update_one(
                {"app_id": app_id},
                {
                    "$set": {
                        "generated_html": widget_html,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
        except Exception as e:
            print(f"Error updating widget: {e}")
            raise
    
    try:
        await loop.run_in_executor(None, update_widget)
    except Exception as e:
        error_msg = str(e)
        if "SSL handshake" in error_msg or "ServerSelectionTimeout" in error_msg:
            raise HTTPException(
                status_code=503,
                detail="Database connection failed. Please check MongoDB Atlas Network Access settings."
            )
        raise HTTPException(status_code=500, detail=f"Failed to update widget: {error_msg}")
    
    return RefreshAppWidgetResponse(
        success=True,
        html=widget_html,
        message="Widget fully refreshed successfully"
    )


@app.delete("/api/app-widgets/{app_id}", response_model=DeleteAppWidgetResponse)
async def delete_app_widget(app_id: str):
    """
    Delete an app widget and unregister the app.
    This removes both the widget and the app registration.
    """
    import asyncio
    
    loop = asyncio.get_event_loop()
    
    def delete_app_and_widget():
        try:
            from bson import ObjectId
            # Delete widget
            widget_result = widgets_collection.delete_one({"app_id": app_id})
            # Delete app
            app_result = apps_collection.delete_one({"_id": ObjectId(app_id)})
            
            if app_result.deleted_count == 0:
                return False, "App not found"
            
            return True, f"App and widget deleted successfully"
        except Exception as e:
            print(f"Error deleting app/widget: {e}")
            raise
    
    try:
        success, message = await loop.run_in_executor(None, delete_app_and_widget)
    except Exception as e:
        error_msg = str(e)
        if "SSL handshake" in error_msg or "ServerSelectionTimeout" in error_msg:
            raise HTTPException(
                status_code=503,
                detail="Database connection failed. Please check MongoDB Atlas Network Access settings."
            )
        raise HTTPException(status_code=500, detail=f"Database error: {error_msg}")
    
    if not success:
        raise HTTPException(status_code=404, detail=message)
    
    return DeleteAppWidgetResponse(
        success=True,
        message=message
    )

