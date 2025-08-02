from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from src.database.core import get_session
from src.database.methods.comment_methods import CommentService
from ..dependencies import get_active_user
from src.database.models.users import User
from ...schemas.comments import CommentRead, CreateCommentInitial, CreateCommentFinal, DeleteCommentInitial, \
    DeleteCommentFinal

router = APIRouter(prefix="/comments", tags=["comments"])


@router.post("/create/", response_model=CommentRead, status_code=status.HTTP_201_CREATED)
async def create_comment(session: Annotated[AsyncSession, Depends(get_session)], comment_data: CreateCommentInitial, user: User = Depends(get_active_user)):
    service = CommentService(session)
    try:
        final_data = CreateCommentFinal(**comment_data.model_dump(), author_id=user.id)
        return await service.create_comment(final_data)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.delete("/delete/", status_code=status.HTTP_200_OK)
async def delete_comment(session: Annotated[AsyncSession, Depends(get_session)], delete_data: DeleteCommentInitial, user: User = Depends(get_active_user)):
    service = CommentService(session)
    try:
        final_data = DeleteCommentFinal(author_id=user.id, comment_id=delete_data.comment_id)
        result = await service.delete_comment(final_data)
        return {"deleted": result}
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))