from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from dotenv import load_dotenv
import os
import bcrypt

_root = Path(__file__).resolve().parent
load_dotenv(_root / ".env.example")
load_dotenv(_root / ".env", override=True)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class BcryptContext:
    def hash(self, password: str) -> str:
        pwd_bytes = password.encode('utf-8')[:72]
        return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode('utf-8')

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        pwd_bytes = plain_password.encode('utf-8')[:72]
        return bcrypt.checkpw(pwd_bytes, hashed_password.encode('utf-8'))

bcrypt_context = BcryptContext()

from auth_routes import auth_router
from order_routes import order_router
from users_routes import users_router

app.include_router(auth_router)
app.include_router(order_router)
app.include_router(users_router)
