from sqladmin import ModelView
from src.database.models import *

class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.username, User.email]
    column_searchable_list = [User.id, User.username, User.email]
    form_excluded_columns = [User.password]

class PostAdmin(ModelView, model=Post):
    column_list = [Post.id, Post.title, Post.author_id]
    column_default_sort = [("created_at", True)]

class TagAdmin(ModelView, model=Tags):
    column_list = "__all__"