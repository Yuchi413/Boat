import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from flask_sqlalchemy import SQLAlchemy

# =========================================
# Flask 綁定的主資料庫 (在 models.py 使用)
# =========================================
db = SQLAlchemy()


# =========================================
# 建立 engine + session + Base 的工具函式
# =========================================
def make_engine_and_session(db_path: str):
    """
    建立一個獨立的 SQLAlchemy engine、session、Base
    用來管理多個 SQLite 資料庫（非 Flask 綁定的）
    """

    # 將路徑轉為絕對路徑，避免 Flask 與 Scheduler session 不一致
    abs_path = os.path.abspath(db_path)
    db_dir = os.path.dirname(abs_path)
    os.makedirs(db_dir, exist_ok=True)

    # 建立 engine，允許多執行緒共用
    engine = create_engine(
        f"sqlite:///{abs_path}",
        connect_args={"check_same_thread": False},
        echo=False,
    )

    # 建立 scoped session（確保 thread 安全）
    Session = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))

    # 建立 Base 給 declarative model 繼承
    Base = declarative_base()

    return engine, Session, Base


# =========================================
# 初始化 Flask 的主資料庫
# =========================================
def init_db(app):
    """
    綁定 Flask 應用與主資料庫 (SQLAlchemy)
    """
    db.init_app(app)
    with app.app_context():
        db.create_all()
        print("✅ Flask 主資料庫初始化完成")
