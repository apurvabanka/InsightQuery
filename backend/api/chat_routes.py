from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from db.session import get_db
from services.chat_service import ChatService
from schemas.chat_schema import ChatRequest, ChatResponse, RequestType

router = APIRouter()

# Initialize chat service
chat_service = ChatService()

@router.post("/chat", response_model=ChatResponse)
def chat_with_data(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Chat endpoint that processes user messages and returns insights or graph configurations.
    
    The system automatically determines if the user is asking for:
    - Insights: Analysis, trends, patterns, understanding of data
    - Graphs: Charts, visualizations, plots, visual representations
    """
    
    try:
        # Process the chat request
        result = chat_service.process_chat(
            db=db,
            session_id=request.session_id,
            user_message=request.user_message
        )

        print("Request Type : ", result.get("request_type"))


        
        # Convert result to response format
        if result.get("request_type") == "error":
            return ChatResponse(
                request_type=RequestType.INSIGHT,  # Default type for errors
                message=result.get("message", "An error occurred"),
                error=result.get("error", "Unknown error")
            )
        
        request_type = RequestType(result.get("request_type", "insight"))
        
        return ChatResponse(
            request_type=request_type,
            message=result.get("message", "Request processed successfully"),
            data=result.get("data", {})
        )
        
    except ValueError as e:
        # Handle specific errors like missing session or CSV files
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # Handle other unexpected errors
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/chat/health")
def chat_health_check():
    """
    Health check endpoint for the chat service
    """
    try:
        # Check if OpenAI API key is configured
        import os
        
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            return {
                "status": "warning",
                "message": "OpenAI API key not configured. Chat functionality may not work properly.",
                "openai_configured": False
            }
        
        return {
            "status": "healthy",
            "message": "Chat service is ready",
            "openai_configured": True
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Chat service error: {str(e)}",
            "openai_configured": False
        } 