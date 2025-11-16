from apscheduler.schedulers.background import BackgroundScheduler
from fetcher import fetch_data
from flask import Flask

# =========================================
# 建立 Scheduler
# =========================================
scheduler = BackgroundScheduler()

def init_scheduler(app: Flask):
    """
    初始化排程，定期執行 fetch_data()
    """
    def scheduled_fetch():
        with app.app_context():
            fetch_data(force_push=False)

    # 每 10 分鐘抓一次
    scheduler.add_job(func=scheduled_fetch, trigger="interval", minutes=10)
    scheduler.start()
    print("[Scheduler] 啟動成功，每 10 分鐘抓一次資料。")
