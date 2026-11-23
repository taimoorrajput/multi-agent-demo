from __future__ import annotations

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.errors import ApiError
from app.models.tag import Tag, task_tags


def _ensure_task_exists(db: Session, task_id: int) -> None:
    # Service layer doesn't import app/models/task.py (owned by T-003), so existence is
    # checked by table name, same as the FK on task_tags.
    row = db.execute(text("SELECT 1 FROM tasks WHERE id = :task_id"), {"task_id": task_id}).first()
    if row is None:
        raise ApiError(404, "TASK_NOT_FOUND", f"Task {task_id} not found")


def attach_tag(db: Session, task_id: int, name: str) -> Tag:
    _ensure_task_exists(db, task_id)

    tag = db.execute(select(Tag).where(Tag.name == name)).scalar_one_or_none()
    if tag is None:
        tag = Tag(name=name)
        db.add(tag)
        db.commit()
        db.refresh(tag)

    already_attached = db.execute(
        select(task_tags).where(task_tags.c.task_id == task_id, task_tags.c.tag_id == tag.id)
    ).first()
    if already_attached is None:
        db.execute(task_tags.insert().values(task_id=task_id, tag_id=tag.id))
        db.commit()

    return tag


def list_tags(db: Session, task_id: int) -> list[Tag]:
    _ensure_task_exists(db, task_id)

    return list(
        db.execute(
            select(Tag).join(task_tags, task_tags.c.tag_id == Tag.id).where(task_tags.c.task_id == task_id)
        ).scalars()
    )


def detach_tag(db: Session, task_id: int, tag_id: int) -> None:
    _ensure_task_exists(db, task_id)

    tag = db.get(Tag, tag_id)
    if tag is None:
        raise ApiError(404, "TAG_NOT_FOUND", f"Tag {tag_id} not found")

    result = db.execute(
        task_tags.delete().where(task_tags.c.task_id == task_id, task_tags.c.tag_id == tag_id)
    )
    db.commit()
    if result.rowcount == 0:
        raise ApiError(404, "TAG_NOT_FOUND", f"Tag {tag_id} is not attached to task {task_id}")
