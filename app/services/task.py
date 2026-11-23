from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.errors import ApiError
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate


def _project_exists(db: Session, project_id: int) -> bool:
    row = db.execute(text("SELECT 1 FROM projects WHERE id = :id"), {"id": project_id}).first()
    return row is not None


def _user_exists(db: Session, user_id: int) -> bool:
    row = db.execute(text("SELECT 1 FROM users WHERE id = :id"), {"id": user_id}).first()
    return row is not None


def create_task(db: Session, data: TaskCreate) -> Task:
    if not _project_exists(db, data.project_id):
        raise ApiError(404, "PROJECT_NOT_FOUND", f"Project {data.project_id} not found")
    if data.assignee_id is not None and not _user_exists(db, data.assignee_id):
        raise ApiError(404, "ASSIGNEE_NOT_FOUND", f"User {data.assignee_id} not found")

    task = Task(
        title=data.title,
        description=data.description,
        project_id=data.project_id,
        assignee_id=data.assignee_id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_task(db: Session, task_id: int) -> Task:
    task = db.get(Task, task_id)
    if task is None:
        raise ApiError(404, "TASK_NOT_FOUND", f"Task {task_id} not found")
    return task


def update_task(db: Session, task_id: int, data: TaskUpdate) -> Task:
    task = get_task(db, task_id)

    if data.assignee_id is not None and not _user_exists(db, data.assignee_id):
        raise ApiError(404, "ASSIGNEE_NOT_FOUND", f"User {data.assignee_id} not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task


def list_tasks(db: Session, project_id: int | None = None) -> list[Task]:
    stmt = select(Task)
    if project_id is not None:
        stmt = stmt.where(Task.project_id == project_id)
    return list(db.scalars(stmt))
