from __future__ import annotations

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.errors import ApiError
from app.models.comment import Comment


def _task_exists(db: Session, task_id: int) -> bool:
    return db.execute(text("SELECT 1 FROM tasks WHERE id = :id"), {"id": task_id}).first() is not None


def _author_exists(db: Session, author_id: int) -> bool:
    return db.execute(text("SELECT 1 FROM users WHERE id = :id"), {"id": author_id}).first() is not None


def create_comment(db: Session, task_id: int, body: str, author_id: int) -> Comment:
    if not _task_exists(db, task_id):
        raise ApiError(404, "TASK_NOT_FOUND", f"Task {task_id} not found")
    if not _author_exists(db, author_id):
        raise ApiError(404, "AUTHOR_NOT_FOUND", f"User {author_id} not found")
    comment = Comment(task_id=task_id, author_id=author_id, body=body)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def list_comments(db: Session, task_id: int) -> list[Comment]:
    if not _task_exists(db, task_id):
        raise ApiError(404, "TASK_NOT_FOUND", f"Task {task_id} not found")
    stmt = select(Comment).where(Comment.task_id == task_id).order_by(Comment.created_at, Comment.id)
    return list(db.scalars(stmt))


def delete_comment(db: Session, comment_id: int) -> None:
    comment = db.get(Comment, comment_id)
    if comment is None:
        raise ApiError(404, "COMMENT_NOT_FOUND", f"Comment {comment_id} not found")
    db.delete(comment)
    db.commit()
