from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
from datetime import datetime

from flask_migrate import Migrate

# 导入自定义模块
from database.db import init_db, db
from api.auth import auth_bp
from api.prediction import prediction_bp
from api.dataset import dataset_bp
from api.model import model_bp
from api.task import task_bp

# 确保日志目录存在
os.makedirs('logs', exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
migrate = Migrate(app, db)  # 初始化 Flask-Migrate

# 配置跨域
CORS(app, resources={r"/*": {"origins": "*"}})

# 配置数据库
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost/time_series_prediction'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'

# 初始化数据库
init_db(app)

# 注册蓝图
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(prediction_bp, url_prefix='/api/prediction')
app.register_blueprint(dataset_bp, url_prefix='/api/dataset')
app.register_blueprint(model_bp, url_prefix='/api/model')
app.register_blueprint(task_bp, url_prefix='/api/task')

# 健康检查路由
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat()
    })

# 错误处理
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    logger.error(f"Server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # 创建数据库表
    with app.app_context():
        db.create_all()
    
    # 启动应用
    app.run(debug=True, host='0.0.0.0', port=5000)