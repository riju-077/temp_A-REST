from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query

from data import objects_db, get_next_id
from schemas import (
    ObjectCreate,
    ObjectUpdate,
    ObjectPatch,
    ObjectResponse,
    ObjectCreateResponse,
    ObjectUpdateResponse,
    DeleteResponse,
)

router = APIRouter(prefix="/objects", tags=["objects"])


@router.get("", response_model=list[ObjectResponse])
def get_all_objects():
    """Get list of all objects"""
    return objects_db


@router.get("/", response_model=list[ObjectResponse])
def get_objects_by_ids(id: list[str] = Query(...)):
    """Get list of objects by IDs"""
    result = [obj for obj in objects_db if obj["id"] in id]
    return result


@router.get("/{object_id}", response_model=ObjectResponse)
def get_single_object(object_id: str):
    """Get a single object by ID"""
    for obj in objects_db:
        if obj["id"] == object_id:
            return obj
    raise HTTPException(status_code=404, detail=f"Object with id = {object_id} not found")


@router.post("", response_model=ObjectCreateResponse)
def create_object(obj: ObjectCreate):
    """Create a new object"""
    new_id = get_next_id()
    created_at = datetime.now(timezone.utc)

    new_object = {
        "id": new_id,
        "name": obj.name,
        "data": obj.data,
        "createdAt": created_at,
    }
    objects_db.append(new_object)
    return new_object


@router.put("/{object_id}", response_model=ObjectUpdateResponse)
def update_object(object_id: str, obj: ObjectUpdate):
    """Update an object (full update)"""
    for i, existing_obj in enumerate(objects_db):
        if existing_obj["id"] == object_id:
            updated_at = datetime.now(timezone.utc)
            updated_object = {
                "id": object_id,
                "name": obj.name,
                "data": obj.data,
                "updatedAt": updated_at,
            }
            objects_db[i] = updated_object
            return updated_object
    raise HTTPException(status_code=404, detail=f"Object with id = {object_id} not found")


@router.patch("/{object_id}", response_model=ObjectUpdateResponse)
def partial_update_object(object_id: str, obj: ObjectPatch):
    """Partially update an object"""
    for i, existing_obj in enumerate(objects_db):
        if existing_obj["id"] == object_id:
            updated_at = datetime.now(timezone.utc)

            updated_object = {
                "id": object_id,
                "name": obj.name if obj.name is not None else existing_obj["name"],
                "data": obj.data if obj.data is not None else existing_obj.get("data"),
                "updatedAt": updated_at,
            }
            objects_db[i] = updated_object
            return updated_object
    raise HTTPException(status_code=404, detail=f"Object with id = {object_id} not found")


@router.delete("/{object_id}", response_model=DeleteResponse)
def delete_object(object_id: str):
    """Delete an object"""
    for i, obj in enumerate(objects_db):
        if obj["id"] == object_id:
            objects_db.pop(i)
            return {"message": f"Object with id = {object_id}, has been deleted."}
    raise HTTPException(status_code=404, detail=f"Object with id = {object_id} not found")
