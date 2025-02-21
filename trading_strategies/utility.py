import os

import httpx
from dotenv import load_dotenv
from fastapi import HTTPException
from tradingstrategies.models import AuthConfig

# Load environment variables
load_dotenv()


async def get_auth_config() -> AuthConfig:
    """Reads authentication config from environment and validates credentials."""
    server = os.getenv("SERVER_URL", "http://localhost")
    port = int(os.getenv("SERVER_PORT", 10000))
    os.getenv("USERNAME")
    os.getenv("PASSWORD")

    if credentials.username == "" or credentials.password == "":
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return AuthConfig(
        username=credentials.username,
        password=credentials.password,
        server=server,
        port=port,
    )


async def query_api(endpoint: str, auth: AuthConfig):
    """Generic function to query the trading API."""
    url = f"http://{auth.server}:{auth.port}{endpoint}"
    headers = {"Authorization": f"Basic {auth.username}:{auth.password}"}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=500, detail=f"Error querying {endpoint}: {str(e)}"
            )
