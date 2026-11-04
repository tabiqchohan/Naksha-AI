from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, default="Untitled Project")
    building_type = Column(String, default="house")
    floors = Column(Integer, default=1)
    plot_width = Column(Float)
    plot_length = Column(Float)
    prompt = Column(Text)
    floor_plan_data = Column(JSON)
    thumbnail = Column(Text, nullable=True)
    is_favorite = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="projects")
