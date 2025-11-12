"""
FastAPI dependencies for dependency injection (best practice).
"""

from fastapi import Depends, HTTPException, status
from typing import Annotated
from bson import ObjectId
from database import apps_collection, widgets_collection
from config import settings
from models import RegisterRequest, ShareDataRequest
import asyncio


def verify_registration_token(request: RegisterRequest) -> RegisterRequest:
    """
    Verify registration token from request.
    Used as a dependency for registration endpoints.
    Returns the request if token is valid.
    """
    if request.registration_token != settings.registration_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid registration token"
        )
    return request


async def verify_integration_token(request: ShareDataRequest) -> dict:
    """
    Verify integration token from request and return app document.
    Used as a dependency for app widget endpoints.
    """
    loop = asyncio.get_event_loop()
    
    def find_app():
        return apps_collection.find_one({"integration_token": request.integration_token})
    
    try:
        app = await loop.run_in_executor(None, find_app)
        if not app:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid integration token"
            )
        return app
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


async def get_widget_by_id(widget_id: str, user_created: bool = True) -> dict:
    """
    Get widget by ID.
    Used as a dependency for widget operations.
    """
    loop = asyncio.get_event_loop()
    
    def find_widget():
        try:
            query = {"_id": ObjectId(widget_id), "user_created": user_created}
            return widgets_collection.find_one(query)
        except Exception as e:
            print(f"Error finding widget: {e}")
            raise
    
    try:
        widget = await loop.run_in_executor(None, find_widget)
        if not widget:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Widget not found"
            )
        return widget
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


async def get_app_widget_by_app_id(app_id: str) -> dict:
    """
    Get app widget by app_id.
    Used as a dependency for app widget operations.
    """
    loop = asyncio.get_event_loop()
    
    def find_widget():
        try:
            return widgets_collection.find_one({
                "app_id": app_id,
                "user_created": {"$ne": True}
            })
        except Exception as e:
            print(f"Error finding widget: {e}")
            raise
    
    try:
        widget = await loop.run_in_executor(None, find_widget)
        if not widget:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="App widget not found"
            )
        return widget
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

