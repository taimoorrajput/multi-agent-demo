from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class TagCreate(BaseModel):
    name: str


class TagRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
