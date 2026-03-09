from fastapi import APIRouter

order_router  = APIRouter(prefix="/orders", tags=["orders"])

@order_router.get("/")

async def orders():
    """Order routes"""
    return {"message": "List of orders"}