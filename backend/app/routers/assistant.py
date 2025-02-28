from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from openai import OpenAI
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from app.utils.postgres import get_db, Users, Tasks
from app.utils.models import (
    Message,
    ChatRequest,
    ChatResponse,
    GetChatHistoryResponse,
)
from app.config import get_settings
from app.logger import get_logger
import json

router = APIRouter(
    prefix="/assistant",
    tags=["Assistant"],
)

logger = get_logger()
settings = get_settings()
oai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

# MongoDB client setup
mongo_client = AsyncIOMotorClient(settings.get_mongo_uri())
mongo_db = mongo_client[settings.MONGO_DB]
chat_collection = mongo_db[settings.MONGO_COLLECTION_CHAT]

async def add_message_to_chat(role: str, content: str):
    """
    Add a message to an existing chat or create a new chat
    Args:
        role: Role of the message sender (user or assistant)
        content: Message content
    Returns:
        None
    """
    message = {
        "role": role,
        "content": content,
    }
    
    # Try to update existing chat document
    await chat_collection.update_one(
        {"_id": "default"},
        {"$push": {"messages": message}},
        upsert=True  # Create if not exists
    )
    
    logger.info(f"Added {role} message to chat with content: {content}")

async def get_chat_history() -> List[Message]:
    """
    Get chat history
    Args:
        chat_id: ID of the chat
    Returns:
        List of messages in the chat
    """
    chat = await chat_collection.find_one({"_id": "default"})
    
    if not chat or "messages" not in chat:
        logger.info(f"No messages found for chat with ID: default")
        return []
    
    messages = []
    for msg in chat["messages"]:
        messages.append(Message(
            role=msg["role"],
            content=msg["content"],
        ))
    
    logger.info(f"Retrieved {len(messages)} messages for chat with ID: default")
    return messages

async def create_task_internal(
    title: str,
    description: str,
    assignee_id: str,
    priority: str,
    status: str,
    db: Session
):
    """Internal function to create a task in the database"""
    try:
        # Verify assignee exists
        user = db.query(Users).filter(Users.id == assignee_id).first()
        if not user:
            raise ValueError("Assignee not found")
            
        # Create a new task
        db_task = Tasks(
            title=title,
            description=description,
            assignee_id=assignee_id,
            status=status,
            priority=priority
        )
        
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        
        return db_task
        
    except Exception as e:
        db.rollback()
        raise e

