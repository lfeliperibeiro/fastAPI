from fastapi import APIRouter, Depends, HTTPException
from models import User
from dependencies import get_session
from main import bcrypt_context
from schemas import userSchema
from sqlalchemy.orm import Session

auth_router  = APIRouter(prefix="/auth", tags=["auth"])

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
