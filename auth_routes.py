from fastapi import APIRouter, Depends, HTTPException
from models import User
from dependencies import get_session, verify_token
from main import bcrypt_context, ALGORITHM, SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES
from schemas import userSchema, loginSchema
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordRequestForm

auth_router  = APIRouter(prefix="/auth", tags=["auth"])

def create_token(user_id: str, duration= timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)):
    expiration_date = datetime.now(timezone.utc) + duration
    info_dict = {"sub": str(user_id), "exp": expiration_date}
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
        refresh_token = create_token(user.id, timedelta(days=7))
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "Bearer"}


@auth_router.post("/login-test")
async def login_test(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = user_authentication(form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(status_code=400, detail="user not found or invalid credentials")
    else:
        access_token = create_token(user.id)
        return {"access_token": access_token, "token_type": "Bearer"}


@auth_router.post("/refresh")

async def use_refresh_token(user: User = Depends(verify_token)):
    access_token = create_token(user.id)

    return {"access_token": access_token, "token_type": "Bearer"}

