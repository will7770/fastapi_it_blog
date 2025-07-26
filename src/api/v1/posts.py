from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from src.database.core import get_session
from src.schemas.posts import PostCreateInitial, PostCreateFinal, PostRead, PostUpdate
from src.database.methods.post_methods import PostService
from ..dependencies import get_active_user
from src.database.models.users import User


router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("/create_post/", response_model=PostRead, status_code=status.HTTP_201_CREATED)
async def create_post(post_data: PostCreateInitial, session: Annotated[AsyncSession, Depends(get_session)], user: User = Depends(get_active_user)):
    try:
        author_id = user.id
        service = PostService(session)
        post_serve_data = PostCreateFinal(**post_data.model_dump(), author_id=author_id)
        post = await service.create_post(post_serve_data)
        return post
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.get("/get_post/{id}", response_model=PostRead, status_code=status.HTTP_200_OK)
async def get_post(id: int, session: Annotated[AsyncSession, Depends(get_session)]):
    try:
        service = PostService(session)
        post = await service.get_post_by_id(id)
        return post
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.get("/search_post/", response_model=list[PostRead], status_code=status.HTTP_200_OK)
async def search_post(query: str, session: Annotated[AsyncSession, Depends(get_session)]):
    service = PostService(session)
    try:
        posts = await service.search_post(query)
        return posts
    except Exception as err:
        raise HTTPException(status_code=204, detail=err)


@router.patch("/update_post/", response_model=PostRead, status_code=status.HTTP_200_OK)
async def update_post(update_data: PostUpdate, session: Annotated[AsyncSession, Depends(get_session)], user: User = Depends(get_active_user)):
    service = PostService(session)
    try:
        if update_data.author_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your post!")
        result = await service.update_post(update_data)
        return result
    except ValueError as err:
        raise HTTPException(status_code=400, detail=err)