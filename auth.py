import os
from fastapi import Header, HTTPException, status

DEMO_API_KEY = os.getenv("DEMO_API_KEY", "demo-demo-key")

async def require_demo_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    """
    Very simple API-key checker used ONLY for /demo/* endpoints.
    Does not affect the existing supervisor-integrated endpoints.
    """
    if x_api_key != DEMO_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing demo API key",
        )
