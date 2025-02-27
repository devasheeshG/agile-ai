import uuid
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from fastapi import Path

class UserRole(str, Enum):
    FRONTEND = "frontend"
    BACKEND = "backend"
    FULLSTACK = "fullstack"
    DEVOPS = "devops"
    QA = "qa"
    DESIGNER = "designer"

class UserBase(BaseModel):
    """Base user model with common fields"""
    name: str
    email: EmailStr
    notes: Optional[str] = None
    minio_resume_id: str
    role: UserRole

class UserCreate(UserBase):
    """Model used for creating users"""
    pass

class UserUpdate(UserBase):
    """Model used for updating users - all fields are optional"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    minio_resume_id: Optional[str] = None
    role: Optional[UserRole] = None

class User(UserBase):
    """Complete user model with ID, used for responses"""
    id: uuid.UUID
    
    # Enable ORM mode
    model_config = ConfigDict(from_attributes=True)

# Response Models
class UserListResponse(BaseModel):
    users: List[User]

class CreateUserRequest(BaseModel):
    user: UserCreate

class CreateUserResponse(BaseModel):
    user: User

class GetUsersResponse(BaseModel):
    users: List[User]

class GetUserRequest(BaseModel):
    user_id: uuid.UUID

    @classmethod
    def query_params(
        cls,
        user_id: uuid.UUID = Path(..., title="User ID", description="The ID of the user to retrieve"),
    ):
        return cls(user_id=user_id)

class GetUserResponse(BaseModel):
    user: User

class UpdateUserRequest(BaseModel):
    user: UserUpdate

class UpdateUserResponse(BaseModel):
    user: User

class DeleteUserRequest(BaseModel):
    user_id: uuid.UUID
    
    @classmethod
    def query_params(
        cls,
        user_id: uuid.UUID = Path(..., title="User ID", description="The ID of the user to delete"),
    ):
        return cls(user_id=user_id)
