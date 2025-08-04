from datetime import datetime, timedelta, timezone
from typing import Optional, Annotated
import os

from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv
from starlette.responses import RedirectResponse

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
    )

    payload = jwt.decode(token, secret_key, algorithms=[algorithm])
    if payload['type'] != "refresh":
        raise credentials_exception
    return payload


async def get_current_user(request: Request, session: AsyncSession = Depends(get_session)):
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")

    if not access_token and not refresh_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if refresh_token and not access_token:
        url = request.url.path
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": f"/user/refresh/?redirect_url={url}"}
        )

    decoded_access_token = jwt.decode(access_token, secret_key, algorithms=[algorithm])
    decoded_refresh_token = jwt.decode(refresh_token, secret_key, algorithms=[algorithm])
    if not decoded_access_token and not decoded_refresh_token:
        raise HTTPException(status_code=401, detail="Invalid tokens")

    username = decoded_access_token.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    async with session as session:
        serivce = UserService(session)
        user =  await serivce.get(by_username=username, return_raw=True)
        if not user:
            raise HTTPException(status_code=401, detail="User does not exist")
        return user


async def get_active_user(user: Annotated[User, Depends(get_current_user)]):
    return user


async def mod_access(user: Annotated[User, Depends(get_current_user)]):
    if user.role == Roles.MODERATOR or user.role == Roles.ADMIN:
        return True
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No access")

async def admin_access(user: Annotated[User, Depends(get_current_user)]):
    if user.role == Roles.ADMIN:
        return True
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No access")


async def verify_tags_and_convert(session: AsyncSession, tags: list) -> list[Tags]:
    existing_tags = (await session.scalars(select(Tags).where(Tags.name.in_(tags)))).all()

    if existing_tags:
        return existing_tags

    return []