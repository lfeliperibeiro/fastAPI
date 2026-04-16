# HTTP-Only Cookies Authentication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrar a autenticação JWT de tokens no body/header `Authorization: Bearer` para cookies HTTP-only inacessíveis ao JavaScript.

**Architecture:** Login e token endpoints definem cookies `access_token` e `refresh_token` via `response.set_cookie`. O `verify_token` em `dependencies.py` lê o cookie `access_token` em vez do header `Authorization`. O endpoint `/refresh` lê o cookie `refresh_token` diretamente. Um novo endpoint `/logout` apaga ambos os cookies.

**Tech Stack:** FastAPI, python-jose (JWT), SQLAlchemy, pytest + starlette TestClient

---

## Arquivos modificados

| Arquivo | Tipo | O que muda |
|---|---|---|
| `main.py` | Modificar | Remove `OAuth2PasswordBearer` / `oauth2_scheme`; restringe CORS |
| `dependencies.py` | Modificar | `verify_token` lê `access_token` de `request.cookies` |
| `auth_routes.py` | Modificar | `/login` e `/token` definem cookies; `/refresh` lê cookie; novo `/logout` |
| `tests/test_auth_routes.py` | Modificar | Atualiza testes de login/refresh; adiciona testes de cookie e logout |

`conftest.py`, `users_routes.py`, `order_routes.py` e os testes deles **não mudam** — todos usam `app.dependency_overrides[verify_token]` que bypassa a implementação.

---

## Task 1: Atualizar verify_token para ler cookie access_token

**Files:**
- Modify: `tests/test_auth_routes.py`
- Modify: `main.py`
- Modify: `dependencies.py`

- [ ] **Step 1: Adicionar testes que vão falhar**

Em `tests/test_auth_routes.py`, adicionar ao final do arquivo (após os testes de reset-password):

```python
# ---------------------------------------------------------------------------
# verify_token via cookie
# ---------------------------------------------------------------------------

def test_verify_token_missing_cookie_returns_401(anon_client):
    """Rota protegida sem cookie deve retornar 401."""
    response = anon_client.get("/users/users")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_verify_token_valid_cookie_passes(anon_client, db_session):
    """Rota protegida com cookie access_token válido deve retornar 200."""
    user = _make_user(db_session, email="cookieuser@example.com")
    token = create_token(user.id)
    anon_client.cookies.set("access_token", token)
    response = anon_client.get("/users/users")
    assert response.status_code == 200
    anon_client.cookies.clear()
```

- [ ] **Step 2: Rodar os testes e confirmar falha**

```bash
cd /Users/feliperibeiro/www/fast-api && uv run pytest tests/test_auth_routes.py::test_verify_token_valid_cookie_passes -v
```

Esperado: `FAILED` — o `verify_token` atual exige `Authorization: Bearer`, não cookie.

- [ ] **Step 3: Atualizar main.py — remover oauth2_scheme e restringir CORS**

Substituir o conteúdo completo de `main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from dotenv import load_dotenv
import os
import bcrypt

_root = Path(__file__).resolve().parent
load_dotenv(_root / ".env.example")
load_dotenv(_root / ".env", override=True)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class BcryptContext:
    def hash(self, password: str) -> str:
        pwd_bytes = password.encode('utf-8')[:72]
        return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode('utf-8')

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        pwd_bytes = plain_password.encode('utf-8')[:72]
        return bcrypt.checkpw(pwd_bytes, hashed_password.encode('utf-8'))

bcrypt_context = BcryptContext()

from auth_routes import auth_router
from order_routes import order_router
from users_routes import users_router

app.include_router(auth_router)
app.include_router(order_router)
app.include_router(users_router)
```

- [ ] **Step 4: Atualizar dependencies.py — verify_token lê cookie**

Substituir o conteúdo completo de `dependencies.py`:

```python
from models import db
from sqlalchemy.orm import sessionmaker, Session
from fastapi import Depends, HTTPException, Request
from models import User
from jose import JWTError, jwt
from main import SECRET_KEY, ALGORITHM


def get_session():
    try:
        Session = sessionmaker(bind=db)
        session = Session()
        yield session
    finally:
        session.close()


def verify_token(request: Request, session: Session = Depends(get_session)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        dict_info = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(dict_info.get("sub"))
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
```

- [ ] **Step 5: Rodar os novos testes e confirmar que passam**

```bash
uv run pytest tests/test_auth_routes.py::test_verify_token_missing_cookie_returns_401 tests/test_auth_routes.py::test_verify_token_valid_cookie_passes -v
```

