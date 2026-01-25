from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any
from pydantic import BaseModel, Field
import httpx
import logging

from core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/calls", tags=["calls"])

ELEVENLABS_OUTBOUND_CALL_URL = "https://api.elevenlabs.io/v1/convai/twilio/outbound-call"
AGENT_ID = "agent_4901kfrz4hkwf5hbz134xv9j0jc8"
AGENT_PHONE_NUMBER_ID = "phnum_2501kfsbbhfcfvjag6vytc7j2d98"


class OutboundCallRequest(BaseModel):
    to_number: str = Field(..., description="Phone number to call (E.164 format, e.g., +14155551234)")


@router.post("/outbound", response_model=Dict[str, Any])
async def initiate_outbound_call(request: OutboundCallRequest):
    """
    Initiate an outbound call using ElevenLabs Conversational AI.
    
    **Requirements:**
    - `to_number`: The recipient's phone number in E.164 format (e.g., +14155551234)
    
    **Agent Configuration:**
    - Agent ID: agent_4901kfrz4hkwf5hbz134xv9j0jc8
    - Agent Phone: phnum_2501kfsbbhfcfvjag6vytc7j2d98
    
    **Returns:**
    - Call initiation response from ElevenLabs API
    """
    
    if not settings.xi_api_key:
        raise HTTPException(
            status_code=500,
            detail="XI_API_KEY not configured. Please set it in your environment variables."
        )
    
    # Prepare the request payload
    payload = {
        "agent_id": AGENT_ID,
        "agent_phone_number_id": AGENT_PHONE_NUMBER_ID,
        "to_number": request.to_number
    }
    
    # Prepare headers
    headers = {
        "xi-api-key": settings.xi_api_key,
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                ELEVENLABS_OUTBOUND_CALL_URL,
                json=payload,
                headers=headers,
                timeout=30.0
            )
            
            # Check if the request was successful
            if response.status_code == 200:
                logger.info(f"Outbound call initiated to {request.to_number} with agent {AGENT_ID}")
                return response.json()
            else:
                error_detail = response.text
                logger.error(f"ElevenLabs API error: {response.status_code} - {error_detail}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"ElevenLabs API error: {error_detail}"
                )
                
    except httpx.RequestError as e:
        logger.error(f"Request error when calling ElevenLabs API: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to connect to ElevenLabs API: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error initiating outbound call: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )
