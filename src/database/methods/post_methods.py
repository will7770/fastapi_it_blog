from datetime import datetime, timezone
from fastapi import HTTPException, status
from ..models.posts import Post, PostStatus, Vote
from ..models.users import User
from src.schemas.posts import PostCreateFinal, PostRead, PostUpdateFinal, PostStatus, PostDeleteFinal, RatePostFinal, \
    DeletePostRatingFinal
from sqlalchemy import select, update, delete, Result, func
from sqlalchemy.ext.asyncio import AsyncSession



class PostService():
    def __init__(self, session: AsyncSession):
        self.session = session


    async def create_post(self, post_data: PostCreateFinal) -> PostRead:
        user_exists = await self.session.scalar(select(User).where(User.id==post_data.author_id))
        if not user_exists:
            raise ValueError(f"User {post_data.author_id} doesnt exist")

        values = post_data.model_dump()
        new_post = Post(**values)

        self.session.add(new_post)
        await self.session.commit()
        await self.session.refresh(new_post)

        return PostRead.model_validate(new_post)


    async def search_post(self, query: str) -> list[PostRead]:
        stmt = (select(Post).where(Post.status==PostStatus.PUBLIC)
                .where(func.to_tsvector("simple", Post.title + " " + Post.content).op("@@")(func.plainto_tsquery("simple", query))))

        results = await self.session.execute(stmt)
        results = results.scalars().all()

        return [PostRead.model_validate(result) for result in results]


    async def get_post_by_id(self, id: int) -> PostRead:
        post = await self.session.get(Post, id)
        if not post:
            raise ValueError("Post with such id doesnt exist")
        return PostRead.model_validate(post)


    async def _get_all_posts(self) -> list[PostRead]:
        stmt = select(Post)
        results = await self.session.execute(stmt)
        results = results.scalars().all()

        return [PostRead.model_validate(result) for result in results]


    async def update_post(self, update_data: PostUpdateFinal) -> PostRead:
        data = update_data.model_dump(exclude={'id', 'author_id'}, exclude_unset=True)
        if not data:
            raise ValueError("No fields to update")

        post = await self.session.get(Post, update_data.id)
        if not post:
            raise ValueError("Post doesnt exist")
        if post.author_id != update_data.author_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not your post!")

        data['updated_at'] = func.now()
        new_status = data.get('status', PostStatus.DRAFT)
        if new_status != PostStatus.DRAFT and post.status != PostStatus.DRAFT:
            data['status'] = new_status
            data['published_at'] = func.now()

        stmt = update(Post).where(Post.id==update_data.id).values(**data).returning(Post)
        updated_post = await self.session.execute(stmt)
        await self.session.refresh(post)
        await self.session.commit()
        return PostRead.model_validate(updated_post.scalar())


    async def delete_post(self, post_data: PostDeleteFinal) -> bool:
        post = await self.session.get(Post, post_data.id)
        if not post:
            raise ValueError("Post doesnt exist")
        if post.author_id != post_data.author_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not your post!")

        stmt = delete(Post).where(Post.id==post.id)
        await self.session.execute(stmt)
        await self.session.commit()

        return True


    async def rate_post(self, rating_data: RatePostFinal) -> dict[str: int]:
        post = await self.session.get(Post, rating_data.post_id)

        if not post:
            raise ValueError("Post doesnt exist")
        vote = await self.session.scalars(select(Vote)
                    .where(Vote.author_id==rating_data.author_id, Vote.post_id==rating_data.post_id))
        vote = vote.first()

        if vote is not None:
            raise ValueError("User had already voted on this post")

        dumped = rating_data.model_dump()
        new_vote = Vote(**dumped)
        self.session.add(new_vote)

        stmt = update(Post).where(Post.id==dumped['post_id']).values(rating=post.rating+dumped['value']).returning(Post.rating)
        result = await self.session.scalar(stmt)

        await self.session.commit()
        return {"id": post.id,
                "new_rating": result}


    async def delete_rating(self, change_data: DeletePostRatingFinal) -> dict[str: int]:
        post = await self.session.get(Post, change_data.post_id)

        if not post:
            raise ValueError("Post doesnt exist")

        vote = (await self.session.execute(delete(Vote)
                     .where(Vote.author_id==change_data.author_id, Vote.post_id==change_data.post_id)
                    .returning(Vote.value))).scalar()

        stmt = update(Post).where(Post.id==change_data.post_id)
        if vote == -1:
            stmt = stmt.values(rating=post.rating+1).returning(Post.rating)
        elif vote == 1:
            stmt = stmt.values(rating=post.rating-1).returning(Post.rating)
        else:
            raise ValueError("User did not vote on that post yet")

        result = await self.session.scalar(stmt)
        await self.session.commit()
        return {"new_rating": result}