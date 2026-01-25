from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from core.cosmos import cosmos_client, Containers
from models.profile import FinancialProfile, ProfileStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.post("/", response_model=Dict[str, Any], status_code=201)
async def create_profile(
    user_id: str = Body(...),
    first_name: Optional[str] = Body(None),
    last_name: Optional[str] = Body(None)
):
    """
    Create a new profile with minimal information (user_id and optional name).
    Profile will be created with 'incomplete' status and default values.
    """
    try:
        # Check if profile already exists
        try:
            existing = await cosmos_client.read_item(
                container=Containers.PROFILES,
                item_id=user_id,
                partition_key_value=user_id
            )
            if existing:
                raise HTTPException(
                    status_code=409,
                    detail=f"Profile already exists for user_id: {user_id}"
                )
        except:
            # Profile doesn't exist, continue with creation
            pass
        
        # Create minimal profile
        now = datetime.utcnow().isoformat()
        profile_data = {
            "user_id": user_id,
            "id": user_id,
            "status": ProfileStatus.INCOMPLETE.value,
            "personal_info": {
                "first_name": first_name,
                "last_name": last_name,
                "date_of_birth": None,
                "nationality": None,
                "marital_status": None,
                "number_of_dependents": None,
                "contact_email": None,
                "contact_phone": None
            },
            "employment": None,
            "financial_position": None,
            "financial_goals": [],
            "risk_profile": None,
            "existing_investments": [],
            "created_at": now,
            "updated_at": now,
            "conversation_id": None,
            "completeness_percentage": 0.0
        }
        
        # Validate with Pydantic
        validated_profile = FinancialProfile(**profile_data)
        profile_dict = validated_profile.model_dump(mode='json', exclude_none=False)
        
        # Save to Cosmos DB
        created_item = await cosmos_client.upsert_item(
            container=Containers.PROFILES,
            item=profile_dict,
            partition_key_value=user_id
        )
        
        logger.info(f"Profile created for user {user_id}")
        return created_item
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating profile for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=Dict[str, Any])
async def get_all_profiles(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: Optional[ProfileStatus] = None
):
    """
    Get all profiles with optional filtering by status.
    Supports pagination via limit and offset.
    """
    try:
        # Build query based on filters
        if status:
            query = "SELECT * FROM c WHERE c.status = @status OFFSET @offset LIMIT @limit"
            parameters = [
                {"name": "@status", "value": status.value},
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
            container=Containers.PROFILES,
            query=query,
            parameters=parameters
        )
        
        # Get total count
        count_query = "SELECT VALUE COUNT(1) FROM c" + (
            " WHERE c.status = @status" if status else ""
        )
        count_params = [{"name": "@status", "value": status.value}] if status else []
        count_result = await cosmos_client.query_items(
            container=Containers.PROFILES,
            query=count_query,
            parameters=count_params
        )
        total = count_result[0] if count_result else 0
        
        return {
            "profiles": items,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(items) < total
        }
        
    except Exception as e:
        logger.error(f"Error fetching profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}", response_model=Dict[str, Any])
