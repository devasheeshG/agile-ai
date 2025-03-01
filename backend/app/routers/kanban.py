from fastapi import APIRouter, Depends, HTTPException, Response, status
import uuid
from sqlalchemy.orm import Session
from app.utils.postgres import Tasks, Users, get_db
from app.logger import get_logger
from typing import Optional
from app.utils.models import (
    TaskStatus,
    TaskPriority,
    CreateTaskRequest,
    CreateTaskResponse,
    GetTasksResponse,
    GetTaskRequest,
    GetTaskResponse,
    DeleteTaskRequest,
    TaskWithId,
    UpdateTaskStatusRequest,
    UpdateTaskAssigneeRequest,
    UpdateTaskPriorityRequest,
    UpdateTaskTitleRequest,
    UpdateTaskDescriptionRequest,
)

router = APIRouter(
    prefix="/tasks",
    tags=["Kanban"],
)

logger = get_logger()

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_task(
    request: CreateTaskRequest,
    db: Session = Depends(get_db)
) -> CreateTaskResponse:
    """Create a new task"""
    try:
        # Verify assignee exists
        user = db.query(Users).filter(Users.id == request.task.assignee_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignee not found"
            )
            
        # Create a new task
        task_data = request.task
        db_task = Tasks(
            title=task_data.title,
            description=task_data.description,
            assignee_id=task_data.assignee_id,
            status=task_data.status,
            priority=task_data.priority
        )
        
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        
        return CreateTaskResponse(
            task=TaskWithId(
                id=db_task.id,
                title=db_task.title,
                description=db_task.description,
                assignee_id=db_task.assignee_id,
                status=db_task.status,
                priority=db_task.priority,
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create task"
        )

@router.get("")
async def get_tasks(
    assignee_id: Optional[uuid.UUID] = None,
    priority: Optional[TaskPriority] = None,
    status: Optional[TaskStatus] = None,
    db: Session = Depends(get_db)
) -> GetTasksResponse:
    """Get all tasks with optional filtering"""
    try:
        query = db.query(Tasks)
        
        # Apply filters if provided
        if assignee_id:
            query = query.filter(Tasks.assignee_id == assignee_id)
        if priority:
            query = query.filter(Tasks.priority == priority)
        if status:
            query = query.filter(Tasks.status == status)
            
        tasks = query.all()
        
        return GetTasksResponse(
            tasks=[TaskWithId(
                id=task.id,
                title=task.title,
                description=task.description,
                assignee_id=task.assignee_id,
                status=task.status,
                priority=task.priority,
            ) for task in tasks]
        )
    
    except Exception as e:
        logger.error(f"Error retrieving tasks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tasks"
        )

@router.get("/{task_id}")
async def get_task(
    request: GetTaskRequest = Depends(GetTaskRequest.query_params),
    db: Session = Depends(get_db)
) -> GetTaskResponse:
    """Get a specific task by ID"""
    try:
        db_task = db.query(Tasks).filter(Tasks.id == request.task_id).first()
        
        if db_task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        return GetTaskResponse(
            task=TaskWithId(
                id=db_task.id,
                title=db_task.title,
                description=db_task.description,
                assignee_id=db_task.assignee_id,
                status=db_task.status,
                priority=db_task.priority,
            )
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve task"
        )

@router.patch("/{task_id}/status")
async def update_task_status(
    task_id: uuid.UUID,
    request: UpdateTaskStatusRequest,
    db: Session = Depends(get_db)
) -> TaskWithId:
    """Update a task's status"""
    try:
        db_task = db.query(Tasks).filter(Tasks.id == task_id).first()
        
        if db_task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        db_task.status = request.status
        db.commit()
        db.refresh(db_task)
        
        return TaskWithId(
            id=db_task.id,
            title=db_task.title,
            description=db_task.description,
            assignee_id=db_task.assignee_id,
            status=db_task.status,
            priority=db_task.priority,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating task status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update task status"
        )

@router.patch("/{task_id}/assignee")
async def update_task_assignee(
    task_id: uuid.UUID,
    request: UpdateTaskAssigneeRequest,
    db: Session = Depends(get_db)
) -> TaskWithId:
    """Update a task's assignee"""
    try:
        db_task = db.query(Tasks).filter(Tasks.id == task_id).first()
        
        if db_task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Verify the new assignee exists
        user = db.query(Users).filter(Users.id == request.assignee_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignee not found"
            )
            
        db_task.assignee_id = request.assignee_id
        db.commit()
        db.refresh(db_task)
        
        return TaskWithId(
            id=db_task.id,
            title=db_task.title,
            description=db_task.description,
            assignee_id=db_task.assignee_id,
            status=db_task.status,
            priority=db_task.priority,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating task assignee: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update task assignee"
        )

@router.patch("/{task_id}/priority")
async def update_task_priority(
    task_id: uuid.UUID,
    request: UpdateTaskPriorityRequest,
    db: Session = Depends(get_db)
) -> TaskWithId:
    """Update a task's priority"""
    try:
        db_task = db.query(Tasks).filter(Tasks.id == task_id).first()
        
        if db_task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        db_task.priority = request.priority
        db.commit()
        db.refresh(db_task)
        
        return TaskWithId(
            id=db_task.id,
            title=db_task.title,
            description=db_task.description,
            assignee_id=db_task.assignee_id,
            status=db_task.status,
            priority=db_task.priority,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating task priority: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update task priority"
        )

@router.patch("/{task_id}/title")
async def update_task_title(
    task_id: uuid.UUID,
    request: UpdateTaskTitleRequest,
    db: Session = Depends(get_db)
) -> TaskWithId:
    """Update a task's title"""
    try:
        db_task = db.query(Tasks).filter(Tasks.id == task_id).first()
        
        if db_task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        db_task.title = request.title
        db.commit()
        db.refresh(db_task)
        
        return TaskWithId(
            id=db_task.id,
            title=db_task.title,
            description=db_task.description,
            assignee_id=db_task.assignee_id,
            status=db_task.status,
            priority=db_task.priority,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating task title: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update task title"
        )

@router.patch("/{task_id}/description")
async def update_task_description(
    task_id: uuid.UUID,
    request: UpdateTaskDescriptionRequest,
    db: Session = Depends(get_db)
) -> TaskWithId:
    """Update a task's description"""
    try:
        db_task = db.query(Tasks).filter(Tasks.id == task_id).first()
        
        if db_task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        db_task.description = request.description
        db.commit()
        db.refresh(db_task)
        
        return TaskWithId(
            id=db_task.id,
            title=db_task.title,
            description=db_task.description,
            assignee_id=db_task.assignee_id,
            status=db_task.status,
            priority=db_task.priority,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating task description: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update task description"
        )

@router.delete("/{task_id}")
async def delete_task(
    request: DeleteTaskRequest = Depends(DeleteTaskRequest.query_params),
    db: Session = Depends(get_db)
):
    """Delete a task"""
    try:
        db_task = db.query(Tasks).filter(Tasks.id == request.task_id).first()
        
        if db_task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        db.delete(db_task)
        db.commit()
        
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete task"
        )
