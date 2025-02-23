import unittest
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from trading_strategies.apis.custom_apis import router
from trading_strategies.models.custom_models import AuthConfig
from trading_strategies.logger_config import setup_logger
from fastapi import FastAPI

# Configure logging
logger = setup_logger(__name__)

# Create a FastAPI app and include the router
app = FastAPI()
app.include_router(router)

# Create a TestClient
client = TestClient(app)

@pytest.mark.asyncio
@patch("trading_strategies.apis.api_utility.query_api", new_callable=AsyncMock)
async def test_get_current_tick(mock_query_api):
    """Test the get_current_tick endpoint."""
    logger.info("Testing get_current_tick endpoint")

    # Set up what query_api should return
    mock_query_api.return_value = {"tick": 10, "period": 1, "status": "open"}

    # Call the endpoint
    response = client.get("/tick")
    # Assertions
    assert response.status_code == 200
    assert response.json() == 10 
    mock_query_api.assert_awaited_once() 

if __name__ == "__main__":
    pytest.main()
