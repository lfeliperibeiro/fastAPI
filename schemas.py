from pydantic import BaseModel
from typing import Optional

class userSchema(BaseModel):
  name: str
  email: str
  password: str
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
      name: str
      price: float
      quantity: int
      size: str

      class Config:
          from_attributes = True