from models import db
from sqlalchemy.orm import sessionmaker, Session
from fastapi import Depends, HTTPException, Request
from models import User
from jose import JWTError, jwt
from main import SECRET_KEY, ALGORITHM


def get_session():
    try:
        Session = sessionmaker(bind=db)
        session = Session()
        yield session
    finally:
        session.close()


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
