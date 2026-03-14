# FastAPI Example

Projeto de exemplo com **FastAPI**, **SQLAlchemy**, **Alembic** e autenticação JWT.

## ✅ Funcionalidades principais

- Cadastro de usuário (signup)
- Login com JWT (access + refresh tokens)
- Rotas protegidas por token (Bearer)
- CRUD simples de pedidos / produtos (com permissões de admin)
- Cancelamento e finalização de pedidos

## 🚀 Preparando o ambiente

### 1) Crie/ative um ambiente virtual

```bash
python -m venv .venv
source .venv/bin/activate.fish
```

### 2) Instale as dependências

```bash
python -m pip install -e .
```

Para instalar também as dependências de desenvolvimento (testes):

```bash
python -m pip install -e .[dev]
```

### 3) Configure variáveis de ambiente

Copie o arquivo de exemplo e preencha os valores:

```bash
cp .env.example .env
```

Edite `.env` e defina pelo menos:

- `SECRET_KEY` (valor aleatório)
- `ALGORITHM` (ex: `HS256`)
- `ACCESS_TOKEN_EXPIRE_MINUTES` (ex: `120`)

### 4) Migre o banco de dados (SQLite)

O projeto usa SQLite (`banco.db` por padrão).

```bash
alembic upgrade head
```

### 5) Execute a aplicação

```bash
python -m uvicorn main:app --reload
```

Ou, se usar o utilitário `uv`:

```bash
uv run uvicorn main:app --reload
```

### 6) Acesse a documentação automática

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

---

## 🔌 Principais rotas (API)

### Autenticação

#### `POST /auth/signup`
Cria um usuário novo.

Body de exemplo (JSON):

```json
{
  "name": "Nome",
  "email": "usuario@exemplo.com",
  "password": "senha123",
  "active": true
}
```

> Observação: a API não permite definir `admin: true` no signup.

#### `POST /auth/login`
Faz login com email + senha e retorna `access_token` e `refresh_token`.

Body de exemplo (JSON):

```json
{
  "email": "usuario@exemplo.com",
  "password": "senha123"
}
```

#### `POST /auth/login-test`
Login via fluxo OAuth2 (form data). Útil para testar `OAuth2PasswordRequestForm`.

#### `POST /auth/refresh`
Renova o token de acesso. Requer enviar o token de refresh no cabeçalho `Authorization: Bearer <refresh_token>`.

---

### Pedidos (requere autenticação)

Para todas as rotas abaixo, envie o cabeçalho:

```
Authorization: Bearer <access_token>
```

#### `GET /orders/`
Retorna um placeholder (a rota ainda não lista pedidos reais).

#### `GET /orders/list` (admin)
Retorna todos os pedidos (apenas usuários admin têm acesso).

#### `GET /orders/order/{order_id}`
Retorna detalhes de um pedido (admin ou dono do pedido).

#### `POST /orders/order`
Cria um pedido para um usuário.

Body (JSON):

```json
{
  "user_id": 1
}
```

#### `POST /orders/order/cancel/{order_id}`
Cancela um pedido (admin ou dono do pedido).

#### `POST /orders/order/finished/{order_id}`
Marca um pedido como finalizado (admin ou dono do pedido).

#### `POST /orders/order/add_product/{order_id}`
Adiciona um produto ao pedido.

Body (JSON):

```json
{
  "name": "Produto",
  "price": 20.0,
  "quantity": 2,
  "size": "M"
}
```

#### `POST /orders/order/remove_product/{product_id}`
Remove um produto de um pedido (admin ou dono do pedido).

---

## 🧪 Testes

Execute o conjunto de testes com:

```bash
pytest
```

