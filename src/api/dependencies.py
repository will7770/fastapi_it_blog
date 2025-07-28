from datetime import datetime, timedelta
from typing import Optional, Annotated
import os
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv
from src.database.methods.user_methods import UserService
from src.database.core import get_session
from src.database.models.users import User




load_dotenv()
secret_key = os.getenv("SECRET_KEY")
expire = os.getenv("ACCESS_TOKEN_EXPIRE_MINS")
algorithm = os.getenv("ALGORITHM")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/token/")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(plain_password: str):
    return pwd_context.hash(plain_password)


async def verify_user(username: str, password: str, session: AsyncSession):
    # use locally imported session lol
    service = UserService(session)
    user = await service.get(by_username=username, return_raw=True)
    if not user:
        return False

    if not verify_password(password, user.password):
        return False

    return user


def create_token(data: dict):
    encode = data.copy()
    encode.update({"expire": expire})

    encoded_jwt = jwt.encode(encode, secret_key, algorithm=algorithm)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_session)):
    invalid_credentials = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                        detail="Invalid credentials",
                                        headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        username = payload.get("sub")
        if not username:
            raise invalid_credentials
    except JWTError:
        raise invalid_credentials
    service = UserService(session)
    user = await service.get(by_username=username)
    if not user:
        raise invalid_credentials
    return user


async def get_active_user(user: Annotated[User, Depends(get_current_user)]):
    return user