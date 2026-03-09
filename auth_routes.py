from fastapi import APIRouter

auth_router  = APIRouter(prefix="/auth", tags=["auth"])

@auth_router.get("/")

async def auth():
    """Authentication routes"""
    return {"message": "Authentication route"}