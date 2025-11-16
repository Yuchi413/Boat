from flask import Blueprint
from .api import api_blueprint
from .web import web_blueprint

# 這裡不用定義新的 Blueprint，只要匯出已經在 api.py / web.py 定義好的即可
__all__ = ["api_blueprint", "web_blueprint"]
