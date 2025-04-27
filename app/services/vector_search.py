from typing import List, Dict, Any, Optional
import logging

from app.services.vector_db import VectorDBService
from app.core.monitoring import measure_time
from app.core.logging import app_logger

class VectorSearchService:
    """Service for searching vector database with additional functionality."""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Get singleton instance of the service."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """Initialize the vector search service."""
        # Ensure singleton pattern
        if VectorSearchService._instance is not None:
            raise RuntimeError("VectorSearchService is a singleton! Use get_instance() instead.")
        
        # Initialize vector DB service
        self.vector_db_service = VectorDBService()
        VectorSearchService._instance = self
    
    @measure_time
    async def search_context(
        self, 
        query: str, 
        conversation_id: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for relevant context using the vector database.
        
        Args:
            query: The search query text
            conversation_id: Optional conversation ID to filter results
            limit: Maximum number of results to return
            
        Returns:
            List of search results with score and payload
        """
        filter_params = {}
        if conversation_id:
            filter_params["conversation_id"] = conversation_id
        
        results = await self.vector_db_service.search_similar(
            query=query,
            filter_params=filter_params,
            limit=limit
        )
        
        app_logger.debug(f"Vector search found {len(results)} results for query: {query[:50]}...")
        return results
    
    @measure_time
    async def store_context(
        self,
        text: str,
        metadata: Dict[str, Any],
        id: Optional[str] = None
    ) -> str:
        """Store context in the vector database.
        
        Args:
            text: The text to store
            metadata: Associated metadata
            id: Optional custom ID
            
        Returns:
            ID of the stored point
        """
        return await self.vector_db_service.store_embedding(
            text=text,
            metadata=metadata,
            id=id
        ) 