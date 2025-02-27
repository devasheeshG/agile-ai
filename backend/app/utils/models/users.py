import uuid
from pydantic import BaseModel, EmailStr, AnyHttpUrl
from fastapi import Path
from typing import List
from enum import Enum

class UserRole(str, Enum):
    FRONTEND = "frontend"
    BACKEND = "backend"
    FULLSTACK = "fullstack"
    DEVOPS = "devops"
    QA = "qa"
    DESIGNER = "designer"

class UserWithId(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    notes: str
    resume_id: str
    role: UserRole

class UserWithoutId(BaseModel):
    name: str
    email: EmailStr
    notes: str
    resume_id: str
    role: UserRole

class CreateUserRequest(BaseModel):
    user: UserWithoutId

class CreateUserResponse(BaseModel):
    user: UserWithId

class GetUsersResponse(BaseModel):
    users: List[UserWithId]

class GetUserRequest(BaseModel):
    user_id: uuid.UUID

    @classmethod
    def query_params(
        cls,
        user_id: uuid.UUID = Path(..., title="User ID", description="The ID of the user to retrieve"),
    ):
        return cls(user_id=user_id)

class GetUserResponse(BaseModel):
    user: UserWithId

class UpdateUserRequest(BaseModel):
    # moved to path parameters as i have no idea how to accept both body data and path parameters
    # in single pydantic model
    # user_id: uuid.UUID
    user: UserWithoutId

class UpdateUserResponse(BaseModel):
    user: UserWithId

class DeleteUserRequest(BaseModel):
    user_id: uuid.UUID
    
    @classmethod
    def query_params(
        cls,
        user_id: uuid.UUID = Path(..., title="User ID", description="The ID of the user to delete"),
    ):
        return cls(user_id=user_id)
