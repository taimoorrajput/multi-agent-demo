from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CommentCreate(BaseModel):
    body: str
    author_id: int


class CommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    author_id: int
    body: str
    created_at: datetime
