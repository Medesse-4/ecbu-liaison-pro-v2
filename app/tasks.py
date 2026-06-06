from celery import Celery
from config import Config

celery_app = Celery("ecbu_liaison_pro_v2", broker=Config.REDIS_URL, backend=Config.REDIS_URL)

@celery_app.task
def daily_backup():
    return "backup_task_placeholder"
