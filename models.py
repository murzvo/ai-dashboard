from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel


class RegisterRequest(BaseModel):
    registration_token: str
    app_name: str


class RegisterResponse(BaseModel):
    integration_token: str
    app_id: str


class ShareDataRequest(BaseModel):
    integration_token: str
    data: Dict[str, Any]
    render_prompt: str


class ShareDataResponse(BaseModel):
    success: bool
    message: str


class CreateUserWidgetRequest(BaseModel):
    prompt: str
    widget_name: Optional[str] = "User Widget"


class CreateUserWidgetResponse(BaseModel):
    success: bool
    widget_id: str
    message: str


class EditUserWidgetRequest(BaseModel):
    widget_id: str
    prompt: str


class EditUserWidgetResponse(BaseModel):
    success: bool
    message: str


class DeleteUserWidgetRequest(BaseModel):
    widget_id: str


class DeleteUserWidgetResponse(BaseModel):
    success: bool
    message: str


class RefreshAppWidgetResponse(BaseModel):
    success: bool
    html: str
    message: str


class DeleteAppWidgetResponse(BaseModel):
    success: bool
    message: str

