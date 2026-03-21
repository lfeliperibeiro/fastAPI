from datetime import datetime, timezone

from sqlalchemy import create_engine, Column, DateTime, Integer, String, Boolean, Float, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

db = create_engine("sqlite:///database.db")

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column("id", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String)
    email = Column("email", String, nullable=False)
    password = Column("password", String)
    active = Column("active", Boolean)
    admin = Column("admin", Boolean, default=False)

    def __init__(self, name: str, email: str, password: str, active: bool = True, admin: bool = False):
        self.name = name
        self.email = email
        self.password = password
        self.active = active
        self.admin = admin

    orders = relationship("Order", back_populates="user")

class Order(Base):
    __tablename__ = "orders"

    ORDER_STATUS = (
        ("Pending", "Pending"),
        ("Cancelled", "Cancelled"),
        ("Completed", "Completed"),
    )

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    status = Column("status", String)
    user_id = Column("user", Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="orders")
    price = Column("price", Float)
    created_at = Column("created_at", DateTime, default=lambda: datetime.now(timezone.utc))
    items = relationship("Product", cascade="all, delete")

    @property
    def user_name(self) -> str | None:
        return self.user.name if self.user is not None else None

    def __init__(self, user_id: int, status: str = "Pending", price: float = 0):
        self.user_id = user_id
        self.status = status
        self.price = price
        self.created_at = datetime.now(timezone.utc)

    def calculate_price(self):
        self.price = sum(item.price * item.quantity for item in self.items)


class Product(Base):
    __tablename__ = "products"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    quantity = Column("quantity", Integer)
    size = Column("size", String)
    name = Column("name", String)
    price = Column("price", Float)
    order = Column("order", ForeignKey("orders.id"))

    def __init__(
        self,
        name: str,
        price: float,
        quantity: int = 1,
        size: str = "",
        order: int | None = None,
    ):
        self.name = name
        self.price = price
        self.quantity = quantity
        self.size = size
        self.order = order