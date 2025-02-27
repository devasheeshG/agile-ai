from fastapi import APIRouter, Depends, HTTPException, Response, status, Path
import uuid
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.utils.postgres import Users, get_db
from app.utils.minio import get_minio_client, MinioClient
from app.logger import get_logger
from app.utils.models import (
    UserRole,
    CreateUserRequest,
    CreateUserResponse,
    GetUsersResponse,
    GetUserRequest,
    GetUserResponse,
    UpdateUserRequest,
    UpdateUserResponse,
    DeleteUserRequest,
    UserWithId,
)

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

logger = get_logger()
minio_client = get_minio_client()

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(
    request: CreateUserRequest,
    db: Session = Depends(get_db)
) -> CreateUserResponse:
    """Create a new user"""
    try:
        # Create a new user
        user_data = request.user
        db_user = Users(
            name=user_data.name,
            email=user_data.email,
            notes=user_data.notes,
            resume_id=user_data.resume_id,
            role=user_data.role
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return CreateUserResponse(
            user=UserWithId(
                id=db_user.id,
                name=db_user.name,
                email=db_user.email,
                notes=db_user.notes,
                resume_id=db_user.resume_id,
                role=db_user.role
            )
        )

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

@router.get("")
async def get_all_users(
    db: Session = Depends(get_db)
) -> GetUsersResponse:
    """Get all users"""
    try:
        db_users = db.query(Users).all()
        
        users = [UserWithId(
            id=user.id,
            name=user.name,
            email=user.email,
            notes=user.notes or "",
            resume_id=user.resume_id,
            role=user.role
        ) for user in db_users]
        
        return GetUsersResponse(users=users)
    
    except Exception as e:
        logger.error(f"Error retrieving users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )

@router.get("/{user_id}")
async def get_user(
    request: GetUserRequest = Depends(GetUserRequest.query_params),
    db: Session = Depends(get_db)
) -> GetUserResponse:
    """Get a specific user by ID"""
    try:
        db_user = db.query(Users).filter(Users.id == request.user_id).first()
        
        if db_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return GetUserResponse(
            user=UserWithId(
                id=db_user.id,
                name=db_user.name,
                email=db_user.email,
                notes=db_user.notes or "",
                resume_id=db_user.resume_id,
                role=db_user.role
            )
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )

@router.put("/{user_id}")
async def update_user(
    request: UpdateUserRequest,
    user_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db),
    minio_client: MinioClient = Depends(get_minio_client)
) -> UpdateUserResponse:
    """Update a user"""
    try:
        db_user = db.query(Users).filter(Users.id == user_id).first()
        
        if db_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_data = request.user
        
        # Check if resume ID is being changed
        if user_data.resume_id and db_user.resume_id != user_data.resume_id:
            # Delete the old resume if it exists
            if db_user.resume_id:
                minio_client.delete_file(db_user.resume_id)
        
        # Update user data
        db_user.name = user_data.name
        db_user.email = user_data.email
        db_user.notes = user_data.notes
        db_user.resume_id = user_data.resume_id
        db_user.role = user_data.role
        
        db.commit()
        db.refresh(db_user)
        
        return UpdateUserResponse(
            user=UserWithId(
                id=db_user.id,
                name=db_user.name,
                email=db_user.email,
                notes=db_user.notes or "",
                resume_id=db_user.resume_id or "",
                role=db_user.role
            )
        )
    
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

@router.delete("/{user_id}")
async def delete_user(
    request: DeleteUserRequest = Depends(DeleteUserRequest.query_params),
    db: Session = Depends(get_db),
    minio_client: MinioClient = Depends(get_minio_client)
):
    """Delete a user"""
    try:
        db_user = db.query(Users).filter(Users.id == request.user_id).first()
        
        if db_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Delete the resume from MinIO if it exists
        if db_user.resume_id:
            minio_client.delete_file(db_user.resume_id)
        
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
