from datetime import datetime, timedelta, timezone
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
from src.database.models.users import User, Roles
from src.database.models.tags import Tags
from sqlalchemy import select




load_dotenv()
secret_key = os.getenv("SECRET_KEY")
access_token_expire = os.getenv("ACCESS_TOKEN_EXPIRE_MINS")
refresh_token_expire = os.getenv("REFRESH_TOKEN_EXPIRE_DAYS")
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


async def verify_user_for_refresh(username: str, session: AsyncSession):
    service = UserService(session)
    user = await service.get(by_username=username, return_raw=True)

    if not user:
        return False
    return user


def create_access_token(data: dict):
    encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(minutes=int(access_token_expire))
    encode.update({"expire": expire.timestamp()})

    encoded_jwt = jwt.encode(encode, secret_key, algorithm=algorithm)
    return encoded_jwt


def create_refresh_token(data: dict):
    encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(days=int(refresh_token_expire))
    encode.update({"expire": expire.timestamp(), "type": "refresh"})

    encoded_jwt = jwt.encode(encode, secret_key, algorithm=algorithm)
    return encoded_jwt


def decode_and_verify_refresh_token(token: str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = jwt.decode(token, secret_key, algorithms=[algorithm])
    if payload['type'] != "refresh":
        raise credentials_exception
    return payload


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
    user = await service.get(by_username=username, return_raw=True)
    if not user:
        raise invalid_credentials
    return user


async def get_active_user(user: Annotated[User, Depends(get_current_user)]):
    return user


async def admin_access(user: Annotated[User, Depends(get_current_user)]):
    if user.role == Roles.ADMIN:
        return True
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No access")


async def verify_tags_and_convert(session: AsyncSession, tags: list) -> list[Tags]:
    existing_tags = (await session.scalars(select(Tags).where(Tags.name.in_(tags)))).all()

    if existing_tags:
        return existing_tags

    return []