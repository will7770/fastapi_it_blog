from fastapi import HTTPException
from src.schemas.users import UserRead, UserCreate
from src.database.models import User
from sqlalchemy import select, update, delete, Result
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Any, Coroutine



class UserService():
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_data: UserCreate) -> UserRead:
        user_exists = await self.session.scalar(select(User).where(User.username==user_data.username))
        if user_exists:
            raise ValueError("User with same username already exists")

        values = user_data.model_dump()
        new_user = User(**values)

        self.session.add(new_user)
        await self.session.commit()
        await self.session.refresh(new_user)

        return UserRead.model_validate(new_user)

    async def get(self, by_id: int = None, by_username: str = None, return_raw: bool = False) -> UserRead | User:
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

    async def update(self, id: int, values: dict) -> UserRead:
        user_exists = await self.session.scalar(select(User.id).where(User.id==id))
        if not user_exists:
            raise HTTPException(status_code=404, detail="User doesnt exist")
        if values is None:
            raise ValueError("No fields to update")

        query = update(User).where(User.id==id).values(**values).returning(User)
        updated_user = await self.session.execute(query)
        await self.session.commit()
        updated_user = updated_user.scalar()

        return UserRead.model_validate(updated_user)

    async def delete(self, id: int, password: str) -> bool:
        async with self.session.begin():
            user = await self.session.scalar(select(User).where(User.id==id))
            if not user:
                raise ValueError("Invalid data")
            if password != user.password:
                raise ValueError("Invalid data")
            query = delete(User).where(User.id==id)
            result = await self.session.execute(query)

            return result.rowcount > 0