from fastapi import APIRouter, Depends, HTTPException, Response, status, Path
import uuid
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.utils.postgres import Users, get_db
from app.utils.minio import get_minio_client, MinioClient
from app.logger import get_logger
from app.utils.models.users import (
    UserCreate,
    UserUpdate,
    User,
    UserListResponse,
)

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

logger = get_logger()
minio_client = get_minio_client()

@router.post("", status_code=status.HTTP_201_CREATED, response_model=User)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Create a new user"""
    try:
        # Create a new user
        db_user = Users(**user_data.model_dump())
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return db_user

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

@router.get("", response_model=UserListResponse)
async def get_all_users(
    db: Session = Depends(get_db)
):
    """Get all users"""
    try:
        db_users = db.query(Users).all()
        return UserListResponse(users=db_users)
    
    except Exception as e:
        logger.error(f"Error retrieving users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )

@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: uuid.UUID = Path(..., description="The ID of the user to retrieve"),
    db: Session = Depends(get_db)
):
    """Get a specific user by ID"""
    try:
        db_user = db.query(Users).filter(Users.id == user_id).first()
        
        if db_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return db_user
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )

@router.put("/{user_id}", response_model=User)
async def update_user(
    user_data: UserUpdate,
    user_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db),
    minio_client: MinioClient = Depends(get_minio_client)
):
    """Update a user"""
    try:
        db_user = db.query(Users).filter(Users.id == user_id).first()
        
        if db_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if resume ID is being changed
        if user_data.minio_resume_id and db_user.minio_resume_id != user_data.minio_resume_id:
            # Delete the old resume if it exists
            if db_user.minio_resume_id:
                minio_client.delete_file(db_user.minio_resume_id)
        
        # Update user data - only update fields that are provided
        update_data = user_data.model_dump(exclude_unset=True, exclude_none=True)
        for key, value in update_data.items():
            setattr(db_user, key, value)
        
        db.commit()
        db.refresh(db_user)
        
        return db_user
    
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID = Path(..., description="The ID of the user to delete"),
    db: Session = Depends(get_db),
    minio_client: MinioClient = Depends(get_minio_client)
):
    """Delete a user"""
    try:
        db_user = db.query(Users).filter(Users.id == user_id).first()
        
        if db_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Delete the resume from MinIO if it exists
        if db_user.minio_resume_id:
            minio_client.delete_file(db_user.minio_resume_id)
        
        # Delete the user from the database
        db.delete(db_user)
        db.commit()
        
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )
