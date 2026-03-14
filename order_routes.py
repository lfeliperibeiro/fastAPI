from fastapi import APIRouter, Depends, HTTPException
from models import Order, User, Product
from sqlalchemy.orm import Session
from dependencies import get_session, verify_token
from schemas import orderSchema, OrderProductSchema, ResponseOrderSchema

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

@order_router.get("list")

async def list_orders(session: Session = Depends(get_session), user: User = Depends(verify_token)):
    if not user.admin:
        raise HTTPException(status_code=403, detail="You do not have permission to view the list of orders")
    else:
        orders = session.query(Order).all()
        return {"orders": orders}


@order_router.post("/order/add_product/{order_id}")

async def add_product_to_order(order_id: int,
                               product_schema: OrderProductSchema,
                               session: Session = Depends(get_session),
                               user: User = Depends(verify_token)):
    order = session.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if not user.admin and user.id != order.user:
        raise HTTPException(status_code=403, detail="You do not have permission to add products to this order")
    product = Product(name=product_schema.name,
                      price=product_schema.price,
                      quantity=product_schema.quantity,
                      size=product_schema.size,
                      order=order_id)

    session.add(product)
    order.calculate_price()
    session.commit()

    return {
        "message": f"Product added successfully to order id: {order_id}",
        "order_id": order_id,
        "price": product.price,
        "total_price": order.price
        }

@order_router.post("/order/remove_product/{product_id}")

async def remove_product_from_order(product_id: int,
                                   session: Session = Depends(get_session),
                                   user: User = Depends(verify_token)):
    product = session.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    order = session.query(Order).filter(Order.id == product.order).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if not user.admin and user.id != order.user:
        raise HTTPException(status_code=403, detail="You do not have permission to remove products from this order")

    session.delete(product)
    order.calculate_price()
    session.commit()

    return {
        "message": f"Product removed successfully from order id: {order.id}",
        "quantity": len(order.items),
        "order": order.items,
    }


@order_router.post("/order/finished/{order_id}")

async def finished_order(order_id: int, session: Session = Depends(get_session), user: User = Depends(verify_token)):
    order = session.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if not user.admin and user.id != order.user:
        raise HTTPException(status_code=403, detail="You do not have permission to cancel this order")

    order.status = "Finished"
    session.commit()

    return {
        "message": f"Order finished successfully for order id: {order.id}",
        "order": order
      }

@order_router.get("/order/{order_id}")

async def get_order(order_id: int, session: Session = Depends(get_session), user: User = Depends(verify_token)):
    order = session.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if not user.admin and user.id != order.user:
        raise HTTPException(status_code=403, detail="You do not have permission to view this order")

    return {
        "quantity": len(order.items),
        "order": order
    }

@order_router.get("/list_order/order_user", response_model=list[ResponseOrderSchema])

async def list_orders_by_user(session: Session = Depends(get_session), user: User = Depends(verify_token)):
    orders = session.query(Order).filter(Order.user == user.id).all()
    return orders