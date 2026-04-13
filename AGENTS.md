# FastAPI — Lógica da Aplicação

## Visão Geral

API REST construída com **FastAPI** + **SQLAlchemy** + **SQLite**. Gerencia usuários, autenticação JWT e pedidos (orders) com produtos.

## Estrutura de Arquivos

```
main.py           # App FastAPI, middleware CORS, configuração JWT, BcryptContext
models.py         # Modelos SQLAlchemy: User, Order, Product
schemas.py        # Schemas Pydantic (validação de entrada/saída)
dependencies.py   # get_session (DB), verify_token (JWT)
auth_routes.py    # Router /auth
order_routes.py   # Router /orders
users_routes.py   # Router /users
email_service.py  # Envio de e-mail via SMTP (recuperação de senha)
.env.example      # Variáveis de ambiente necessárias
```

## Banco de Dados

SQLite em `database.db`. Três tabelas:

- **users** — id, name, email, password (bcrypt), active, admin
- **orders** — id, user_id (FK), status (Pending/Cancelled/Finished), price (calculado), created_at
- **products** — id, name, price, quantity, size, order (FK) — produto é criado livre e depois vinculado a um order

Relacionamentos: `User` → `orders` (one-to-many), `Order` → `items` (one-to-many, cascade delete).

## Autenticação

- Bcrypt para hash de senhas (truncado em 72 bytes)
- JWT com `python-jose` — payload: `{ sub: user_id, exp, admin }`
- **Access token**: expira conforme `ACCESS_TOKEN_EXPIRE_MINUTES`
- **Refresh token**: expira em 7 dias
- **Password reset token**: expira em `PASSWORD_RESET_TOKEN_EXPIRE_MINUTES` (padrão 30 min), payload adiciona `purpose: "password_reset"`

`verify_token` em `dependencies.py` decodifica o JWT do header `Authorization: Bearer <token>` e retorna o `User` do banco.

## Rotas

### `/auth`

| Método | Endpoint               | Auth | Descrição |
|--------|------------------------|------|-----------|
| POST   | `/auth/signup`         | -    | Cria usuário; valida email único e confirmação de senha |
| POST   | `/auth/login`          | -    | Retorna access_token + refresh_token |
| POST   | `/auth/refresh`        | JWT  | Renova access_token |
| POST   | `/auth/forgot-password`| -    | Envia e-mail de reset (resposta genérica mesmo se e-mail não existe) |
| POST   | `/auth/reset-password` | -    | Troca senha via token de reset |

### `/orders` (todas exigem JWT)

| Método | Endpoint                              | Admin | Descrição |
|--------|---------------------------------------|-------|-----------|
| POST   | `/orders/order`                       | -     | Cria pedido com lista de produtos existentes |
| PUT    | `/orders/order/edit/{order_id}`       | próprio ou admin | Substitui produtos do pedido e recalcula preço |
| POST   | `/orders/order/cancel/{order_id}`     | próprio ou admin | Muda status para Cancelled |
| POST   | `/orders/order/finished/{order_id}`   | próprio ou admin | Muda status para Finished |
| GET    | `/orders/order/{order_id}`            | próprio ou admin | Detalhes de um pedido |
| GET    | `/orders/list_order/order_user`       | -     | Lista pedidos do usuário logado |
| GET    | `/orders/list`                        | sim   | Lista todos os produtos |
| POST   | `/orders/order/add_product`           | -     | Cria produto avulso (sem order vinculado) |
| POST   | `/orders/order/remove_product/{id}`   | -     | Remove produto pelo id |

**Cálculo de preço**: `Order.calculate_price()` soma `product.price * product.quantity` de todos os itens vinculados.

### `/users` (todas exigem JWT)

| Método | Endpoint              | Admin | Descrição |
|--------|-----------------------|-------|-----------|
| GET    | `/users/users`        | -     | Lista todos os usuários |
| GET    | `/users/user/{id}`    | -     | Detalhe de um usuário |
| PUT    | `/users/user/{id}`    | sim   | Atualiza name, email, active, admin |

## Fluxo de Recuperação de Senha

1. `POST /auth/forgot-password` com `{ email }` — gera token JWT de reset e envia por SMTP
2. Frontend redireciona para `PASSWORD_RESET_BASE_URL?token=<token>`
3. `POST /auth/reset-password` com `{ token, password, confirm_password }` — valida token, troca senha

## Variáveis de Ambiente (`.env`)

```
SECRET_KEY                          # Chave para assinar JWTs
ALGORITHM                           # ex: HS256
ACCESS_TOKEN_EXPIRE_MINUTES         # Expiração do access token

SMTP_HOST / MAILTRAP_HOST           # Host SMTP
SMTP_PORT / MAILTRAP_PORT           # Porta SMTP (padrão 2525)
SMTP_USER / MAILTRAP_USER           # Usuário SMTP
SMTP_PASSWORD / MAILTRAP_PASSWORD   # Senha SMTP
MAIL_FROM                           # Remetente dos e-mails
PASSWORD_RESET_BASE_URL             # URL do frontend para reset
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES # Validade do token de reset (padrão 30)
```

## Executar

```bash
uv run uvicorn main:app
```

Docs interativas em `http://localhost:8000/docs`.
