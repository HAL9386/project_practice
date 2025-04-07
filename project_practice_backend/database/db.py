from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging

# 创建SQLAlchemy实例
db = SQLAlchemy()


# 创建日志记录器
logger = logging.getLogger(__name__)

def init_db(app):
    """
    初始化数据库
    """
    try:
        db.init_app(app)
        Migrate(app, db)
        
        # 创建所有表（如果不存在）
        with app.app_context():
            db.create_all()
            
        logger.info("数据库初始化成功")
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        raise e