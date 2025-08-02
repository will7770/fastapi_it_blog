from fastapi import FastAPI, Depends
from sqladmin import Admin
from sqlalchemy.ext.asyncio import AsyncEngine


def init_admin(app: FastAPI, engine: AsyncEngine) -> None:
    """Initialize SQLAdmin interface"""
    from sqladmin import Admin
    from src.admin.views import UserAdmin, PostAdmin, TagAdmin

    admin = Admin(
        app,
        engine,
        title="Admin",
        base_url="/admin",
        templates_dir="admin/templates",
    )

    admin.add_view(UserAdmin)
    admin.add_view(PostAdmin)
    admin.add_view(TagAdmin)
