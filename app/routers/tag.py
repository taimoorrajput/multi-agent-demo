from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.tag import TagCreate, TagRead
from app.services import tag as tag_service

router = APIRouter(prefix="/tasks/{task_id}/tags", tags=["tags"])


@router.post("", response_model=TagRead, status_code=status.HTTP_201_CREATED)
def attach_tag(task_id: int, payload: TagCreate, db: Session = Depends(get_db)) -> TagRead:  # noqa: B008
    tag = tag_service.attach_tag(db, task_id, payload.name)
    return TagRead.model_validate(tag)


@router.get("", response_model=list[TagRead])
def list_tags(task_id: int, db: Session = Depends(get_db)) -> list[TagRead]:  # noqa: B008
    tags = tag_service.list_tags(db, task_id)
    return [TagRead.model_validate(tag) for tag in tags]


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def detach_tag(task_id: int, tag_id: int, db: Session = Depends(get_db)) -> None:  # noqa: B008
    tag_service.detach_tag(db, task_id, tag_id)
