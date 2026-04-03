from datetime import datetime
from typing import Optional

from pydantic import BaseModel

class userSchema(BaseModel):
  name: str
  email: str
  password: str
  confirm_password: str
  active: Optional[bool]
  admin: Optional[bool]

  class Config:
    from_attributes = True

class UserSchema(BaseModel):
  id: int
  name: str
  email: str
  active: bool
  admin: bool

  class Config:
    from_attributes = True


class UsersListResponseSchema(BaseModel):
  users: list[UserSchema]

  class Config:
    from_attributes = True

class OrderItemInputSchema(BaseModel):
  product_id: int
  quantity: int

  class Config:
    from_attributes = True


class orderSchema(BaseModel):
  user_id: int
  products: list[OrderItemInputSchema]
  notes: Optional[str] = None
  payment_method: Optional[str] = None

  class Config:
    from_attributes = True


class loginSchema(BaseModel):
  email: str
  password: str

  class Config:
    from_attributes = True


class ForgotPasswordSchema(BaseModel):
  email: str

  class Config:
    from_attributes = True


class ResetPasswordSchema(BaseModel):
  token: str
  password: str
  confirm_password: str

  class Config:
    from_attributes = True


class OrderProductSchema(BaseModel):
      id: int
      name: str
      price: float
      quantity: int
      size: str

      class Config:
          from_attributes = True


class ProductListSchema(BaseModel):
    id: int
    name: str
    price: float
    size: str

    class Config:
        from_attributes = True


class ProductCreateSchema(BaseModel):
    name: str
    price: float
    size: str

    class Config:
        from_attributes = True

class ResponseUserSchema(BaseModel):
    name: str

    class Config:
        from_attributes = True


class ResponseOrderSchema(BaseModel):
    id: int
    status: str
    user: Optional[ResponseUserSchema] = None
    user_name: str | None
    price: float
    created_at: Optional[datetime] = None
    items: list[OrderProductSchema]

    class Config:
        from_attributes = True


class OrdersListResponseSchema(BaseModel):
    orders: list[ResponseOrderSchema]

    class Config:
        from_attributes = True

class OrdersListProductsResponseSchema(BaseModel):
    products: list[ProductListSchema]

    class Config:
        from_attributes = True


class OrderListProductItemSchema(BaseModel):
    product_id: int
    quantity: int

    class Config:
        from_attributes = True


class AdminOrderResponseSchema(BaseModel):
    order_id: int
    products: list[OrderListProductItemSchema]
    total_price: float
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    notes: Optional[str] = None
    payment_method: Optional[str] = None


class OrderProductSummarySchema(BaseModel):
    product_id: int
    name: str
    price: float
    size: str

    class Config:
        from_attributes = True


class AdminOrderListSchema(BaseModel):
    products: list[OrderProductSummarySchema]

    class Config:
        from_attributes = True

    class Config:
        from_attributes = True

class UpdateUserSchema(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    active: Optional[bool] = None
    admin: Optional[bool] = None

    class Config:
        from_attributes = True