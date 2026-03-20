from pydantic import BaseModel
from typing import Optional

class userSchema(BaseModel):
  name: str
  email: str
  password: str
  confirm_password: str
  active: Optional[bool]
  admin: Optional[bool]

  class Config:
    from_attributes = True

class orderSchema(BaseModel):
  user_id: int

  class Config:
    from_attributes = True


class loginSchema(BaseModel):
  email: str
  password: str

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
    items: list[OrderProductSchema]

    class Config:
        from_attributes = True


class OrdersListResponseSchema(BaseModel):
    orders: list[ResponseOrderSchema]

    class Config:
        from_attributes = True

class OrdersListProductsResponseSchema(BaseModel):
    products: list[OrderProductSchema]

    class Config:
        from_attributes = True