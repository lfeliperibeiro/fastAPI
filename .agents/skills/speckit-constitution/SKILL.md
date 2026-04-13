---
name: speckit-constitution
description: Constituição local da API FastAPI deste repositório. Use para manter regras de domínio, contratos de autenticação/autorização e invariantes ao alterar rotas, models, schemas, testes e migrações.
---

# Speckit Constitution

Use este skill quando a tarefa envolver mudanças na API, no banco, nos contratos de autenticação ou no fluxo de pedidos.

## Contexto do sistema

- Stack atual: FastAPI + SQLAlchemy ORM + Alembic + SQLite.
- Arquivos centrais: `main.py`, `models.py`, `auth_routes.py`, `order_routes.py`, `users_routes.py`, `dependencies.py`, `schemas.py`.
- O banco local padrão é `database.db`. Mudanças estruturais exigem migration em `alembic/versions/`.

## Regras obrigatórias

- Preserve a separação atual por domínio:
  `auth_routes.py` cuida de autenticação e reset de senha.
  `order_routes.py` cuida de pedidos e produtos.
  `users_routes.py` cuida de leitura/atualização de usuários.
- Toda rota protegida deve continuar usando `verify_token` de `dependencies.py`.
- Tokens JWT devem continuar assinados com `SECRET_KEY` e `ALGORITHM` vindos de ambiente.
- Não grave segredos no código. Continue usando `.env` e `.env.example`.
- Se uma mudança alterar estrutura de resposta, valide também o impacto em `schemas.py` e nos testes.

## Autenticação e usuários

- Senhas devem continuar passando por `bcrypt_context` em `main.py`.
- O hash/verificação atual trunca a senha em 72 bytes por compatibilidade com bcrypt. Não remova isso sem migrar a estratégia inteira.
- `POST /auth/signup` precisa continuar validando:
  email único
  `password == confirm_password`
- Tokens de acesso e refresh carregam `sub` com `user_id`.
- Refresh token continua com duração de 7 dias, salvo instrução explícita em contrário.
- Token de reset deve continuar com `purpose: "password_reset"` para não se confundir com token de login.
- `forgot-password` deve manter resposta genérica quando o e-mail não existir.
- Apenas admin pode alterar `active` e `admin` via `PUT /users/user/{user_id}`.

## Autorização

- Admin bypass continua válido onde já existe.
- Operações em pedido individual devem permitir apenas:
  dono do pedido
  ou admin
- Ao criar nova rota protegida, defina explicitamente quem pode executar:
  usuário autenticado
  dono do recurso
  admin
- Nunca confie no `admin` vindo só do payload sem validar o usuário do banco. O padrão correto já existe em `verify_token`.

## Invariantes de pedidos e produtos

- Um pedido precisa ter ao menos um produto.
- Quantidade de item em pedido deve ser maior que zero.
- Preço total do pedido deve continuar derivado de `sum(item.price * item.quantity)`.
- Ao editar pedido, os produtos vinculados anteriormente são desvinculados antes da nova associação. Preserve esse comportamento ou mude junto com testes e contrato.
- Status de pedido hoje seguem o vocabulário já usado no código:
  `Pending`
  `Cancelled`
  `Finished`
  Observação: `models.py` ainda declara `Completed` em `ORDER_STATUS`; trate isso como inconsistência existente e não introduza novos status sem alinhar model, rotas, schemas e testes.
- Produto pode existir avulso antes de ser associado a um pedido. Não assuma que todo `Product` já tem `order`.

## Banco e migrações

- Mudou model SQLAlchemy, coluna, relacionamento ou default persistido: gere migration Alembic correspondente.
- Evite lógica dependente de SQLite se isso dificultar futura troca de banco, exceto quando a tarefa for explicitamente local.
- Mantenha relacionamentos coerentes com os nomes atuais:
  `User.orders`
  `Order.items`
- Se alterar cascade, FK ou nulidade, revise impacto de exclusão e desvinculação de produtos.

## Contratos de API

- Prefira mudanças compatíveis com clientes existentes.
- Se mudar shape de request/response, atualize:
  `schemas.py`
  docstrings ou README se o endpoint estiver documentado
  testes afetados
- Mensagens de erro devem continuar específicas o suficiente para depuração, sem vazar segredo.

## Testes mínimos esperados

- Toda mudança de comportamento em rota deve adicionar ou ajustar teste em `tests/`.
- Para autenticação, cubra ao menos sucesso e falha principal.
- Para pedidos, cubra ao menos autorização, validação de quantidade e cálculo de preço quando esses pontos forem afetados.
- Se corrigir bug sem teste, adicione regressão antes de encerrar a tarefa quando for viável.

## Checklist de mudança

- Identifique se a alteração toca autenticação, autorização, contrato HTTP ou schema de banco.
- Atualize código do domínio certo sem espalhar regra por arquivos aleatórios.
- Recalcule impactos em `schemas.py`, migrations e testes.
- Rode os testes relevantes; se não rodar, deixe isso explícito.
