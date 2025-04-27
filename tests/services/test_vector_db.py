import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.vector_db import VectorDBService


@pytest.fixture
def mock_qdrant_client():
    client = MagicMock()
    client.upsert = MagicMock()
    client.search = MagicMock()
    client.get_collections = MagicMock()
    return client


@pytest.fixture
def mock_openai_embeddings():
    embeddings = MagicMock()
    embeddings.embed_query = MagicMock(return_value=[0.1] * 1536)
    return embeddings


@pytest.fixture
def vector_db_service(mock_qdrant_client, mock_openai_embeddings):
    with patch('app.services.vector_db.QdrantClient', return_value=mock_qdrant_client), \
         patch('app.services.vector_db.OpenAIEmbeddings', return_value=mock_openai_embeddings):
        
        # Create a fresh instance
        VectorDBService._instance = None
        service = VectorDBService()
        
        # Mock the _ensure_collection_exists method
        service._ensure_collection_exists = MagicMock()
        
        yield service


@pytest.mark.asyncio
async def test_store_embedding_with_uuid_string(vector_db_service):
    """Test storing embedding with UUID string ID."""
    uuid_str = str(uuid.uuid4())
    
    result = await vector_db_service.store_embedding(
        text="Test embedding", 
        metadata={"test": "value"},
        id=uuid_str
    )
    
    # Verify the ID was used correctly
    assert result == uuid_str
    vector_db_service.client.upsert.assert_called_once()
    # Extract the ID that was passed to upsert
    call_args = vector_db_service.client.upsert.call_args[1]
    points = call_args.get('points', [])
    assert len(points) == 1
    assert points[0].id == uuid_str


@pytest.mark.asyncio
async def test_store_embedding_with_numeric_id(vector_db_service):
    """Test storing embedding with numeric ID (should be converted to UUID)."""
    numeric_id = "123"
    
    result = await vector_db_service.store_embedding(
        text="Test embedding", 
        metadata={"test": "value"},
        id=numeric_id
    )
    
    # Verify the ID was converted to UUID
    assert result != numeric_id
    assert uuid.UUID(result)  # Should be valid UUID
    
    vector_db_service.client.upsert.assert_called_once()
    # Extract the ID that was passed to upsert
    call_args = vector_db_service.client.upsert.call_args[1]
    points = call_args.get('points', [])
    assert len(points) == 1
    assert points[0].id != numeric_id
    # Verify it's a valid UUID
    uuid.UUID(points[0].id)


@pytest.mark.asyncio
async def test_store_embedding_with_invalid_id(vector_db_service):
    """Test storing embedding with an invalid ID (should be converted to UUID)."""
    invalid_id = "not a uuid or number"
    
    result = await vector_db_service.store_embedding(
        text="Test embedding", 
        metadata={"test": "value"},
        id=invalid_id
    )
    
    # Verify the ID was converted to UUID
    assert result != invalid_id
    assert uuid.UUID(result)  # Should be valid UUID
    
    vector_db_service.client.upsert.assert_called_once()
    # Extract the ID that was passed to upsert
    call_args = vector_db_service.client.upsert.call_args[1]
    points = call_args.get('points', [])
    assert len(points) == 1
    assert points[0].id != invalid_id
    # Verify it's a valid UUID
    uuid.UUID(points[0].id)


@pytest.mark.asyncio
async def test_store_embedding_with_no_id(vector_db_service):
    """Test storing embedding with no ID provided (should generate UUID)."""
    result = await vector_db_service.store_embedding(
        text="Test embedding", 
        metadata={"test": "value"},
        id=None
    )
    
    # Verify a UUID was generated
    assert result is not None
    assert uuid.UUID(result)  # Should be valid UUID
    
    vector_db_service.client.upsert.assert_called_once()
    # Extract the ID that was passed to upsert
    call_args = vector_db_service.client.upsert.call_args[1]
    points = call_args.get('points', [])
    assert len(points) == 1
    # Verify it's a valid UUID
    uuid.UUID(points[0].id)


@pytest.mark.asyncio
async def test_store_embedding_with_exception(vector_db_service):
    """Test handling exception when storing embedding."""
    # Make the upsert method raise an exception
    vector_db_service.client.upsert.side_effect = Exception("Test exception")
    
    # Should not raise but return a fallback ID
    result = await vector_db_service.store_embedding(
        text="Test embedding", 
        metadata={"test": "value"}
    )
    
    # Verify a fallback ID was returned
    assert result is not None
    assert result.startswith("fallback-")
    
    # Verify upsert was called
    vector_db_service.client.upsert.assert_called_once() 