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