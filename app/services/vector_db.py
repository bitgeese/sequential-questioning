from typing import List, Dict, Any, Optional, Union
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain_openai import OpenAIEmbeddings
import os
import time
import httpx
import uuid

from app.core.config import get_settings
from app.core.logging import app_logger
from app.core.monitoring import measure_time

settings = get_settings()


class VectorDBService:
    """Service for interacting with Qdrant vector database."""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one vector db service instance."""
        if cls._instance is None:
            cls._instance = super(VectorDBService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize Qdrant client and OpenAI embeddings."""
        # Get the Qdrant URL from environment or use host:port if not available
        qdrant_url = os.getenv("QDRANT_URL", None)
        
        if qdrant_url:
            # Initialize with URL
            app_logger.info(f"Connecting to Qdrant using URL: {qdrant_url}")
            self.client = QdrantClient(url=qdrant_url)
        else:
            # Initialize with host and port
            app_logger.info(f"Connecting to Qdrant using Host: {settings.QDRANT_HOST}, Port: {settings.QDRANT_PORT}")
            self.client = QdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT
            )
        
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self.embeddings = OpenAIEmbeddings(
            api_key=settings.OPENAI_API_KEY
        )
        
        # Try to ensure collection exists with retry
        self._ensure_collection_exists_with_retry()
        
        app_logger.info(f"Vector DB service initialized with collection '{self.collection_name}'")
    
    def _ensure_collection_exists_with_retry(self, max_retries=5, retry_delay=2):
        """Create the collection if it doesn't exist, with retry logic."""
        retries = 0
        while retries < max_retries:
            try:
                self._ensure_collection_exists()
                return
            except (httpx.ConnectError, httpx.ConnectTimeout) as e:
                retries += 1
                app_logger.warning(f"Failed to connect to Qdrant (attempt {retries}/{max_retries}): {str(e)}")
                if retries < max_retries:
                    app_logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 1.5  # Exponential backoff
                else:
                    app_logger.error(f"Failed to connect to Qdrant after {max_retries} attempts.")
                    # Continue without vector DB functionality
                    app_logger.warning("Application will continue without vector database functionality.")
                    break
    
    def _ensure_collection_exists(self):
        """Create the collection if it doesn't exist."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [collection.name for collection in collections]
            
            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=1536,  # OpenAI embeddings dimension
                        distance=models.Distance.COSINE
                    )
                )
                app_logger.info(f"Created new collection '{self.collection_name}' in Qdrant")
        except Exception as e:
            app_logger.error(f"Error ensuring collection exists: {str(e)}")
            raise
    
    @measure_time
    async def store_embedding(
        self, 
        text: str, 
        metadata: Dict[str, Any], 
        id: Optional[str] = None
    ) -> str:
        """Store a text embedding in the vector database.
        
        Args:
            text: The text to embed and store
            metadata: Associated metadata for the embedding
            id: Optional custom ID for the point
            
        Returns:
            ID of the stored point
        """
        try:
            # Generate embedding
            embedding = await self._get_embedding(text)
            
            # Use provided ID or generate a proper UUID
            # Always ensure the ID is a UUID string format regardless of input
            if id is not None:
                # Try to convert the ID to UUID if it's not already
                try:
                    # If it's a numeric ID or other non-UUID format, create a new UUID
                    if not (id.startswith('{') and id.endswith('}') or '-' in id):
                        point_id = str(uuid.uuid4())
                    else:
                        # If it looks like a UUID, ensure it's properly formatted
                        point_id = str(uuid.UUID(id))
                except (ValueError, AttributeError, TypeError):
                    # If conversion fails, generate a new UUID
                    point_id = str(uuid.uuid4())
            else:
                # Generate a new UUID if none provided
                point_id = str(uuid.uuid4())
            
            # Upsert the point
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload=metadata
                    )
                ]
            )
            
            app_logger.debug(f"Stored embedding with ID {point_id} in collection '{self.collection_name}'")
            return point_id
        except Exception as e:
            app_logger.error(f"Error storing embedding: {str(e)}")
            raw_response = getattr(e, "response", None)
            if raw_response:
                app_logger.error(f"Raw response content:\n{raw_response.content}")
            # Continue execution even if embedding storage fails
            # Return a fallback ID if we can't store the embedding
            return id if id is not None else f"fallback-{str(uuid.uuid4())}"
    
    @measure_time
    async def search_similar(
        self, 
        query: str, 
        filter_params: Optional[Dict[str, Any]] = None, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar embeddings in the vector database.
        
        Args:
            query: The query text to search for
            filter_params: Optional filter parameters for search
            limit: Maximum number of results to return
            
        Returns:
            List of search results with score and payload
        """
        try:
            # Generate embedding for query
            query_embedding = await self._get_embedding(query)
            
            # Prepare search filter
            search_filter = None
            if filter_params:
                search_filter = models.Filter(
                    must=[
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value)
                        )
                        for key, value in filter_params.items()
                    ]
                )
            
            # Perform search
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                query_filter=search_filter
            )
            
            # Format results
            results = []
            for result in search_results:
                results.append({
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload
                })
            
            app_logger.debug(f"Found {len(results)} similar embeddings for query in '{self.collection_name}'")
            return results
        except Exception as e:
            app_logger.error(f"Error searching similar embeddings: {str(e)}")
            # Return empty results if search fails
            return []
    
    async def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using OpenAI.
        
        Args:
            text: The text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        try:
            return self.embeddings.embed_query(text)
        except Exception as e:
            app_logger.error(f"Error generating embedding: {str(e)}")
            # Return a zero embedding as fallback
            return [0.0] * 1536  # OpenAI embeddings are 1536-dimensional


# Create vector db service instance
vector_db_service = VectorDBService() 