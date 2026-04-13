"""
Fixtures compartilhadas para todos os testes.

Estratégia:
- Banco SQLite em memória com StaticPool (uma única conexão compartilhada)
- Override de `get_session` para usar o banco de memória
- Override de `verify_token` para injetar usuários fake (user normal e admin)
- Limpeza de tabelas via DELETE entre testes (dentro da mesma conexão)
"""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from main import app
from models import Base, User, Product, Order
from dependencies import get_session, verify_token
from main import bcrypt_context


# ---------------------------------------------------------------------------
# Engine em memória compartilhada (session-scoped)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def engine():
    e = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(e)
    yield e
    Base.metadata.drop_all(e)


@pytest.fixture()
def db_session(engine):
    """Sessão limpa a cada teste — remove dados das tabelas após cada um."""
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.rollback()
    # Limpa dados (FK: products → orders → users)
    session.execute(text("DELETE FROM products"))
    session.execute(text("DELETE FROM orders"))
    session.execute(text("DELETE FROM users"))
    session.commit()
    session.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(session, *, name="Test User", email="user@test.com",
               password="secret123", active=True, admin=False) -> User:
    hashed = bcrypt_context.hash(password)
    u = User(name, email, hashed, active=active, admin=admin)
    session.add(u)
    session.commit()
    session.refresh(u)
    return u


def _make_product(session, *, name="Produto A", price=10.0,
                  quantity=1, size="M") -> Product:
    p = Product(name=name, price=price, quantity=quantity, size=size)
    session.add(p)
    session.commit()
    session.refresh(p)
    return p


# ---------------------------------------------------------------------------
# Fixtures de cliente HTTP
# ---------------------------------------------------------------------------

@pytest.fixture()
def anon_client(db_session):
    """Client sem autenticação — apenas override de get_session."""
    app.dependency_overrides.clear()
    app.dependency_overrides[get_session] = lambda: (yield db_session)
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def user_client(db_session):
    """Client autenticado como usuário normal."""
    user = _make_user(db_session)
    app.dependency_overrides.clear()
    app.dependency_overrides[get_session] = lambda: (yield db_session)
    app.dependency_overrides[verify_token] = lambda: user
    yield TestClient(app), user, db_session
    app.dependency_overrides.clear()


@pytest.fixture()
def admin_client(db_session):
    """Client autenticado como administrador."""
    admin = _make_user(db_session, name="Admin", email="admin@test.com",
                       password="adminpass", admin=True)
    app.dependency_overrides.clear()
    app.dependency_overrides[get_session] = lambda: (yield db_session)
    app.dependency_overrides[verify_token] = lambda: admin
    yield TestClient(app), admin, db_session
    app.dependency_overrides.clear()
