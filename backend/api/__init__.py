"""
API 模块初始化
"""
# API 路由模块（用于 main.py 导入）
from . import auth, users, repositories, categories, skills, webhooks, sync, public_categories

__all__ = ['auth', 'users', 'repositories', 'categories', 'skills', 'webhooks', 'sync', 'public_categories']
