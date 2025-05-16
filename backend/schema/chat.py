from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class MessageContent(BaseModel):
    """Structure for message content"""
    message: str
    places: List[Dict[str, Any]] = []
    context: Optional[str] = None
    applied_filters: Dict[str, Any] = Field(default_factory=dict)
    filter_action: str = "keep"  # keep/update/clear

class ChatHistoryItem(BaseModel):
    """Structure for chat history items"""
    role: str
    content: MessageContent
    timestamp: datetime
