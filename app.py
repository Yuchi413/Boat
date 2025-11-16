from flask import Flask
from flask_cors import CORS
import os

# 自訂模組
from config import MAIN_DB_PATH
from database import init_db
from models import init_models
from routes import api_blueprint, web_blueprint
from fetcher import fetch_data
from scheduler import init_scheduler


# =========================================
# 建立 Flask 應用
# =========================================
app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

# 設定主資料庫 URI（Flask 綁定）
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.abspath(MAIN_DB_PATH)}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# =========================================
# 初始化資料庫
# =========================================
print("🔧 初始化 Flask 資料庫 ...")
init_db(app)        # 綁定 Flask → 主資料庫
init_models(app)    # 建立主 DB + 其他分庫的表格
print("✅ 所有資料庫初始化完成")

# =========================================
# 註冊 Blueprint
# =========================================
app.register_blueprint(api_blueprint, url_prefix="/api")
app.register_blueprint(web_blueprint)

# =========================================
# 主程式入口
# =========================================
if __name__ == "__main__":
    with app.app_context():
        print("🚀 伺服器啟動中：執行第一次 AIS 抓取 ...")
        try:
            fetch_data(force_push=True)
            print("✅ 首次資料抓取完成")
        except Exception as e:
            print(f"⚠️ 初次 fetch_data() 執行失敗: {e}")

    # 啟動定時排程（背景自動抓取）
    init_scheduler(app)

    # 啟動 Flask 伺服器
    app.run(host="0.0.0.0", port=5000, debug=False)

