from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid
from app.database import get_db
from app.auth.dependencies import get_current_active_user
from app.models.user_models import User
from app.models.project_models import Project

router = APIRouter(prefix="/projects", tags=["Projects"])


class ProjectCreate(BaseModel):
    title: str
    building_type: str = "house"
    floors: int = 1
    plot_width: float
    plot_length: float
    prompt: Optional[str] = ""
    floor_plan_data: dict


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    is_favorite: Optional[bool] = None
    floor_plan_data: Optional[dict] = None


@router.post("/save")
async def save_project(req: ProjectCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    project_id = str(uuid.uuid4())[:8]
    project = Project(
        project_id=project_id,
        user_id=current_user.id,
        title=req.title,
        building_type=req.building_type,
        floors=req.floors,
        plot_width=req.plot_width,
        plot_length=req.plot_length,
        prompt=req.prompt,
        floor_plan_data=req.floor_plan_data
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return {"message": "Project saved", "project_id": project.project_id, "id": project.id}


@router.get("/list")
async def list_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    projects = db.query(Project).filter(Project.user_id == current_user.id).order_by(Project.updated_at.desc()).all()
    return [{"id": p.id, "project_id": p.project_id, "title": p.title, "building_type": p.building_type, "floors": p.floors, "plot_width": p.plot_width, "plot_length": p.plot_length, "created_at": p.created_at, "updated_at": p.updated_at} for p in projects]


@router.get("/{project_id}")
async def get_project(project_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    project = db.query(Project).filter(Project.project_id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}")
async def update_project(project_id: str, req: ProjectUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    project = db.query(Project).filter(Project.project_id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if req.title is not None:
        project.title = req.title
    if req.is_favorite is not None:
        project.is_favorite = req.is_favorite
    if req.floor_plan_data is not None:
        project.floor_plan_data = req.floor_plan_data
    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(project)
    return {"message": "Project updated"}


@router.delete("/{project_id}")
async def delete_project(project_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    project = db.query(Project).filter(Project.project_id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return {"message": "Project deleted"}
