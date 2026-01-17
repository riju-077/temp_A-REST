from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ObjectBase(BaseModel):
    name: str
    data: dict[str, Any] | None = None


class ObjectCreate(ObjectBase):
    """Schema for creating a new object"""
    pass


class ObjectUpdate(ObjectBase):
    """Schema for full update (PUT) - all fields required"""
    pass


class ObjectPatch(BaseModel):
    """Schema for partial update (PATCH) - all fields optional"""
    name: str | None = None
    data: dict[str, Any] | None = None


class ObjectResponse(BaseModel):
    """Schema for object response"""
    id: str
    name: str
    data: dict[str, Any] | None = None


class ObjectCreateResponse(ObjectResponse):
    """Schema for created object response"""
    createdAt: datetime


class ObjectUpdateResponse(ObjectResponse):
    """Schema for updated object response"""
    updatedAt: datetime


class DeleteResponse(BaseModel):
    """Schema for delete response"""
    message: str