Esperado: `2 passed`

- [ ] **Step 6: Confirmar que os outros testes continuam passando**

```bash
uv run pytest tests/test_users_routes.py tests/test_order_routes.py -v
```

Esperado: todos `passed` (usam `app.dependency_overrides[verify_token]`).

- [ ] **Step 7: Commit**

```bash
git add main.py dependencies.py tests/test_auth_routes.py
git commit -m "feat: verify_token reads access_token from HTTP-only cookie"
```

---

## Task 2: Atualizar /login para definir cookies

**Files:**
- Modify: `tests/test_auth_routes.py`
- Modify: `auth_routes.py`

- [ ] **Step 1: Atualizar test_login_success para esperar cookies**

Em `tests/test_auth_routes.py`, substituir `test_login_success`:

```python
def test_login_success(anon_client, db_session):
    _make_user(db_session, email="login@example.com", password="mypassword")
    payload = {"email": "login@example.com", "password": "mypassword"}
    response = anon_client.post("/auth/login", json=payload)
    assert response.status_code == 200
    assert response.json() == {"message": "Login realizado com sucesso"}
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies
```

- [ ] **Step 2: Rodar o teste e confirmar falha**

```bash
uv run pytest tests/test_auth_routes.py::test_login_success -v
```

Esperado: `FAILED` — o endpoint ainda retorna JSON com tokens, não cookies.

- [ ] **Step 3: Atualizar /login em auth_routes.py**

Adicionar `Request, Response` aos imports do fastapi no topo de `auth_routes.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, Request, Response
```

Substituir a função `login`:

```python
@auth_router.post("/login")
async def login(login_schema: loginSchema, response: Response, session: Session = Depends(get_session)):
    user = user_authentication(login_schema.email, login_schema.password, session)
    if not user:
        raise HTTPException(status_code=400, detail="user not found or invalid credentials")
    access_token = create_token(user.id, admin=_user_is_admin(user))
    refresh_token = create_token(
        user.id, admin=_user_is_admin(user), duration=timedelta(days=7)
    )
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=7 * 24 * 3600,
    )
    return {"message": "Login realizado com sucesso"}
```

- [ ] **Step 4: Rodar o teste e confirmar que passa**

```bash
uv run pytest tests/test_auth_routes.py::test_login_success tests/test_auth_routes.py::test_login_wrong_password tests/test_auth_routes.py::test_login_unknown_email -v
```

Esperado: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add auth_routes.py tests/test_auth_routes.py
git commit -m "feat: /login sets access_token and refresh_token as HTTP-only cookies"
```

---

## Task 3: Atualizar /token para definir cookies

**Files:**
- Modify: `tests/test_auth_routes.py`
- Modify: `auth_routes.py`

- [ ] **Step 1: Atualizar test_token_endpoint_success para esperar cookies**

Em `tests/test_auth_routes.py`, substituir `test_token_endpoint_success`:

```python
def test_token_endpoint_success(anon_client, db_session):
    _make_user(db_session, email="token@example.com", password="tokenpass")
    response = anon_client.post(
        "/auth/token",
        data={"username": "token@example.com", "password": "tokenpass"},
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Login realizado com sucesso"}
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies
```

- [ ] **Step 2: Rodar o teste e confirmar falha**

```bash
uv run pytest tests/test_auth_routes.py::test_token_endpoint_success -v
```

Esperado: `FAILED` — endpoint ainda retorna JSON com token.

- [ ] **Step 3: Atualizar /token em auth_routes.py**

Substituir a função `login_form`:

```python
@auth_router.post("/token")
async def login_form(form: OAuth2PasswordRequestForm = Depends(), response: Response = None, session: Session = Depends(get_session)):
    user = user_authentication(form.username, form.password, session)
    if not user:
        raise HTTPException(status_code=400, detail="user not found or invalid credentials")
    access_token = create_token(user.id, admin=_user_is_admin(user))
    refresh_token = create_token(
        user.id, admin=_user_is_admin(user), duration=timedelta(days=7)
    )
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=7 * 24 * 3600,
    )
    return {"message": "Login realizado com sucesso"}
```

- [ ] **Step 4: Rodar os testes e confirmar que passam**

```bash
uv run pytest tests/test_auth_routes.py::test_token_endpoint_success tests/test_auth_routes.py::test_token_endpoint_invalid -v
```

Esperado: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add auth_routes.py tests/test_auth_routes.py
git commit -m "feat: /token sets access_token and refresh_token as HTTP-only cookies"
```

