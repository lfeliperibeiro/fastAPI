# FastAPI Example

API simples utilizando FastAPI, SQLAlchemy e Alembic.

## Funcionalidades principais

- Criação de usuário (signup)
- Login com JWT (access + refresh tokens)
- Rotas protegidas via token (você precisa estar autenticado para acessar)
- CRUD de pedidos (apenas admins podem ver todos os pedidos)
- Cancelamento de pedidos (admins ou dono do pedido)
- Adição de produtos a um pedido (admins ou dono do pedido)

## Dependências

As dependências são gerenciadas via `pyproject.toml` (PEP 621). O projeto usa:

- FastAPI
- SQLAlchemy
- Alembic
- Passlib + bcrypt
- python-jose (JWT)
- python-dotenv

## Rodando localmente

1) Ative o ambiente virtual (supondo que você use um `.venv`):

```bash
source .venv/bin/activate.fish
```

2) Instale dependências (se ainda não estiverem instaladas):

```bash
pip install -r requirements.txt
```

3) Execute a aplicação:

```bash
uvicorn main:app --reload
```


Alternativa (com o utilitário `uv`):

```bash
 uv run uvicorn main:app --reload
 ```


4) Acesse a documentação automática:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Rotas principais

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

#### `POST /auth/refresh`
Renova o token (precisa enviar o refresh token).


### Pedidos (requere autenticação)

Todas as rotas abaixo exigem que você envie o cabeçalho `Authorization: Bearer <token>`.

#### `GET /orders/`
Retorna um placeholder (ainda não implementado para listar pedidos reais).

#### `POST /orders/order`
Cria um pedido para o usuário indicado.

Body (JSON):

```json
{
  "user_id": 1
}
```

#### `POST /orders/order/cancel/{order_id}`
Cancela um pedido. Só o admin ou o dono do pedido podem cancelar.

#### `POST /orders/order/add_product/{order_id}`
Adiciona um produto a um pedido.

Body (JSON):

```json
{
  "name": "Produto",
  "price": 20.0,
  "quantity": 2,
  "size": "M"
}
```

## Banco de dados

O projeto usa SQLite (`banco.db` por padrão). Para gerar migrações com Alembic:

```bash
alembic revision --autogenerate -m "mensagem"
alembic upgrade head
```