async def get_profile_by_user_id(user_id: str):
    """
    Get a specific profile by user ID.
    """
    try:
        item = await cosmos_client.read_item(
            container=Containers.PROFILES,
            item_id=user_id,
            partition_key_value=user_id
        )
        
        if not item:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return item
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching profile for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{user_id}", response_model=Dict[str, Any])
async def update_profile_by_user_id(
    user_id: str,
    profile_data: Dict[str, Any] = Body(...)
):
    """
    Update a profile by user ID. Supports partial updates.
    Automatically recalculates completeness percentage and updates timestamp.
    """
    try:
        # First, fetch the existing profile
        existing_profile = await cosmos_client.read_item(
            container=Containers.PROFILES,
            item_id=user_id,
            partition_key_value=user_id
        )
        
        if not existing_profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Merge the updates with existing data
        updated_data = {**existing_profile, **profile_data}
        
        # Ensure user_id consistency
        updated_data["user_id"] = user_id
        updated_data["id"] = user_id
        
        # Update timestamp
        updated_data["updated_at"] = datetime.utcnow().isoformat()
        
        # Validate the updated profile
        try:
            validated_profile = FinancialProfile(**updated_data)
            # Convert back to dict with completeness recalculated
            # Use mode='json' to ensure datetime objects are serialized
            profile_dict = validated_profile.model_dump(mode='json', exclude_none=False)
        except Exception as validation_error:
            logger.error(f"Validation error: {validation_error}")
            raise HTTPException(
                status_code=422,
                detail=f"Invalid profile data: {str(validation_error)}"
            )
        
        # Update in Cosmos DB
        updated_item = await cosmos_client.upsert_item(
            container=Containers.PROFILES,
            item=profile_dict,
            partition_key_value=user_id
        )
        
        logger.info(f"Profile updated for user {user_id}")
        return updated_item
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/by-name", response_model=Dict[str, Any])
async def search_profiles_by_name(
    name: str,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    """
    Search profiles by first name or last name (case-insensitive partial match).
    """
    try:
        query = """
            SELECT * FROM c 
            WHERE CONTAINS(LOWER(c.personal_info.first_name), LOWER(@name))
            OR CONTAINS(LOWER(c.personal_info.last_name), LOWER(@name))
            OFFSET @offset LIMIT @limit
        """
        parameters = [
            {"name": "@name", "value": name},
            {"name": "@offset", "value": offset},
            {"name": "@limit", "value": limit}
        ]
        
        items = await cosmos_client.query_items(
            container=Containers.PROFILES,
            query=query,
            parameters=parameters
        )
        
        return {
            "profiles": items,
            "total": len(items),
            "limit": limit,
            "offset": offset,
            "search_term": name
        }
        
    except Exception as e:
        logger.error(f"Error searching profiles by name {name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/by-status", response_model=Dict[str, Any])
async def search_profiles_by_status(
    status: ProfileStatus,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    """
    Search profiles by completion status.
    """
    try:
        query = """
            SELECT * FROM c 
            WHERE c.status = @status 
            ORDER BY c.updated_at DESC
            OFFSET @offset LIMIT @limit
        """
        parameters = [
            {"name": "@status", "value": status.value},
            {"name": "@offset", "value": offset},
            {"name": "@limit", "value": limit}
        ]
        
        items = await cosmos_client.query_items(
            container=Containers.PROFILES,
            query=query,
            parameters=parameters
        )
        
        return {
            "profiles": items,
            "total": len(items),
            "limit": limit,
            "offset": offset,
            "status": status.value
        }
        
    except Exception as e:
        logger.error(f"Error searching profiles by status {status}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/by-employment", response_model=Dict[str, Any])
async def search_profiles_by_employment_status(
    employment_status: str,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    """
    Search profiles by employment status.
    """
    try:
        query = """
            SELECT * FROM c 
            WHERE c.employment.employment_status = @employment_status
            OFFSET @offset LIMIT @limit
        """
        parameters = [
            {"name": "@employment_status", "value": employment_status},
            {"name": "@offset", "value": offset},
            {"name": "@limit", "value": limit}
        ]
        
        items = await cosmos_client.query_items(
            container=Containers.PROFILES,
            query=query,
            parameters=parameters
        )
        
        return {
            "profiles": items,
            "total": len(items),
            "limit": limit,
            "offset": offset,
            "employment_status": employment_status
        }
        
    except Exception as e:
        logger.error(f"Error searching profiles by employment status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/by-net-worth-range", response_model=Dict[str, Any])
async def search_profiles_by_net_worth(
    min_net_worth: Optional[float] = None,
    max_net_worth: Optional[float] = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    """
    Search profiles by net worth range.
    """
    try:
        # Build dynamic query based on provided parameters
        conditions = []
        parameters = [
            {"name": "@offset", "value": offset},
            {"name": "@limit", "value": limit}
        ]
        
        if min_net_worth is not None:
            conditions.append("c.financial_position.net_worth >= @min_net_worth")
            parameters.append({"name": "@min_net_worth", "value": min_net_worth})
        
        if max_net_worth is not None:
            conditions.append("c.financial_position.net_worth <= @max_net_worth")
            parameters.append({"name": "@max_net_worth", "value": max_net_worth})
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT * FROM c 
            WHERE {where_clause}
            ORDER BY c.financial_position.net_worth DESC
            OFFSET @offset LIMIT @limit
        """
        
        items = await cosmos_client.query_items(
            container=Containers.PROFILES,
            query=query,
            parameters=parameters
        )
        
        return {
            "profiles": items,
            "total": len(items),
            "limit": limit,
            "offset": offset,
            "min_net_worth": min_net_worth,
            "max_net_worth": max_net_worth
        }
        
    except Exception as e:
        logger.error(f"Error searching profiles by net worth: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/by-risk-attitude", response_model=Dict[str, Any])
async def search_profiles_by_risk_attitude(
    risk_attitude: str,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    """
    Search profiles by risk attitude (very_low, low, medium, high, very_high).
    """
    try:
        query = """
            SELECT * FROM c 
            WHERE c.risk_profile.risk_attitude = @risk_attitude
            OFFSET @offset LIMIT @limit
        """
        parameters = [
            {"name": "@risk_attitude", "value": risk_attitude},
            {"name": "@offset", "value": offset},
            {"name": "@limit", "value": limit}
        ]
        
        items = await cosmos_client.query_items(
            container=Containers.PROFILES,
            query=query,
            parameters=parameters
        )
        
        return {
            "profiles": items,
            "total": len(items),
            "limit": limit,
            "offset": offset,
            "risk_attitude": risk_attitude
        }
        
    except Exception as e:
        logger.error(f"Error searching profiles by risk attitude: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/by-income-range", response_model=Dict[str, Any])
async def search_profiles_by_income(
    min_income: Optional[float] = None,
    max_income: Optional[float] = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    """
    Search profiles by total annual income range.
    """
    try:
        conditions = []
        parameters = [
            {"name": "@offset", "value": offset},
            {"name": "@limit", "value": limit}
        ]
        
        if min_income is not None:
            conditions.append("c.employment.total_annual_income >= @min_income")
            parameters.append({"name": "@min_income", "value": min_income})
        
        if max_income is not None:
            conditions.append("c.employment.total_annual_income <= @max_income")
            parameters.append({"name": "@max_income", "value": max_income})
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT * FROM c 
            WHERE {where_clause}
            ORDER BY c.employment.total_annual_income DESC
            OFFSET @offset LIMIT @limit
        """
        
        items = await cosmos_client.query_items(
            container=Containers.PROFILES,
            query=query,
            parameters=parameters
        )
        
        return {
            "profiles": items,
            "total": len(items),
            "limit": limit,
            "offset": offset,
            "min_income": min_income,
            "max_income": max_income
        }
        
    except Exception as e:
        logger.error(f"Error searching profiles by income: {e}")
        raise HTTPException(status_code=500, detail=str(e))
