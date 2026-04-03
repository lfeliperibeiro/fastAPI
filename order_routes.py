from fastapi import APIRouter, Depends, HTTPException
from models import Order, User, Product
from sqlalchemy.orm import Session, joinedload
from dependencies import get_session, verify_token
from schemas import (
    orderSchema,
    ProductCreateSchema,
    ResponseOrderSchema,
    AdminOrderResponseSchema,
    OrderProductSummarySchema,
)

order_router  = APIRouter(prefix="/orders", tags=["orders"], dependencies=[Depends(verify_token)])

@order_router.get("/")

async def orders():
    """Order routes"""
    return {"message": "List of orders"}


@order_router.post("/order")

async def create_order(order_schema: orderSchema, session: Session = Depends(get_session)):
    if not order_schema.products:
        raise HTTPException(status_code=400, detail="At least one product is required")

    new_order = Order(
        user_id=order_schema.user_id,
        notes=order_schema.notes,
        payment_method=order_schema.payment_method,
    )
    session.add(new_order)
    session.flush()

    linked_products = []
    for item in order_schema.products:
        if item.quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be greater than zero")
        product = session.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product not found: {item.product_id}")
        product.order = new_order.id
        product.quantity = item.quantity
        linked_products.append({"product_id": product.id, "quantity": product.quantity})

    new_order.calculate_price()

    session.commit()
    session.refresh(new_order)
    return {
        "message": f"Order created successfully for order id: {new_order.id}",
        "order_id": new_order.id,
        "products": linked_products,
        "total_price": new_order.price,
        "status": new_order.status,
        "created_at": new_order.created_at.isoformat() if new_order.created_at else None,
        "notes": new_order.notes,
        "payment_method": new_order.payment_method,
    }


@order_router.put("/order/edit/{order_id}")

async def edit_order(
    order_id: int,
    order_schema: orderSchema,
    session: Session = Depends(get_session),
    user: User = Depends(verify_token),
):
    if not order_schema.products:
        raise HTTPException(status_code=400, detail="At least one product is required")

    order = session.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if not user.admin and user.id != order.user_id:
        raise HTTPException(status_code=403, detail="You do not have permission to edit this order")

    current_products = session.query(Product).filter(Product.order == order.id).all()
    for current in current_products:
        current.order = None
        current.quantity = 1

    linked_products = []
    for item in order_schema.products:
        if item.quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be greater than zero")
        product = session.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product not found: {item.product_id}")
        product.order = order.id
        product.quantity = item.quantity
        linked_products.append({"product_id": product.id, "quantity": product.quantity})

    order.user_id = order_schema.user_id
    order.notes = order_schema.notes
    order.payment_method = order_schema.payment_method
    order.calculate_price()

    session.commit()
    session.refresh(order)
    return {
        "message": f"Order updated successfully for order id: {order.id}",
        "order_id": order.id,
        "products": linked_products,
        "total_price": order.price,
        "status": order.status,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "notes": order.notes,
        "payment_method": order.payment_method,
    }


@order_router.post("/order/cancel/{order_id}")

async def cancel_order(order_id: int, session: Session = Depends(get_session), user: User = Depends(verify_token)):
    order = session.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if not user.admin and user.id != order.user_id:
        raise HTTPException(status_code=403, detail="You do not have permission to cancel this order")

    order.status = "Cancelled"
    session.commit()

    return {
        "message": f"Order cancelled successfully for order id: {order.id}",
        "order_id": order.id,
        "status": order.status,
    }

@order_router.get("/list", response_model=list[OrderProductSummarySchema])

async def list_orders(session: Session = Depends(get_session), user: User = Depends(verify_token)):
    if not user.admin:
        raise HTTPException(status_code=403, detail="You do not have permission to view the list of orders")

    products = session.query(Product).all()
    return [
        {"product_id": p.id, "name": p.name, "price": p.price, "size": p.size}
        for p in products
    ]


@order_router.post("/order/add_product")

async def add_product_to_order(product_schema: ProductCreateSchema,
                               session: Session = Depends(get_session),
                               user: User = Depends(verify_token)):
    product = Product(
        name=product_schema.name,
        price=product_schema.price,
        size=product_schema.size,
    )

    session.add(product)
    session.commit()
    session.refresh(product)

    return {
        "message": "Product created successfully",
        "product_id": product.id,
        "price": product.price,
    }

@order_router.post("/order/remove_product/{product_id}")

async def remove_product_from_order(product_id: int,
                                   session: Session = Depends(get_session),
                                   user: User = Depends(verify_token)):
    product = session.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    session.delete(product)
    session.commit()

    return {
        "message": f"Product removed successfully for product id: {product_id}",
    }


@order_router.post("/order/finished/{order_id}")

async def finished_order(order_id: int, session: Session = Depends(get_session), user: User = Depends(verify_token)):
    order = session.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if not user.admin and user.id != order.user_id:
        raise HTTPException(status_code=403, detail="You do not have permission to cancel this order")

    order.status = "Finished"
    session.commit()

    return {
        "message": f"Order finished successfully for order id: {order.id}",
        "order_id": order.id,
        "status": order.status,
    }

@order_router.get("/order/{order_id}")

async def get_order(order_id: int, session: Session = Depends(get_session), user: User = Depends(verify_token)):
    order = session.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if not user.admin and user.id != order.user_id:
        raise HTTPException(status_code=403, detail="You do not have permission to view this order")

    return {
        "quantity": len(order.items),
        "order": order
    }

@order_router.get("/list_order/order_user", response_model=list[AdminOrderResponseSchema])

async def list_orders_by_user(session: Session = Depends(get_session), user: User = Depends(verify_token)):
    orders = (
        session.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.user_id == user.id)
        .all()
    )
    return [
        {
            "order_id": order.id,
            "products": [{"product_id": p.id, "quantity": p.quantity} for p in order.items],
            "total_price": order.price,
            "status": order.status,
            "created_at": order.created_at,
            "notes": order.notes,
            "payment_method": order.payment_method,
        }
        for order in orders
    ]