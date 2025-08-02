from datetime import datetime, timezone
from fastapi import HTTPException, status

from ..models import Comment
from ..models.posts import Post, PostStatus, Vote
from ..models.users import User
from src.schemas.posts import PostCreateFinal, PostRead, PostUpdateFinal, PostStatus, PostDeleteFinal, RatePostFinal, \
    DeletePostRatingFinal
from sqlalchemy import select, update, delete, Result, func
from sqlalchemy.ext.asyncio import AsyncSession
from ...schemas.comments import CreateCommentFinal, CommentRead, DeleteCommentFinal


class CommentService():
    def __init__(self, session: AsyncSession):
        self.session = session


    async def create_comment(self, comment_data: CreateCommentFinal) -> CommentRead:
        post = await self.session.get(Post, comment_data.post_id)
        if not post:
            raise ValueError("Post doesnt exist")

        dumped = comment_data.model_dump()
        if dumped['parent_id']:
            parent = await self.session.scalar(select(Comment.id).where(Comment.id==dumped['parent_id']))
            if not parent:
                raise ValueError("Comment doesnt exist")
        dumped['parent_id'] = None

        comment = Comment(**dumped)
        self.session.add(comment)
        await self.session.commit()
        await self.session.refresh(comment)

        return CommentRead.model_validate(comment)


    async def delete_comment(self, delete_data: DeleteCommentFinal) -> bool:
        comment = await self.session.get(Comment, delete_data.comment_id)
        if not comment:
            raise ValueError("Comment doesnt exist")
        if comment.author_id != delete_data.author_id:
            raise HTTPException(status_code=422, detail="Unauthorized")

        stmt = delete(Comment).where(Comment.id==delete_data.comment_id)
        await self.session.execute(stmt)
        await self.session.commit()

        return True