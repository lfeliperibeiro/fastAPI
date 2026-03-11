from fastapi import APIRouter, Depends, HTTPException
from models import User
from dependencies import get_session
from main import bcrypt_context, ALGORITHM, SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES
from schemas import userSchema, loginSchema
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone

auth_router  = APIRouter(prefix="/auth", tags=["auth"])

def create_token(user_id: str):
    expiration_date = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    info_dict = {"sub": user_id, "exp": expiration_date}
    encoding_jwt = jwt.encode(info_dict, SECRET_KEY, algorithm=ALGORITHM)
    token = encoding_jwt
    return token

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
        password = bcrypt_context.hash(user_schema.password)
        new_user = User(user_schema.name, user_schema.email, password, user_schema.admin, user_schema.active)
        session.add(new_user)
        session.commit()
        return {"message": f"User created successfully {user_schema.email}"}

@auth_router.post("/login")

async def login(login_schema: loginSchema, session: Session = Depends(get_session)):
    user = user_authentication(login_schema.email, login_schema.password, session)
    if not user:
        raise HTTPException(status_code=400, detail="user not found or invalid credentials")
    else:
        access_token = create_token(user.id)
        return {"access_token": access_token, "token_type": "Bearer"}

