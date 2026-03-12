from fastapi import APIRouter, Depends, HTTPException
from models import Order, User
from sqlalchemy.orm import Session
from dependencies import get_session, verify_token
from schemas import orderSchema

order_router  = APIRouter(prefix="/orders", tags=["orders"], dependencies=[Depends(verify_token)])

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


@order_router.post("/order/cancel/{order_id}")

async def cancel_order(order_id: int, session: Session = Depends(get_session), user: User = Depends(verify_token)):
    order = session.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if not user.admin and user.id != order.user:
        raise HTTPException(status_code=403, detail="You do not have permission to cancel this order")

    order.status = "Cancelled"
    session.commit()

    return {
        "message": f"Order cancelled successfully for order id: {order.id}",
        "order": order
      }