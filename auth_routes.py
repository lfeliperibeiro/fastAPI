import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from dependencies import get_session
from email_service import send_password_reset_email
from main import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    SECRET_KEY,
    bcrypt_context,
)
from models import User
from schemas import (
    ForgotPasswordSchema,
    ResetPasswordSchema,
    loginSchema,
    userSchema,
)
auth_router = APIRouter(prefix="/auth", tags=["auth"])

def create_token(
    user_id: str,
    *,
    admin: bool = False,
    duration: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    purpose: str | None = None,
):
    expiration_date = datetime.now(timezone.utc) + duration
    info_dict = {
        "sub": str(user_id),
        "exp": expiration_date,
        "admin": bool(admin),
    }
    if purpose:
        info_dict["purpose"] = purpose
    encoding_jwt = jwt.encode(info_dict, SECRET_KEY, algorithm=ALGORITHM)
    return encoding_jwt


def _password_reset_expire() -> timedelta:
    minutes = int(os.getenv("PASSWORD_RESET_TOKEN_EXPIRE_MINUTES", "30"))
    return timedelta(minutes=minutes)


def create_password_reset_token(user_id: int) -> str:
    expiration_date = datetime.now(timezone.utc) + _password_reset_expire()
    payload = {
        "sub": str(user_id),
        "exp": expiration_date,
        "purpose": "password_reset",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_password_reset_token(token: str) -> int:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("purpose") != "password_reset":
            raise JWTError()
        return int(payload["sub"])
    except JWTError:
        raise HTTPException(
            status_code=400,
            detail="Token de recuperação inválido ou expirado",
        ) from None


def _user_is_admin(user: User) -> bool:
    return bool(user.admin) if user.admin is not None else False



def user_authentication(email: str, password: str, session: Session):
    user = session.query(User).filter(User.email == email).first()

    if not user:
        return False
    elif not bcrypt_context.verify(password, user.password):
        return False
    else:
        return user

@auth_router.get("/")

async def auth():
    """Authentication routes"""
    return {"message": "Authentication route"}

@auth_router.post("/signup")

async def signup(user_schema: userSchema, session: Session = Depends(get_session)):
    user = session.query(User).filter(User.email == user_schema.email).first()

    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    else:
        if user_schema.password != user_schema.confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match")
        password = bcrypt_context.hash(user_schema.password)
        new_user = User(user_schema.name, user_schema.email, password, user_schema.active, user_schema.admin)
        session.add(new_user)
        session.commit()
        return {"message": f"User created successfully {user_schema.email}"}

@auth_router.post("/token")
async def login_form(response: Response, form: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = user_authentication(form.username, form.password, session)
    if not user:
        raise HTTPException(status_code=400, detail="user not found or invalid credentials")
    access_token = create_token(user.id, admin=_user_is_admin(user))
    refresh_token = create_token(
        user.id, admin=_user_is_admin(user), duration=timedelta(days=7), purpose="refresh"
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


@auth_router.post("/login")
async def login(login_schema: loginSchema, response: Response, session: Session = Depends(get_session)):
    user = user_authentication(login_schema.email, login_schema.password, session)
    if not user:
        raise HTTPException(status_code=400, detail="user not found or invalid credentials")
    access_token = create_token(user.id, admin=_user_is_admin(user))
    refresh_token = create_token(
        user.id, admin=_user_is_admin(user), duration=timedelta(days=7), purpose="refresh"
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


@auth_router.post("/forgot-password")
async def forgot_password(
    body: ForgotPasswordSchema,
    session: Session = Depends(get_session),
):
    user = session.query(User).filter(User.email == body.email).first()
    if user:
        token = create_password_reset_token(user.id)
        try:
            send_password_reset_email(user.email, token, user.name)
        except RuntimeError as e:
            raise HTTPException(status_code=503, detail=str(e)) from e
        except OSError:
            raise HTTPException(
                status_code=502,
                detail="Não foi possível enviar o e-mail. Verifique SMTP_HOST e credenciais.",
            ) from None
    return {
        "message": "Se o e-mail estiver cadastrado, você receberá instruções em breve.",
    }


@auth_router.post("/reset-password")
async def reset_password(
    body: ResetPasswordSchema,
    session: Session = Depends(get_session),
):
    if body.password != body.confirm_password:
        raise HTTPException(status_code=400, detail="As senhas não coincidem")
    user_id = decode_password_reset_token(body.token)
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="Usuário não encontrado")
    user.password = bcrypt_context.hash(body.password)
    session.commit()
    return {"message": "Senha redefinida com sucesso"}

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
        if dict_info.get("purpose") != "refresh":
            raise JWTError()
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


@auth_router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", httponly=True, samesite="lax")
    response.delete_cookie("refresh_token", httponly=True, samesite="lax")
    return {"message": "Logout realizado"}
