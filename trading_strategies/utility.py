import base64
import os

import httpx
from dotenv import load_dotenv
from fastapi import HTTPException

from trading_strategies.custom_models import AuthConfig

# Load environment variables
load_dotenv()


def get_auth_config() -> AuthConfig:
    """Reads authentication config from environment and validates credentials."""
    server = os.getenv("SERVER", "http://localhost")
    port = int(os.getenv("PORT"))
    username = os.getenv("USERNAME")
    password = os.getenv("PASSWORD")

    # Check if credentials are provided
    if not username or not password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Check if port is within valid range (1-65535)
    if not (1 <= port <= 65535):
        raise HTTPException(status_code=400, detail="Invalid port number")

    return AuthConfig(
        username=username,
        password=password,
        server=server,
        port=port,
    )


from typing import Any, Dict, Optional


async def query_api(
    method: str,
    endpoint: str,
    auth: AuthConfig,
    params: Optional[Dict[str, Any]] = None,
    json: Optional[Dict[str, Any]] = None,
) -> Any:
    """Generic function to query the trading API with different HTTP methods."""

    url = f"http://{auth.server}:{auth.port}{endpoint}"
    auth_str = f"{auth.username}:{auth.password}"
    encoded_auth = base64.b64encode(auth_str.encode()).decode()
    headers = {"accept": "application/json", "authorization": f"Basic {encoded_auth}"}

    async with httpx.AsyncClient() as client:
        try:
            if method.lower() == "get":
                response = await client.get(url, headers=headers, params=params)
            elif method.lower() == "post":
                response = await client.post(url, headers=headers, json=json)
            elif method.lower() == "delete":
                response = await client.delete(url, headers=headers, json=json)
            elif method.lower() == "put":
                response = await client.put(url, headers=headers, json=json)
            else:
                raise ValueError("Unsupported HTTP method.")

            response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
            return response.json()
        except httpx.RequestError as e:
            print(f"Request error: {str(e)}")  # Log the request error
            raise HTTPException(
                status_code=500, detail=f"Error querying {endpoint}: {str(e)}"
            )
        except httpx.HTTPStatusError as e:
            print(f"HTTP error: {str(e)}")  # Log the HTTP error
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Error querying {endpoint}: {str(e)}",
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
