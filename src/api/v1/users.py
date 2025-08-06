from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Response, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from starlette.responses import RedirectResponse
from src.database.core import get_session
from src.schemas.users import UserCreate, UserRead, UserUpdateFinal, UserDelete, UserUpdateInitial, Profile
from src.database.methods.user_methods import UserService
from ..dependencies import verify_user, create_access_token, verify_user_for_refresh, get_active_user, \
    verify_tags_and_convert, create_refresh_token, decode_and_verify_refresh_token, admin_access
from src.database.models.users import User
from ...schemas.posts import PostRead
from jose import jwt, JWTError
from ...utils import hash_password



router = APIRouter(prefix="/user", tags=["users"])


@router.get("/refresh/")
async def refresh_token(request: Request,
                        session: Annotated[AsyncSession, Depends(get_session)],
                        redirect_url: str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        token = request.cookies.get("refresh_token")
        payload = decode_and_verify_refresh_token(token)
        username = payload.get('sub')
        if not username:
            raise credentials_exception

        user = await verify_user_for_refresh(username, session)
        if not user:
            raise credentials_exception

        response = RedirectResponse(redirect_url)
        access_token = create_access_token(data={"sub": username})
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            samesite="lax",
            max_age=30 * 60
        )

        return response
    except JWTError:
        raise credentials_exception


@router.post("/register/")
async def register(session: Annotated[AsyncSession, Depends(get_session)],
                   user_data: UserCreate
                   ):
    service = UserService(session)
    try:
        user_exists = await service.create(user_data)
        return user_exists
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/login")
async def login_for_access_token(session: Annotated[AsyncSession, Depends(get_session)],
                                 response: Response,
                                 username: str = Form(...),
                                 password: str = Form(...)):
    user = await verify_user(username, password, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    refesh_token = create_refresh_token(
        data={"sub": user.username}
    )
    response.set_cookie(
        key="refresh_token",
        value=refesh_token,
        httponly=True,
        samesite="lax",
        max_age=7*24*60*60,
    )

    access_token = create_access_token(
        data={"sub": user.username}
    )
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        max_age=30*60
    )

    return {"access_token": access_token, "refresh_token": refesh_token}


@router.post("/logout/", status_code=status.HTTP_200_OK)
async def logout(response: Response,
                 user: User = Depends(get_active_user)):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return {"status": "logged out successfully"}


@router.get("/profile/", response_model=Profile, status_code=status.HTTP_200_OK)
async def profile(session: Annotated[AsyncSession, Depends(get_session)],
                  user: User = Depends(get_active_user)):
    service = UserService(session)
    return await service.profile(user.id)


@router.post("/create/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(user_create: UserCreate,
                      response: Response,
                      session: Annotated[AsyncSession, Depends(get_session)]):
    service = UserService(session)
    try:
        hashed_password = hash_password(user_create.password)
        user_create.password = hashed_password
        created_user = await service.create(user_create)

        refesh_token = create_refresh_token(
            data={"sub": created_user.username}
        )
        response.set_cookie(
            key="refresh_token",
            value=refesh_token,
            httponly=True,
            samesite="lax",
            max_age=7 * 24 * 60 * 60,
        )

        access_token = create_access_token(
            data={"sub": created_user.username}
        )
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            samesite="lax",
            max_age=30 * 60
        )
        return created_user
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.get("/user/{id}", response_model=UserRead, status_code=status.HTTP_200_OK)
async def get_user(id: str | int,
                   session: Annotated[AsyncSession, Depends(get_session)]):
    service = UserService(session)
    try:
        if id.isdigit():
            user = await service.get(by_id=int(id))
        else:
            user = await service.get(by_username=id)
        return user
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.patch("/update/", response_model=UserRead, status_code=status.HTTP_200_OK)
async def update_user(user_data: UserUpdateInitial,
                      session: Annotated[AsyncSession, Depends(get_session)],
                      user: User = Depends(get_active_user)):
    service = UserService(session)
    try:
        user_id = user.id
        update_data = UserUpdateFinal(**user_data.model_dump(), id=user_id)
        new_user = await service.update(update_data)
        return new_user
    except ValueError as err:
        raise HTTPException(status_code=200, detail=str(err))


@router.post("/favorite_tag/", status_code=status.HTTP_200_OK)
async def favorite_tag(session: Annotated[AsyncSession, Depends(get_session)],
                       user: User = Depends(get_active_user),
                       tags: list[str] = Query(..., alias="tag")):
    service = UserService(session)
    processed_tags = await verify_tags_and_convert(session, tags)
    if not processed_tags:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect tag names")

    result = await service.add_tag_to_favorites(user_id=user.id, tags=processed_tags)
    if result:
        return {"status": "success"}
    return {"status": "failed"}


@router.delete("/delete/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_data: UserDelete,
                      session: Annotated[AsyncSession, Depends(get_session)],
                      is_admin = Depends(admin_access)):
    service = UserService(session)
    try:
        deleted = await service.delete(user_data.id, user_data.password)
        return {"user_deleted?": deleted}
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))


@router.get("/my_posts/", response_model=list[PostRead], status_code=status.HTTP_200_OK)
async def my_posts(session: Annotated[AsyncSession, Depends(get_session)],
                   user: User = Depends(get_active_user)):
    service = UserService(session)
    return await service.user_posts(user_id=user.id)