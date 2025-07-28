from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from src.database.core import get_session
from src.schemas.users import UserCreate, UserRead, UserUpdateFinal, UserDelete, UserUpdateInitial
from src.database.methods.user_methods import UserService
from ..dependencies import hash_password, verify_user, create_token, expire, get_active_user
from src.database.models.users import User
from ...database.methods.post_methods import PostService
from ...schemas.posts import PostRead



router = APIRouter(prefix="/user", tags=["users"])


@router.post("/token")
async def login_for_access_token(session: Annotated[AsyncSession, Depends(get_session)], form_data: OAuth2PasswordRequestForm = Depends()):
    user = await verify_user(form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_token(
        data={"sub": user.username}
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/profile/", response_model=UserRead, status_code=status.HTTP_200_OK)
async def profile(user: User = Depends(get_active_user)):
    return UserRead.model_validate(user)


@router.post("/create_user/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(user_create: UserCreate, session: Annotated[AsyncSession, Depends(get_session)]):
    service = UserService(session)
    try:
        hashed_password = hash_password(user_create.password)
        user_create.password = hashed_password
        return await service.create(user_create)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.get("/get_user/{path}", response_model=UserRead, status_code=status.HTTP_200_OK)
async def get_user(path: str | int, session: Annotated[AsyncSession, Depends(get_session)]):
    service = UserService(session)
    try:
        if path.isdigit():
            user = await service.get(by_id=int(path))
        else:
            user = await service.get(by_username=path)

        return user
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.patch("/update_user/", response_model=UserRead, status_code=status.HTTP_200_OK)
async def update_user(user_data: UserUpdateInitial, session: Annotated[AsyncSession, Depends(get_session)], user: User = Depends(get_active_user)):
    service = UserService(session)
    try:
        user_id = user.id
        update_data = UserUpdateFinal(**user_data.model_dump(), id=user_id)
        new_user = await service.update(update_data)
        return new_user
    except ValueError as err:
        raise HTTPException(status_code=200, detail=str(err))


@router.delete("/delete_user/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_data: UserDelete, session: Annotated[AsyncSession, Depends(get_session)]):
    service = UserService(session)
    try:
        deleted = await service.delete(user_data.id, user_data.password)
        return {"user_deleted?": deleted}
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))


@router.get("/my_posts/", response_model=list[PostRead], status_code=status.HTTP_200_OK)
async def my_posts(session: Annotated[AsyncSession, Depends(get_session)], user: User = Depends(get_active_user)):
    service = UserService(session)
    return await service.user_posts(user_id=user.id)