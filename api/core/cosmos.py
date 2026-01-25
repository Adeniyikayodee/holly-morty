from azure.cosmos import CosmosClient, PartitionKey, exceptions
from typing import Optional, Dict, Any
from enum import Enum
import logging

from core.config import settings

logger = logging.getLogger(__name__)


class ContainerConfig:
    """Configuration for a Cosmos DB container"""
    def __init__(self, name: str, partition_key: str):
        self.name = name
        self.partition_key = partition_key


class Containers(str, Enum):
    """Enum of available containers"""
    CONVERSATIONS = "conversations"
    PROFILES = "profiles"
    INSIGHTS = "insights"


# Container configurations with partition keys
CONTAINER_CONFIGS = {
    Containers.CONVERSATIONS: ContainerConfig(
        name="conversations",
        partition_key="/conversation_id"
    ),
    Containers.PROFILES: ContainerConfig(
        name="profiles",
        partition_key="/user_id"
    ),
    Containers.INSIGHTS: ContainerConfig(
        name="insights",
        partition_key="/user_id"
    ),
}


class CosmosDBClient:
    """Singleton Cosmos DB client for managing multiple containers"""
    
    _instance: Optional["CosmosDBClient"] = None
    _client: Optional[CosmosClient] = None
    _database = None
    _containers: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Cosmos DB client (only once)"""
        if self._client is None and settings.cosmos_connection_string:
            try:
                self._client = CosmosClient.from_connection_string(
                    settings.cosmos_connection_string
                )
                logger.info("Cosmos DB client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Cosmos DB client: {e}")
                raise
    
    async def initialize_containers(self):
        """Create database and all configured containers if they don't exist"""
        if not self._client:
            logger.warning("Cosmos DB client not initialized - connection string not provided")
            return
        
        try:
            # Create database if it doesn't exist
            self._database = self._client.create_database_if_not_exists(
                id=settings.cosmos_database_name
            )
            logger.info(f"Database '{settings.cosmos_database_name}' ready")
            
            # Create all configured containers
            for container_enum, config in CONTAINER_CONFIGS.items():
                container = self._database.create_container_if_not_exists(
                    id=config.name,
                    partition_key=PartitionKey(path=config.partition_key)
                )
                self._containers[container_enum] = container
                logger.info(f"Container '{config.name}' ready (partition key: {config.partition_key})")
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to initialize Cosmos DB containers: {e}")
            raise
    
    def get_container(self, container: Containers):
        """Get a specific container by enum"""
        if container not in self._containers:
            logger.warning(f"Container {container} not initialized")
            return None
        return self._containers[container]
    
    async def create_item(
        self, 
        container: Containers, 
        item: Dict[str, Any], 
        partition_key_value: str
    ) -> Dict[str, Any]:
        """
        Create an item in the specified container
        
        Args:
            container: The container enum to use
            item: The item data to create
            partition_key_value: The value for the partition key
            
        Returns:
            The created item
        """
        container_client = self.get_container(container)
        if not container_client:
            logger.warning(f"Container {container} not initialized - skipping creation")
            return item
        
        try:
            config = CONTAINER_CONFIGS[container]
            # Extract partition key field name (e.g., "/user_id" -> "user_id")
            pk_field = config.partition_key.lstrip("/")
            
            # Ensure id and partition key are set
            item_with_keys = {
                "id": item.get("id", partition_key_value),
                pk_field: partition_key_value,
                **item
            }
            
            created_item = container_client.create_item(body=item_with_keys)
            logger.info(f"Created item in {container}: {item_with_keys.get('id')}")
            return created_item
            
        except exceptions.CosmosResourceExistsError:
            logger.warning(f"Item {item.get('id')} already exists in {container}")
            return await self.upsert_item(container, item, partition_key_value)
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to create item in {container}: {e}")
            raise
    
    async def upsert_item(
        self, 
        container: Containers, 
        item: Dict[str, Any], 
        partition_key_value: str
    ) -> Dict[str, Any]:
        """
        Upsert (create or update) an item in the specified container
        
        Args:
            container: The container enum to use
            item: The item data to upsert
            partition_key_value: The value for the partition key
            
        Returns:
            The upserted item
        """
        container_client = self.get_container(container)
        if not container_client:
            logger.warning(f"Container {container} not initialized - skipping upsert")
            return item
        
        try:
            config = CONTAINER_CONFIGS[container]
            pk_field = config.partition_key.lstrip("/")
            
            item_with_keys = {
                "id": item.get("id", partition_key_value),
                pk_field: partition_key_value,
                **item
            }
            
            upserted_item = container_client.upsert_item(body=item_with_keys)
            logger.info(f"Upserted item in {container}: {item_with_keys.get('id')}")
            return upserted_item
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to upsert item in {container}: {e}")
            raise
    
    async def read_item(
        self, 
        container: Containers, 
        item_id: str, 
        partition_key_value: str
    ) -> Optional[Dict[str, Any]]:
        """
        Read an item from the specified container
        
        Args:
            container: The container enum to use
            item_id: The item ID to read
            partition_key_value: The partition key value
            
        Returns:
            The item data or None if not found
        """
        container_client = self.get_container(container)
        if not container_client:
            logger.warning(f"Container {container} not initialized")
            return None
        
        try:
            item = container_client.read_item(
                item=item_id,
                partition_key=partition_key_value
            )
            return item
        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"Item {item_id} not found in {container}")
            return None
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to read item from {container}: {e}")
            raise
    
    async def query_items(
        self, 
        container: Containers, 
        query: str, 
        parameters: Optional[list] = None,
        partition_key_value: Optional[str] = None
    ) -> list:
        """
        Query items from the specified container
        
        Args:
            container: The container enum to use
            query: SQL query string
            parameters: Query parameters
            partition_key_value: Optional partition key for cross-partition queries
            
        Returns:
            List of matching items
        """
        container_client = self.get_container(container)
        if not container_client:
            logger.warning(f"Container {container} not initialized")
            return []
        
        try:
            query_params = {
                "query": query,
                "parameters": parameters or []
            }
            
            if partition_key_value:
                items = list(container_client.query_items(
                    **query_params,
                    partition_key=partition_key_value
                ))
            else:
                items = list(container_client.query_items(
                    **query_params,
                    enable_cross_partition_query=True
                ))
            
            return items
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to query items from {container}: {e}")
            raise
    
    @property
    def is_initialized(self) -> bool:
        """Check if Cosmos DB client is initialized"""
        return len(self._containers) > 0


# Global instance
cosmos_client = CosmosDBClient()
