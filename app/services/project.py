from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.errors import ApiError
from app.models.project import Project
from app.schemas.project import ProjectCreate


def _ensure_owner_exists(db: Session, owner_id: int) -> None:
    # Service layer doesn't import app/models/user.py (owned by T-001), so existence is
    # checked by table name, same as the FK on projects.owner_id.
    row = db.execute(text("SELECT 1 FROM users WHERE id = :owner_id"), {"owner_id": owner_id}).first()
    if row is None:
        raise ApiError(404, "OWNER_NOT_FOUND", f"User {owner_id} not found")


def create_project(db: Session, data: ProjectCreate) -> Project:
    _ensure_owner_exists(db, data.owner_id)

    project = Project(name=data.name, description=data.description, owner_id=data.owner_id)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_project(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise ApiError(404, "PROJECT_NOT_FOUND", f"Project {project_id} not found")
    return project


def list_projects(db: Session, owner_id: int | None = None) -> list[Project]:
    stmt = select(Project)
    if owner_id is not None:
        stmt = stmt.where(Project.owner_id == owner_id)
    return list(db.scalars(stmt))
