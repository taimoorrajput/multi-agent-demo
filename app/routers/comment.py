from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.comment import CommentCreate, CommentRead
from app.services import comment as comment_service

router = APIRouter(tags=["comments"])


@router.post(
    "/tasks/{task_id}/comments",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_comment(
    task_id: int, payload: CommentCreate, db: Session = Depends(get_db)  # noqa: B008
) -> CommentRead:
    comment = comment_service.create_comment(db, task_id, payload.body, payload.author_id)
    return CommentRead.model_validate(comment)


@router.get("/tasks/{task_id}/comments", response_model=list[CommentRead])
def list_comments(task_id: int, db: Session = Depends(get_db)) -> list[CommentRead]:  # noqa: B008
    comments = comment_service.list_comments(db, task_id)
    return [CommentRead.model_validate(comment) for comment in comments]


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(comment_id: int, db: Session = Depends(get_db)) -> None:  # noqa: B008
    comment_service.delete_comment(db, comment_id)
