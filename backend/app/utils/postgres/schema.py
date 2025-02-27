# Path: app/utils/postgres/schema.py
# Description: This file contains the database scheme of the application.

import uuid
from .base import DatabaseBase
from sqlalchemy import (
    Column,
    String,
    UUID,
    Enum,
    ForeignKey,
)
from app.config import get_settings
from sqlalchemy.orm import relationship
from app.utils.models import UserRole, TaskStatus, TaskPriority

settings = get_settings()

class Users(DatabaseBase):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    notes = Column(String, nullable=True)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resume_uploads.id"), nullable=False)
    role = Column(Enum(UserRole), nullable=False)

    # relationship to tasks
    tasks = relationship("Tasks", back_populates="assignee")

class ResumeUploads(DatabaseBase):
    __tablename__ = "resume_uploads"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    minio_resume_id = Column(UUID(as_uuid=True), nullable=False)
    mongodb_resume_id = Column(UUID(as_uuid=True), nullable=False)

class Tasks(DatabaseBase):
    __tablename__ = "tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    assignee_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(Enum(TaskStatus), nullable=False, default=TaskStatus.TODO)
    priority = Column(Enum(TaskPriority), nullable=False, default=TaskPriority.MEDIUM)

    # relationship to users
    assignee = relationship("Users", back_populates="tasks")
