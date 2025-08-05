from fastapi import FastAPI
import uvicorn
from database.core import init_db
from src.api.v1 import users, posts, comments
from src.admin.setup import init_admin
from src.database.core import engine
from src.middlewares import admin_protection_middleware
from contextlib import asynccontextmanager
from src.cache.redis_config import r


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    init_admin(app, engine)
    yield
    await r.close()

app = FastAPI(
    title="FastAPI blog app",
    description="Unoriginal, but im trying my best",
    version="0.0.0",
    lifespan=lifespan
)

app.middleware("http")(admin_protection_middleware)


app.include_router(users.router)
app.include_router(posts.router)
app.include_router(comments.router)


if __name__ == '__main__':
    uvicorn.run("main:app")