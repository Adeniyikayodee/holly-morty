from fastapi import APIRouter, Request, HTTPException, status
import time
import hmac
from hashlib import sha256
import json
import logging

from models.elevenlabs import ElevenLabsWebhook
from core.config import settings
from core.cosmos import cosmos_client, Containers

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def verify_elevenlabs_signature(payload: bytes, signature_header: str, secret: str) -> bool:
    """
    Verify the ElevenLabs webhook signature.
    
    Args:
        payload: Raw request body
        signature_header: The elevenlabs-signature header value
        secret: Your ElevenLabs webhook secret
        
    Returns:
        True if signature is valid, False otherwise
    """
    if not signature_header or not secret:
        return False
    
    try:
        # Parse the signature header
        parts = signature_header.split(",")
        timestamp = parts[0][2:]  # Remove 't=' prefix
        hmac_signature = parts[1]  # This includes 'v0=' prefix
        
        # Validate timestamp (within 30 minutes)
        tolerance = int(time.time()) - 30 * 60
        if int(timestamp) < tolerance:
            return False
        
        # Compute expected signature
        full_payload_to_sign = f"{timestamp}.{payload.decode('utf-8')}"
        mac = hmac.new(
            key=secret.encode("utf-8"),
            msg=full_payload_to_sign.encode("utf-8"),
            digestmod=sha256,
        )
        expected_signature = 'v0=' + mac.hexdigest()
        
        # Compare signatures
        return hmac.compare_digest(hmac_signature, expected_signature)
    except Exception as e:
        print(f"Error verifying signature: {e}")
        return False


@router.post("/holly-conversation")
async def holly_conversation_webhook(request: Request):
    """
    Webhook endpoint for ElevenLabs post-call transcription events.
    
    Receives and processes conversation data from Holly (ElevenLabs AI agent).
    """
    # Get raw payload and signature header
    payload = await request.body()
    
    # signature_header = request.headers.get("elevenlabs-signature")
    
    # # Verify webhook signature if secret is configured
    # if settings.elevenlabs_webhook_secret:
    #     if not signature_header:
    #         raise HTTPException(
    #             status_code=status.HTTP_401_UNAUTHORIZED,
    #             detail="Missing elevenlabs-signature header"
    #         )
        
    #     if not verify_elevenlabs_signature(
    #         payload, 
    #         signature_header, 
    #         settings.elevenlabs_webhook_secret
    #     ):
    #         raise HTTPException(
    #             status_code=status.HTTP_401_UNAUTHORIZED,
    #             detail="Invalid webhook signature"
    #         )
    
    # Parse the webhook payload
    # Fix invalid escape sequences in the payload (ElevenLabs sends \' which is not valid JSON)
    try:
        payload_str = payload.decode('utf-8')
        # Replace invalid \' with just ' (single quotes don't need escaping in JSON)
        #payload_str = payload_str.replace("\\'", "'")
        webhook_data = json.loads(payload_str)
    except Exception as e:
        logger.error(f"Error parsing webhook payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid webhook payload: {str(e)}"
        )
    
    # Process only post_call_transcription events
    if webhook_data["type"] == "post_call_transcription":
        conversation_id = webhook_data['data']['conversation_id']
        
        logger.info("📞 POST CALL TRANSCRIPTION RECEIVED")
        logger.info(f"Agent ID: {webhook_data['data']['agent_id']}")
        logger.info(f"Conversation ID: {conversation_id}")
        logger.info(f"Status: {webhook_data['data']['status']}")
        
        # Store in Cosmos DB conversations container
        try:
            stored_item = await cosmos_client.upsert_item(
                container=Containers.CONVERSATIONS,
                item=webhook_data['data'],
                partition_key_value=conversation_id
            )
            logger.info(f"✅ Conversation stored in Cosmos DB: {conversation_id}")
        except Exception as e:
            logger.error(f"Failed to store conversation in Cosmos DB: {e}")
            # Don't fail the webhook if storage fails
    else:
        logger.info(f"Received webhook event of type: {webhook_data['type']} (not processing)")
    
    return {"status": "received"}
