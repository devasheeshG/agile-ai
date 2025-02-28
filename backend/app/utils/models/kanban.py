import uuid
from typing import List
from enum import Enum
from pydantic import BaseModel
from fastapi import Path

class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"

class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class TaskBase(BaseModel):
    title: str
    description: str
    assignee_id: uuid.UUID
    status: TaskStatus
    priority: TaskPriority

class TaskWithId(TaskBase):
    id: uuid.UUID

class TaskWithoutId(TaskBase):
    pass

# Request/Response Models
class CreateTaskRequest(BaseModel):
    task: TaskWithoutId

class CreateTaskResponse(BaseModel):
    task: TaskWithId

class GetTasksResponse(BaseModel):
    tasks: List[TaskWithId]

class GetTaskRequest(BaseModel):
    task_id: uuid.UUID
    
    @classmethod
    def query_params(
        cls,
        task_id: uuid.UUID = Path(..., title="Task ID", description="The ID of the task to retrieve"),
    ):
        return cls(task_id=task_id)

class GetTaskResponse(BaseModel):
    task: TaskWithId

class DeleteTaskRequest(BaseModel):
    task_id: uuid.UUID
    
    @classmethod
    def query_params(
        cls,
        task_id: uuid.UUID = Path(..., title="Task ID", description="The ID of the task to delete"),
    ):
        return cls(task_id=task_id)

class UpdateTaskStatusRequest(BaseModel):
    status: TaskStatus

class UpdateTaskAssigneeRequest(BaseModel):
    assignee_id: uuid.UUID

class UpdateTaskPriorityRequest(BaseModel):
    priority: TaskPriority

class UpdateTaskTitleRequest(BaseModel):
    title: str

class UpdateTaskDescriptionRequest(BaseModel):
    description: str
