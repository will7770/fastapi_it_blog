from fastapi import FastAPI
import uvicorn
from database.core import init_db
from src.database.models import *
from src.api.v1 import users, posts, comments
from src.admin.setup import init_admin
from src.database.core import engine
from src.middlewares import admin_protection_middleware


app = FastAPI(
    title="FastAPI blog app",
    description="Unoriginal, but im trying my best",
    version="0.0.0",
)

app.middleware("http")(admin_protection_middleware)


app.include_router(users.router)
app.include_router(posts.router)
app.include_router(comments.router)


async def startup_event():
    await init_db()
    init_admin(app, engine)

app.add_event_handler("startup", startup_event)

if __name__ == '__main__':
    uvicorn.run("main:app")