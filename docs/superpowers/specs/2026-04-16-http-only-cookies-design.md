# Design: Migração para Cookies HTTP-Only

**Data:** 2026-04-16  
**Status:** Aprovado

## Contexto

A API FastAPI retorna `access_token` e `refresh_token` como JSON no corpo da resposta. O frontend armazena esses tokens (geralmente em `localStorage`), expondo-os a ataques XSS. A migracao para cookies HTTP-only elimina esse vetor: o browser gerencia os cookies e o JavaScript nao pode le-los.

O cliente e uma aplicacao web em `http://localhost:3000`. Nao ha clientes mobile ou API direta, portanto uma migracao completa sem fallback e viavel.

## Abordagem escolhida

**Cookies somente** (sem fallback para `Authorization: Bearer`).

- `SameSite=lax` mitiga CSRF sem necessidade de CSRF token adicional
- `HttpOnly=True` impede acesso via JavaScript
- CORS restrito a `http://localhost:3000`

## Mudancas por arquivo

### `main.py`

- Remover `OAuth2PasswordBearer` e `oauth2_scheme`
- Atualizar `allow_origins` de `["*"]` para `["http://localhost:3000"]`

### `dependencies.py`

- Remover `Depends(oauth2_scheme)` de `verify_token`
- `verify_token` passa a receber `request: Request` e ler `request.cookies.get("access_token")`
- Retorna `401` se cookie ausente ou token invalido

```python
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

### `auth_routes.py`

**`POST /auth/login` e `POST /auth/token`:**

- Adicionam parametro `response: Response`
- Chamam `response.set_cookie(...)` para `access_token` e `refresh_token`
- Retornam `{"message": "Login realizado com sucesso"}` (sem tokens no body)

Configuracao dos cookies:

| Atributo    | Valor                                  |
|-------------|----------------------------------------|
| `httponly`  | `True`                                 |
| `secure`    | `False` (dev) — ativar em producao     |
| `samesite`  | `"lax"`                                |
| `max_age`   | `ACCESS_TOKEN_EXPIRE_MINUTES * 60` (access) / `7 * 24 * 3600` (refresh) |

**`POST /auth/refresh`:**

- Le `refresh_token` de `request.cookies.get("refresh_token")`
- Define novo cookie `access_token` na resposta
- Retorna `{"message": "Token renovado"}`

**`POST /auth/logout`** (novo endpoint):

- Sem autenticacao exigida
- Chama `response.delete_cookie("access_token")` e `response.delete_cookie("refresh_token")`
- Retorna `{"message": "Logout realizado"}`

## Endpoints nao alterados

Todos os endpoints que usam `Depends(verify_token)` (`/orders/*`, `/users/*`) continuam funcionando sem alteracao de assinatura — apenas a origem do token muda internamente.

## Pontos de atencao

- **Swagger `/docs`:** Rotas protegidas nao funcionarao via Swagger UI (nao envia cookies automaticamente). Usar Postman ou HTTPie para testes de rotas autenticadas.
- **`secure=True` em producao:** Deve ser ativado quando o frontend estiver em HTTPS.
- **`allow_origins` em producao:** Substituir `http://localhost:3000` pela URL real do frontend.

## Fora de escopo

- CSRF token (double-submit pattern) — `SameSite=lax` e suficiente para o perfil de risco atual
- Clientes mobile ou Bearer header fallback
