from pydantic import BaseModel
from typing import List

class Message(BaseModel):
    role: str  # "user" or "assistant" or "system" or "tool"
    content: str

class ChatRequest(BaseModel):
    user_message: str

class ChatResponse(BaseModel):
    assistant_response: str

class GetChatHistoryResponse(BaseModel):
    messages: List[Message]
