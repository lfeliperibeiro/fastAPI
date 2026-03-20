import pytest
from sqlalchemy import create_engine, inspect

import models


def test_user_model_initialization():
    """Creating a User should set all attributes correctly."""
    u = models.User("Alice", "alice@example.com", "s3cr3t", active=False, admin=True)
    assert u.name == "Alice"
    assert u.email == "alice@example.com"
    assert u.password == "s3cr3t"
    assert u.active is False
    assert u.admin is True


def test_order_model_initialization():
    """Creating an Order should set fields and allow different statuses."""
    o = models.Order(user_id=42, status="Completed", price=12.50)
    assert o.user_id == 42
    assert o.status == "Completed"
    assert o.price == 12.50


def test_product_model_initialization():
    """A Product instance holds the values passed to its constructor."""
    p = models.Product("Widget", 5.0, 10, "M", order=7)
    assert p.name == "Widget"
    assert p.price == 5.0
    assert p.quantity == 10
    assert p.size == "M"
    assert p.order == 7


def test_order_status_choices():
    """The ORDER_STATUS tuple should contain the expected options."""
    assert ("Pending", "Pending") in models.Order.ORDER_STATUS
    assert ("Cancelled", "Cancelled") in models.Order.ORDER_STATUS
    assert ("Completed", "Completed") in models.Order.ORDER_STATUS


def test_metadata_creates_tables():
    """The declarative base metadata should be able to create all tables."""
    engine = create_engine("sqlite:///:memory:")
    models.Base.metadata.create_all(engine)
    insp = inspect(engine)

    names = insp.get_table_names()
    assert "users" in names
    assert "orders" in names
    assert "products" in names
