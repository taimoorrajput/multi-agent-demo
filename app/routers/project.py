from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.project import ProjectCreate, ProjectRead
from app.services import project as project_service

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectRead, status_code=201)
def create_project(data: ProjectCreate, db: Session = Depends(get_db)) -> ProjectRead:  # noqa: B008
    return project_service.create_project(db, data)


@router.get("", response_model=list[ProjectRead])
def list_projects(owner_id: int | None = None, db: Session = Depends(get_db)) -> list[ProjectRead]:  # noqa: B008
    return project_service.list_projects(db, owner_id)


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: int, db: Session = Depends(get_db)) -> ProjectRead:  # noqa: B008
    return project_service.get_project(db, project_id)
