from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.services import task as task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskRead, status_code=201)
def create_task(data: TaskCreate, db: Session = Depends(get_db)) -> TaskRead:  # noqa: B008
    return task_service.create_task(db, data)


@router.get("", response_model=list[TaskRead])
def list_tasks(project_id: int | None = None, db: Session = Depends(get_db)) -> list[TaskRead]:  # noqa: B008
    return task_service.list_tasks(db, project_id)


@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: int, db: Session = Depends(get_db)) -> TaskRead:  # noqa: B008
    return task_service.get_task(db, task_id)


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(task_id: int, data: TaskUpdate, db: Session = Depends(get_db)) -> TaskRead:  # noqa: B008
    return task_service.update_task(db, task_id, data)
