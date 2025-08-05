from typing import Literal

from fastapi import HTTPException, status
from sqlalchemy.orm import joinedload
from ..models import Comment, Tags
from ..models.posts import Post, PostStatus, Vote
from ..models.users import User
from src.schemas.posts import PostCreateFinal, PostRead, PostUpdateFinal, PostStatus, PostDeleteFinal, RatePostFinal, \
    DeletePostRatingFinal, Tag
from sqlalchemy import select, update, delete, Result, func
from sqlalchemy.ext.asyncio import AsyncSession



class PostService():
    def __init__(self, session: AsyncSession):
        self.session = session


    async def create_post(self, post_data: PostCreateFinal) -> PostRead:
        """Create a post and return it"""
        user_exists = await self.session.scalar(select(User).where(User.id==post_data.author_id))
        if not user_exists:
            raise ValueError(f"User {post_data.author_id} doesnt exist")

        values = post_data.model_dump(exclude={"tags"})
        new_post = Post(**values)

        if post_data.tags:
            new_post.tags = post_data.tags
            await self.session.flush()

        self.session.add(new_post)
        await self.session.commit()
        await self.session.refresh(new_post)

        return PostRead.model_validate(new_post)


    async def get_posts(self, id: int = None,
                        tags: list = None,
                        search_query: str = None,
                        order: Literal['newest', 'oldest'] = None) -> list[PostRead]:
        """
        Get a list of posts by args
        :param id: returns a list of 1 post with exact id match
        :param tags: returns posts with matching tags
        :param order: orders the posts by time
        :param search_query: str to match with title
        :return: list of validated posts
        """
        stmt = select(Post).options(joinedload(Post.comments))

        if id:
            stmt = stmt.where(Post.id==id)

        if tags:
            stmt = stmt.where(Post.tags.any(Tags.name.in_(tags)))

        if search_query:
            stmt = (stmt.where(Post.status==PostStatus.PUBLIC)
                .where(func.to_tsvector("simple", Post.title + " " + Post.content)
                .op("@@")(func.plainto_tsquery("simple", search_query))))

        if order:
            if order == 'newest':
                stmt = stmt.order_by(Post.published_at.desc())
            elif order == 'oldest':
                stmt = stmt.order_by(Post.published_at.asc())

        posts = await self.session.scalars(stmt)
        if not posts:
            raise ValueError("No posts found")
        return [PostRead.model_validate(post) for post in posts.unique().all()]


    async def update_post(self, update_data: PostUpdateFinal) -> PostRead:
        """Update the post if user matches the author"""
        data = update_data.model_dump(exclude={'id', 'author_id', 'tags'}, exclude_unset=True)
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

        if update_data.tags:
            post.tags = update_data.tags
            await self.session.flush()

        await self.session.commit()
        await self.session.refresh(post)
        return PostRead.model_validate(updated_post.scalar())


    async def delete_post(self, post_data: PostDeleteFinal) -> bool:
        """Delete the post if user matches the author"""
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
        """
        Rate the post and create a new entry in db for the rating
        :return: new post rating
        """
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
        """
        Delete the rating from post and its entry in db
        :return: new post rating
        """
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


    async def bookmark_post(self, user_id: int, post_id: int) -> dict[str: str]:
        """
        Add a post to user's bookmarks
        :return: dict with operation's status
        """
        post = await self.session.get(Post, post_id)
        if not post:
            raise ValueError("Post doesnt exist")
        user = (await self.session.scalars(select(User).where(User.id==user_id).options(joinedload(User.bookmarks)))).first()
        if not user:
            raise ValueError("User doesnt exist")


        bookmarked_already = next((bookmark for bookmark in user.bookmarks if bookmark.id == post_id), None)
        if bookmarked_already:
            user.bookmarks.remove(bookmarked_already)
            await self.session.commit()
            return {"status": "removed"}

        user.bookmarks.append(post)
        await self.session.commit()
        return {"status": "added"}


    async def _get_all_tags(self) -> list[Tag]:
        """Utility for viewing all existing tags"""
        tags = (await self.session.scalars(select(Tags))).all()

        return [Tag.model_validate(tag) for tag in tags]