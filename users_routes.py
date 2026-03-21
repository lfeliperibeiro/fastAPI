from fastapi import APIRouter, Depends, HTTPException
from models import User
from dependencies import get_session, verify_token
from sqlalchemy.orm import Session

from schemas import UpdateUserSchema, userSchema, UsersListResponseSchema

users_router  = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(verify_token)])


@users_router.get("/")

async def users():
    """Users routes"""
    return {"message": "Users routes"}

@users_router.get("/users", response_model=UsersListResponseSchema)

async def get_users(session: Session = Depends(get_session)):
    users = session.query(User).all()
    return {
        "users": [
            {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "active": bool(user.active) if user.active is not None else False,
                "admin": bool(user.admin) if user.admin is not None else False,
            }
            for user in users
        ]
    }

@users_router.get("/user/{user_id}")
async def get_user(user_id: int, session: Session = Depends(get_session)):
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    else:
        return {"user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "active": user.active,
            "admin": user.admin
        }}

@users_router.put("/user/{user_id}")

async def update_user(
    user_id: int,
    user_schema: UpdateUserSchema,
    session: Session = Depends(get_session),
    current_user: User = Depends(verify_token),
):
    if not current_user.admin:
        raise HTTPException(
            status_code=403,
            detail="Only administrators can update users",
        )
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    else:
        user.name = user_schema.name
        user.email = user_schema.email
        user.active = user_schema.active
        user.admin = user_schema.admin
        session.commit()
        return {"message": f"User updated successfully"}