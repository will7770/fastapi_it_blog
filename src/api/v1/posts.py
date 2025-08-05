from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, Optional
from src.database.core import get_session
from src.schemas.posts import PostCreateInitial, PostCreateFinal, PostRead, PostUpdateInitial, \
    PostUpdateFinal, PostDeleteInitial, PostDeleteFinal, RatePostInitial, RatePostFinal, DeletePostRatingFinal, \
    DeletePostRatingInitial
from src.database.methods.post_methods import PostService
from ..dependencies import get_active_user, verify_tags_and_convert
from src.database.models.users import User


router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("/create/", response_model=PostRead, status_code=status.HTTP_201_CREATED)
async def create_post(post_data: PostCreateInitial,
                      session: Annotated[AsyncSession, Depends(get_session)],
                      user: User = Depends(get_active_user)):
    try:
        author_id = user.id
        service = PostService(session)
        data = post_data.model_dump(exclude={"tags"})

        if post_data.tags:
            processed_tags = await verify_tags_and_convert(session, post_data.tags)
            if not processed_tags:
                raise HTTPException(status_code=400, detail="Incorrect tags")
            data['tags'] = processed_tags

        post_serve_data = PostCreateFinal(**data, author_id=author_id)
        post = await service.create_post(post_serve_data)
        return post
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.get("/post/", status_code=status.HTTP_200_OK)
async def get_post(session: Annotated[AsyncSession, Depends(get_session)],
                   id: int = None,
                   tags: Optional[list[str]] = Query([], alias="tag", example=["Python", "JavaScript"])):
    try:
        service = PostService(session)
        post = await service.get_posts(id, tags)
        return post
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.get("/search/", response_model=list[PostRead], status_code=status.HTTP_200_OK)
async def search_post(query: str,
                      session: Annotated[AsyncSession, Depends(get_session)]):
    service = PostService(session)
    try:
        posts = await service.search_post(query)
        return posts
    except ValueError as err:
        raise HTTPException(status_code=204, detail=err)


@router.patch("/update/", response_model=PostRead, status_code=status.HTTP_200_OK)
async def update_post(update_data: PostUpdateInitial,
                      session: Annotated[AsyncSession,
                      Depends(get_session)],
                      user: User = Depends(get_active_user)):
    service = PostService(session)
    try:
        user_id = user.id
        data = update_data.model_dump(exclude={"tags"})
        if update_data.tags:
            processed_tags = await verify_tags_and_convert(session, update_data.tags)
            if not processed_tags:
                raise HTTPException(status_code=400, detail="Incorrect tags")
            data['tags'] = processed_tags


        new_data = PostUpdateFinal(**data, author_id=user_id)
        result = await service.update_post(new_data)
        return result
    except ValueError as err:
        raise HTTPException(status_code=400, detail=err)


@router.delete("/delete/", status_code=status.HTTP_200_OK)
async def delete_post(session: Annotated[AsyncSession, Depends(get_session)],
                      delete_data: PostDeleteInitial,
                      user: User = Depends(get_active_user)):
    service = PostService(session)
    try:
        final_delete_data = PostDeleteFinal(id=delete_data.id, author_id=user.id)
        return await service.delete_post(final_delete_data)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=err)


@router.get("/recent_posts/", status_code=status.HTTP_200_OK)
async def recent_posts(session: Annotated[AsyncSession, Depends(get_session)]):
    service = PostService(session)
    try:
        return await service.get_posts(order='newest')
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.get("/my_feed/", status_code=status.HTTP_200_OK)
async def my_feed(session: Annotated[AsyncSession, Depends(get_session)],
                  user: User = Depends(get_active_user)):
    service = PostService(session)
    try:
        converted_tags = [tag.name for tag in user.favorite_tags]
        return await service.get_posts(order='newest', tags=converted_tags)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/rate/", status_code=status.HTTP_200_OK)
async def rate_post(session: Annotated[AsyncSession, Depends(get_session)],
                    rating_data: RatePostInitial,
                    user: User = Depends(get_active_user)):
    service = PostService(session)
    try:
        final_rating_data = RatePostFinal(**rating_data.model_dump(), author_id=user.id)
        return await service.rate_post(final_rating_data)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.delete("/delete_post_rating/", status_code=status.HTTP_200_OK)
async def delete_post_rating(session: Annotated[AsyncSession, Depends(get_session)],
                             rating_data: DeletePostRatingInitial,
                             user: User = Depends(get_active_user)):
    service = PostService(session)
    try:
        final_delete_data = DeletePostRatingFinal(post_id=rating_data.post_id, author_id=user.id)
        return await service.delete_rating(final_delete_data)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/bookmarks/", status_code=status.HTTP_200_OK)
async def bookmarks(session: Annotated[AsyncSession, Depends(get_session)],
                    user: User = Depends(get_active_user),
                    post_id: int = Body(..., embed=True)):
    service = PostService(session)
    try:
        return await service.bookmark_post(user_id=user.id, post_id=post_id)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.get("/all_tags/", status_code=status.HTTP_200_OK)
async def all_tags(session: Annotated[AsyncSession, Depends(get_session)]):
    service = PostService(session)
    return await service._get_all_tags()