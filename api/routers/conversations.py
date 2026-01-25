from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
import logging

from core.cosmos import cosmos_client, Containers

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("/", response_model=Dict[str, Any])
async def get_all_conversations(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user_id: Optional[str] = None
):
    """
    Get all conversations with optional filtering by user_id.
    Supports pagination via limit and offset.
    """
    try:
        # Build query based on filters
        if user_id:
            query = "SELECT * FROM c WHERE c.user_id = @user_id OFFSET @offset LIMIT @limit"
            parameters = [
                {"name": "@user_id", "value": user_id},
                {"name": "@offset", "value": offset},
                {"name": "@limit", "value": limit}
            ]
        else:
            query = "SELECT * FROM c OFFSET @offset LIMIT @limit"
            parameters = [
                {"name": "@offset", "value": offset},
                {"name": "@limit", "value": limit}
            ]
        
        items = await cosmos_client.query_items(
            container=Containers.CONVERSATIONS,
            query=query,
            parameters=parameters
        )
        
        # Get total count for pagination
        count_query = "SELECT VALUE COUNT(1) FROM c" + (
            " WHERE c.user_id = @user_id" if user_id else ""
        )
        count_params = [{"name": "@user_id", "value": user_id}] if user_id else []
        count_result = await cosmos_client.query_items(
            container=Containers.CONVERSATIONS,
            query=count_query,
            parameters=count_params
        )
        total = count_result[0] if count_result else 0
        
        return {
            "conversations": items,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(items) < total
        }
        
    except Exception as e:
        logger.error(f"Error fetching conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}", response_model=Dict[str, Any])
async def get_conversation_by_id(conversation_id: str):
    """
    Get a specific conversation by ID.
    """
    try:
        item = await cosmos_client.read_item(
            container=Containers.CONVERSATIONS,
            item_id=conversation_id,
            partition_key_value=conversation_id
        )
        
        if not item:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return item
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}", response_model=Dict[str, Any])
async def get_conversations_by_user(
    user_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    """
    Get all conversations for a specific user.
    """
    try:
        query = """
            SELECT * FROM c 
            WHERE c.user_id = @user_id 
            ORDER BY c._ts DESC
            OFFSET @offset LIMIT @limit
        """
        parameters = [
            {"name": "@user_id", "value": user_id},
            {"name": "@offset", "value": offset},
            {"name": "@limit", "value": limit}
        ]
        
        items = await cosmos_client.query_items(
            container=Containers.CONVERSATIONS,
            query=query,
            parameters=parameters
        )
        
        # Get count
        count_query = "SELECT VALUE COUNT(1) FROM c WHERE c.user_id = @user_id"
        count_result = await cosmos_client.query_items(
            container=Containers.CONVERSATIONS,
            query=count_query,
            parameters=[{"name": "@user_id", "value": user_id}]
        )
        total = count_result[0] if count_result else 0
        
        return {
            "conversations": items,
            "total": total,
            "limit": limit,
            "offset": offset,
            "user_id": user_id,
            "has_more": offset + len(items) < total
        }
        
    except Exception as e:
        logger.error(f"Error fetching conversations for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/by-status", response_model=Dict[str, Any])
async def search_conversations_by_status(
    status: str,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    """
    Search conversations by status (e.g., 'done', 'in_progress').
    """
    try:
        query = """
            SELECT * FROM c 
            WHERE c.status = @status 
            ORDER BY c._ts DESC
            OFFSET @offset LIMIT @limit
        """
        parameters = [
            {"name": "@status", "value": status},
            {"name": "@offset", "value": offset},
            {"name": "@limit", "value": limit}
        ]
        
        items = await cosmos_client.query_items(
            container=Containers.CONVERSATIONS,
            query=query,
            parameters=parameters
        )
        
        return {
            "conversations": items,
            "total": len(items),
            "limit": limit,
            "offset": offset,
            "status": status
        }
        
    except Exception as e:
        logger.error(f"Error searching conversations by status {status}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/by-agent", response_model=Dict[str, Any])
async def search_conversations_by_agent(
    agent_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    """
    Search conversations by agent ID.
    """
    try:
        query = """
            SELECT * FROM c 
            WHERE c.agent_id = @agent_id 
            ORDER BY c._ts DESC
            OFFSET @offset LIMIT @limit
        """
        parameters = [
            {"name": "@agent_id", "value": agent_id},
            {"name": "@offset", "value": offset},
            {"name": "@limit", "value": limit}
        ]
        
        items = await cosmos_client.query_items(
            container=Containers.CONVERSATIONS,
            query=query,
            parameters=parameters
        )
        
        return {
            "conversations": items,
            "total": len(items),
            "limit": limit,
            "offset": offset,
            "agent_id": agent_id
        }
        
    except Exception as e:
        logger.error(f"Error searching conversations by agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/by-date-range", response_model=Dict[str, Any])
async def search_conversations_by_date(
    start_timestamp: int,
    end_timestamp: int,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    """
    Search conversations within a date range using Unix timestamps.
    """
    try:
        query = """
            SELECT * FROM c 
            WHERE c.metadata.start_time_unix_secs >= @start 
            AND c.metadata.start_time_unix_secs <= @end
            ORDER BY c.metadata.start_time_unix_secs DESC
            OFFSET @offset LIMIT @limit
        """
        parameters = [
            {"name": "@start", "value": start_timestamp},
            {"name": "@end", "value": end_timestamp},
            {"name": "@offset", "value": offset},
            {"name": "@limit", "value": limit}
        ]
        
        items = await cosmos_client.query_items(
            container=Containers.CONVERSATIONS,
            query=query,
            parameters=parameters
        )
        
        return {
            "conversations": items,
            "total": len(items),
            "limit": limit,
            "offset": offset,
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp
        }
        
    except Exception as e:
        logger.error(f"Error searching conversations by date range: {e}")
        raise HTTPException(status_code=500, detail=str(e))
