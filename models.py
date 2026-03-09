from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, ForeignKey
from sqlalchemy.orm import declarative_base
# from sqlalchemy_utils.types import ChoiceType

db = create_engine("sqlite:///banco.db")

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

class Order(Base):
    __tablename__ = "orders"

    # ORDER_STATUS = (
    #     ("Pending", "Pending"),
    #     ("Cancelled", "Cancelled"),
    #     ("Completed", "Completed"),
    # )

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    status = Column("status", String)
    user = Column("user", ForeignKey("users.id"))
    price = Column("price", Float)

    def __init__(self, user: int, status: str = "Pending", price: float = 0):
        self.user = user
        self.status = status
        self.price = price


class Product(Base):
    __tablename__ = "products"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    quantity = Column("quantity", Integer)
    size = Column("size", String)
    name = Column("name", String)
    price = Column("price", Float)
    order = Column("order", ForeignKey("orders.id"))

    def __init__(self, name: str, price: float, quantity: int, size: str, order: int):
        self.name = name
        self.price = price
        self.quantity = quantity
        self.size = size
        self.order = order