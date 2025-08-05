from fastapi import HTTPException
from sqlalchemy.orm import joinedload

from src.database.models import Post
from src.schemas.posts import PostRead
from src.schemas.users import UserRead, UserCreate, UserUpdateFinal, Profile
from src.database.models import User
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession



class UserService():
    def __init__(self, session: AsyncSession):
        self.session = session


    async def create(self, user_data: UserCreate) -> UserRead:
        """Create a user and return them"""
        user_exists = await self.session.scalar(select(User).where(User.username==user_data.username))
        if user_exists:
            raise ValueError("User with same username already exists")

        values = user_data.model_dump()
        new_user = User(**values)

        self.session.add(new_user)
        await self.session.refresh(new_user)

        return UserRead.model_validate(new_user)


    async def get(self, by_id: int = None, by_username: str = None, return_raw: bool = False) -> UserRead | User:
        """
        Get a user by one of args
        :param by_id: find user by their id
        :param by_username: find user by their username
        :param return_raw: return raw User object
        :return: validated or raw user
        """
        if not by_id and not by_username:
            raise ValueError("No criteria specified")

        query = select(User)
        if by_id:
            query = query.where(User.id==by_id)
        elif by_username:
            query = query.where(User.username==by_username)

        user = await self.session.scalar(query)

        if user is None:
            raise HTTPException(status_code=404, detail="User doesnt exist")

        if return_raw:
            return user

        return UserRead.model_validate(user)


    async def update(self, update_data: UserUpdateFinal) -> UserRead:
        """Update user and return them"""
        user_exists = await self.session.scalar(select(User.id).where(User.id==update_data.id))
        if not user_exists:
            raise HTTPException(status_code=404, detail="User doesnt exist")
        values = update_data.model_dump(exclude_unset=True)
        if values is None:
            raise ValueError("No fields to update")

        query = update(User).where(User.id==update_data.id).values(**values).returning(User)
        updated_user = await self.session.execute(query)
        updated_user = updated_user.scalar()
        await self.session.commit()

        return UserRead.model_validate(updated_user)


    async def delete(self, id: int, password: str) -> bool:
        """Delete the user (handle proper admin access checking in endpoints)"""
        user = await self.session.scalar(select(User).where(User.id==id))
        if not user:
            raise ValueError("Invalid data")
        if password != user.password:
            raise ValueError("Invalid data")
        query = delete(User).where(User.id==id)
        result = await self.session.execute(query)

        await self.session.commit()

        return result.rowcount > 0


    async def add_tag_to_favorites(self, user_id: int, tags: list) -> bool:
        """Add a tag to user's favorites"""
        stmt = select(User).where(User.id==user_id).options(joinedload(User.favorite_tags))
        user = (await self.session.scalars(stmt)).first()

        if not user:
            raise HTTPException(status_code=404, detail="User doesnt exist")

        user.favorite_tags = tags
        await self.session.commit()

        return True

    async def user_posts(self, user_id: int) -> list[PostRead]:
        """Return a list of posts belonging to user"""
        stmt = await self.session.scalars(select(Post).where(Post.author_id==user_id).options(joinedload(Post.comments)))
        posts = stmt.unique().all()
        return [PostRead.model_validate(post) for post in posts]


    async def profile(self, user_id: int) -> Profile:
        """Return a complete list of user's data"""
        stmt = await self.session.scalars(select(User).where(User.id==user_id).options(joinedload(User.bookmarks), joinedload(User.favorite_tags)))
        result = stmt.first()

        return Profile.model_validate(result)