---

## Task 4: Atualizar /refresh para ler e definir cookies

**Files:**
- Modify: `tests/test_auth_routes.py`
- Modify: `auth_routes.py`

- [ ] **Step 1: Adicionar teste novo e atualizar teste existente**

Em `tests/test_auth_routes.py`, substituir `test_refresh_token` e `test_refresh_token_invalid`:

```python
def test_refresh_token(anon_client, db_session):
    """Refresh com refresh_token cookie válido deve definir novo access_token cookie."""
    user = _make_user(db_session, email="refresh@example.com")
    refresh_tok = create_token(user.id, duration=timedelta(days=7))
    anon_client.cookies.set("refresh_token", refresh_tok)
    response = anon_client.post("/auth/refresh")
    assert response.status_code == 200
    assert response.json() == {"message": "Token renovado"}
    assert "access_token" in response.cookies
    anon_client.cookies.clear()


def test_refresh_token_invalid(anon_client):
    anon_client.cookies.set("refresh_token", "invalidtoken")
    response = anon_client.post("/auth/refresh")
    assert response.status_code == 401
    anon_client.cookies.clear()


def test_refresh_token_missing(anon_client):
    """Sem cookie refresh_token deve retornar 401."""
    response = anon_client.post("/auth/refresh")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
```

- [ ] **Step 2: Rodar os testes e confirmar falha**

```bash
uv run pytest tests/test_auth_routes.py::test_refresh_token tests/test_auth_routes.py::test_refresh_token_missing -v
```

Esperado: `FAILED` — endpoint ainda usa `Depends(verify_token)` e retorna JSON com token.

- [ ] **Step 3: Atualizar /refresh em auth_routes.py**

Remover `verify_token` do import de `dependencies` (linha 9):

```python
from dependencies import get_session
```

Substituir a função `use_refresh_token`:

```python
@auth_router.post("/refresh")
async def use_refresh_token(
    request: Request,
    response: Response,
    session: Session = Depends(get_session),
):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        dict_info = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(dict_info.get("sub"))
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    access_token = create_token(user.id, admin=_user_is_admin(user))
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return {"message": "Token renovado"}
```

- [ ] **Step 4: Rodar os testes e confirmar que passam**

```bash
uv run pytest tests/test_auth_routes.py::test_refresh_token tests/test_auth_routes.py::test_refresh_token_invalid tests/test_auth_routes.py::test_refresh_token_missing -v
```

Esperado: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add auth_routes.py tests/test_auth_routes.py
git commit -m "feat: /refresh reads refresh_token cookie and sets new access_token cookie"
```

---

## Task 5: Adicionar endpoint /logout

**Files:**
- Modify: `tests/test_auth_routes.py`
- Modify: `auth_routes.py`

- [ ] **Step 1: Adicionar teste de logout**

Em `tests/test_auth_routes.py`, adicionar ao final do arquivo:

```python
# ---------------------------------------------------------------------------
# POST /auth/logout
# ---------------------------------------------------------------------------

def test_logout_returns_success(anon_client):
    """Logout deve retornar 200 e limpar os cookies."""
    anon_client.cookies.set("access_token", "sometoken")
    anon_client.cookies.set("refresh_token", "somerefresh")
    response = anon_client.post("/auth/logout")
    assert response.status_code == 200
    assert response.json() == {"message": "Logout realizado"}
    anon_client.cookies.clear()
```

- [ ] **Step 2: Rodar o teste e confirmar falha**

```bash
uv run pytest tests/test_auth_routes.py::test_logout_returns_success -v
```

Esperado: `FAILED` — endpoint não existe, retorna 404 ou 405.

- [ ] **Step 3: Adicionar /logout em auth_routes.py**

Adicionar ao final de `auth_routes.py` (após o endpoint `/refresh`):

```python
@auth_router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logout realizado"}
```

- [ ] **Step 4: Rodar o teste e confirmar que passa**

```bash
uv run pytest tests/test_auth_routes.py::test_logout_returns_success -v
```

Esperado: `1 passed`

- [ ] **Step 5: Rodar a suite completa e confirmar que tudo passa**

```bash
uv run pytest tests/ -v
```

Esperado: todos os testes `passed`.

- [ ] **Step 6: Commit**

```bash
git add auth_routes.py tests/test_auth_routes.py
git commit -m "feat: add /logout endpoint that clears HTTP-only cookies"
```
