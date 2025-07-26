from datetime import datetime, timezone
from ..models.posts import Post
from ..models.users import User
from src.schemas.posts import PostCreateInitial, PostCreateFinal, PostRead, PostUpdate, PostStatus
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
        stmt = select(Post).where(func.to_tsvector("simple", Post.title + " " + Post.content).op("@@")(func.plainto_tsquery("simple", query)))
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

    async def update_post(self, update_data: PostUpdate) -> PostRead:
        data = update_data.model_dump(exclude={'id', 'author_id'}, exclude_unset=True)
        if not data:
            raise ValueError("No fields to update")

        post = await self.session.get(Post, update_data.id)
        if not post:
            raise ValueError("Post doesnt exist")

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