async def edit_task_internal(
    task_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    assignee_id: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Internal function to edit a task in the database"""
    try:
        # Find the task
        db_task = db.query(Tasks).filter(Tasks.id == task_id).first()
        if not db_task:
            raise ValueError("Task not found")
            
        # Update fields if provided
        if title is not None:
            db_task.title = title
        if description is not None:
            db_task.description = description
        if assignee_id is not None:
            # Verify assignee exists
            user = db.query(Users).filter(Users.id == assignee_id).first()
            if not user:
                raise ValueError("Assignee not found")
            db_task.assignee_id = assignee_id
        if priority is not None:
            db_task.priority = priority
        if status is not None:
            db_task.status = status
        
        db.commit()
        db.refresh(db_task)
        
        return db_task
        
    except Exception as e:
        db.rollback()
        raise e

async def delete_task_internal(
    task_id: str,
    db: Session
):
    """Internal function to delete a task in the database"""
    try:
        # Find the task
        db_task = db.query(Tasks).filter(Tasks.id == task_id).first()
        if not db_task:
            raise ValueError("Task not found")
            
        # Delete the task
        db.delete(db_task)
        db.commit()
        
        return True
        
    except Exception as e:
        db.rollback()
        raise e

SYSTEM_PROMPT = """
You are a helpful task management assistant. Your primary responsibility is to help project managers create, edit, and manage tasks.

When a project manager describes a task they want to create, COLLECT all necessary information FIRST before creating the task.

You can:
1. Create new tasks using the create_task function
2. Edit existing tasks using the edit_task function
3. Delete tasks using the delete_task function

If the user doesn't specify all required information, ask follow-up questions to collect it.

Be conversational and helpful. If users ask questions about task management in general, answer them.

You can also help users find the right assignee for a task by suggesting users from the available list.
"""

@router.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(request: ChatRequest, db: Session = Depends(get_db)):
    """Chat with the AI assistant that can manage tasks"""
    try:
        # Fetch users and tasks from the database
        users = db.query(Users).all()
        tasks = db.query(Tasks).all()

        # Format users into a readable format for the prompt
        formatted_users = "\n".join([
            f"- ID: {user.id}, Name: {user.name}, Email: {user.email}, Role: {user.role}"
            for user in users
        ])

        # Format tasks into a readable format for the prompt
        formatted_tasks = "\n".join([
            f"- ID: {task.id}, Title: {task.title}, Status: {task.status}, " +
            f"Priority: {task.priority}, Assignee: {task.assignee_id}"
            for task in tasks
        ])

        # Update system prompt with this information
        dynamic_system_prompt = f"""
{SYSTEM_PROMPT}

AVAILABLE USERS:
{formatted_users}

EXISTING TASKS:
{formatted_tasks}
"""
        
        # Define available tools
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "create_task",
                    "description": "Create a new task and assign it to a user",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "The title of the task"
                            },
                            "description": {
                                "type": "string",
                                "description": "Detailed description of the task"
                            },
                            "assignee_id": {
                                "type": "string",
                                "description": "UUID of the user to assign the task to"
                            },
                            "priority": {
                                "type": "string",
                                "enum": ["low", "medium", "high"],
                                "description": "Priority of the task"
                            },
                            "status": {
                                "type": "string",
                                "enum": ["todo", "in_progress", "review", "done"],
                                "description": "Status of the task",
                            }
                        },
                        "required": ["title", "description", "assignee_id", "priority", "status"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "edit_task",
                    "description": "Edit an existing task",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "UUID of the task to edit"
                            },
                            "title": {
                                "type": "string",
                                "description": "New title of the task (optional)"
                            },
                            "description": {
                                "type": "string",
                                "description": "New description of the task (optional)"
                            },
                            "assignee_id": {
                                "type": "string",
                                "description": "UUID of the new assignee (optional)"
                            },
                            "priority": {
                                "type": "string",
                                "enum": ["low", "medium", "high"],
                                "description": "New priority of the task (optional)"
                            },
                            "status": {
                                "type": "string",
                                "enum": ["todo", "in_progress", "review", "done"],
                                "description": "New status of the task (optional)",
                            }
                        },
                        "required": ["task_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_task",
                    "description": "Delete an existing task",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "UUID of the task to delete"
                            }
                        },
                        "required": ["task_id"]
                    }
                }
            }
        ]
        
        # Create system message
        system_message = {
            "role": "system", 
            "content": dynamic_system_prompt
        }
        
        # Retrieve chat history from MongoDB
        previous_messages = await get_chat_history()
        previous_messages_dict = [msg.model_dump() for msg in previous_messages]
        
        # Add the new user message to MongoDB
        await add_message_to_chat("user", request.user_message)
        
        # Compile full message history with system message, previous messages, and new user message
        messages = [system_message] + previous_messages_dict + [{"role": "user", "content": request.user_message}]
        
        # Call OpenAI API
        response = oai_client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        
        # Check if the model wants to call a function
        if response_message.tool_calls:
            # Handle the function calls
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                # Process different function calls
                if function_name == "create_task":
                    # Create task in database
                    task_created = await create_task_internal(
                        title=function_args["title"],
                        description=function_args["description"],
                        assignee_id=function_args["assignee_id"],
                        priority=function_args.get("priority", "medium"),
                        status=function_args.get("status", "todo"),
                        db=db
                    )
                    
                    # Add the result of the function call
                    messages.append(response_message.model_dump())
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": json.dumps({"task_id": str(task_created.id), "success": True})
                    })
                
                elif function_name == "edit_task":
                    # Edit task in database
                    task_edited = await edit_task_internal(
                        task_id=function_args["task_id"],
                        title=function_args.get("title"),
                        description=function_args.get("description"),
                        assignee_id=function_args.get("assignee_id"),
                        priority=function_args.get("priority"),
                        status=function_args.get("status"),
                        db=db
                    )
                    
                    # Add the result of the function call
                    messages.append(response_message.model_dump())
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": json.dumps({"task_id": str(task_edited.id), "success": True})
                    })
                
                elif function_name == "delete_task":
                    # Delete task in database
                    success = await delete_task_internal(
                        task_id=function_args["task_id"],
                        db=db
                    )
                    
                    # Add the result of the function call
                    messages.append(response_message.model_dump())
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": json.dumps({"success": success})
                    })
            
            # Get a new response from the model with the function results
            second_response = oai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=messages
            )
            
            assistant_response = second_response.choices[0].message.content
            
            # Store assistant's response in MongoDB
            await add_message_to_chat("assistant", assistant_response)
            
            return ChatResponse(assistant_response=assistant_response)
        
        # If no function call, just return the response
        assistant_response = response_message.content
        
        # Store assistant's response in MongoDB
        await add_message_to_chat("assistant", assistant_response)
        
        return ChatResponse(assistant_response=assistant_response)
    
    except Exception as e:
        logger.error(f"Error in chat with assistant: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat: {str(e)}"
        )

@router.get("/history", response_model=GetChatHistoryResponse)
async def get_chat_history_route() -> GetChatHistoryResponse:
    """Get chat history"""
    try:
        messages = await get_chat_history()
        return GetChatHistoryResponse(messages=messages)
    
    except Exception as e:
        logger.error(f"Error in get_chat_history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chat history: {str(e)}"
        )
