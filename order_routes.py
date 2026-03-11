from fastapi import APIRouter, Depends
from models import Order
from sqlalchemy.orm import Session
from dependencies import get_session
from schemas import orderSchema

order_router  = APIRouter(prefix="/orders", tags=["orders"])

@order_router.get("/")

async def orders():
    """Order routes"""
    return {"message": "List of orders"}


@order_router.post("/order")

async def create_order(order_schema: orderSchema, session: Session = Depends(get_session)):
    new_order = Order(user=order_schema.user_id)
    session.add(new_order)
    session.commit()
    return {"message": f"Order created successfully for order id: {order_schema.user_id}"}