from fastapi import FastAPI
import uvicorn
from database.core import init_db
from src.database.models import *
from database.models import User, Post
from src.api.v1 import users, posts

app = FastAPI(
    title="FastAPI blog app",
    description="Unoriginal, but im trying my best",
    version="0.0.0",
)


app.include_router(users.router)
app.include_router(posts.router)

async def startup_event():
    await init_db()

app.add_event_handler("startup", startup_event)

if __name__ == '__main__':
    uvicorn.run("main:app")