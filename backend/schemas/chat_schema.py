from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from enum import Enum

class RequestType(str, Enum):
    INSIGHT = "insight"
    GRAPH = "graph"

class ChatRequest(BaseModel):
    session_id: str
    user_message: str

class InsightResponse(BaseModel):
    type: str = "insight"
    message: str
    insights: List[str]
    summary: str

class GraphResponse(BaseModel):
    type: str = "graph"
    message: str
    chart_type: str
    chart_data: Dict[str, Any]
    chart_config: Dict[str, Any]

class ChatResponse(BaseModel):
    request_type: RequestType
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None 