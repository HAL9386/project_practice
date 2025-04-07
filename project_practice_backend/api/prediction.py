import jwt
from flask import Blueprint, request, jsonify, current_app
import os
import json
import numpy as np
import pandas as pd
from datetime import datetime
import logging
import time

from database.db import db
from database.models import Task, Dataset, Model, SystemLog, User

# 创建蓝图
prediction_bp = Blueprint('prediction', __name__)

# 创建日志记录器
logger = logging.getLogger(__name__)

# 预测结果保存目录
RESULT_DIR = 'results'

@prediction_bp.route('/predict', methods=['POST'])
def predict():
    """
    执行时间序列预测
    """
    try:
        # 确保结果目录存在
        os.makedirs(RESULT_DIR, exist_ok=True)
        
        data = request.get_json()
        
        # 验证必要字段
        required_fields = ['taskName', 'modelType', 'hyperParams']
        if not all(k in data for k in required_fields):
            return jsonify({'success': False, 'message': '缺少必要字段'}), 400
        
        # 获取用户ID（如果有认证）
        user_id = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            try:
                token = auth_header.split(' ')[1]
                payload = jwt.decode(
                    token,
                    current_app.config['SECRET_KEY'],
                    algorithms=['HS256']
                )
                user_id = payload['user_id']
            except Exception as e:
                logger.warning(f'获取用户ID失败: {str(e)}')
        
        # 创建预测任务记录
        task = Task(
            name=data['taskName'],
            user_id=user_id,
            model_id=get_model_id(data['modelType']),
            status='running',
            hyperparams=data['hyperParams'],
            created_at=datetime.utcnow()
        )
        
        # 处理数据源
        if data.get('dataSourceType') == 'preset' and data.get('datasetId'):
            task.dataset_id = data['datasetId']
            dataset = Dataset.query.get(data['datasetId'])
            if not dataset:
                return jsonify({'success': False, 'message': '数据集不存在'}), 404
            data_file = dataset.file_path
        elif data.get('dataSourceType') == 'upload' and request.files.get('file'):
            # 保存上传的文件
            file = request.files['file']
            upload_dir = 'uploads'
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
            file.save(file_path)
            data_file = file_path
        else:
            return jsonify({'success': False, 'message': '无效的数据源'}), 400
        
        # 保存任务到数据库
        db.session.add(task)
        db.session.commit()
        
        # 记录系统日志
        log = SystemLog(
            level='INFO',
            message=f'创建预测任务: {data["taskName"]}',
            source='prediction.predict',
            user_id=user_id
        )
        db.session.add(log)
        db.session.commit()
        
        # 执行预测（这里是模拟，实际应用中可能需要异步处理）
        start_time = time.time()
        
        # 读取数据
        df = pd.read_csv(data_file)
        
        # 模拟预测过程
        time.sleep(2)  # 模拟计算时间
        
        # 生成模拟预测结果
        result = generate_mock_prediction(df, data['hyperParams'])
        
        # 计算执行时长
        duration = time.time() - start_time
        
        # 保存预测结果
        result_file = os.path.join(RESULT_DIR, f"task_{task.id}_result.json")
        with open(result_file, 'w') as f:
            json.dump(result, f)
        
        # 更新任务状态
        task.status = 'completed'
        task.completed_at = datetime.utcnow()
        task.duration = duration
        task.result_path = result_file
        task.metrics = result['metrics']
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '预测完成',
            'taskId': task.id,
            'result': result
        }), 200
        
    except Exception as e:
        logger.error(f'预测失败: {str(e)}')
        return jsonify({'success': False, 'message': f'预测失败: {str(e)}'}), 500

@prediction_bp.route('/tasks', methods=['GET'])
def get_tasks():
    """
    获取预测任务列表
    """
    try:
        # 获取用户ID（如果有认证）
        user_id = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            try:
                token = auth_header.split(' ')[1]
                payload = jwt.decode(
                    token,
                    current_app.config['SECRET_KEY'],
                    algorithms=['HS256']
                )
                user_id = payload['user_id']
                is_admin = payload.get('is_admin', False)
            except Exception as e:
                logger.warning(f'获取用户ID失败: {str(e)}')
        
        # 查询任务
        query = Task.query
        
        # 如果不是管理员，只显示自己的任务
        if user_id and not is_admin:
            query = query.filter_by(user_id=user_id)
        
        # 排序和分页
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # 应用排序
        if hasattr(Task, sort_by):
            if sort_order.lower() == 'desc':
                query = query.order_by(getattr(Task, sort_by).desc())
            else:
                query = query.order_by(getattr(Task, sort_by))
        
        # 执行分页查询
        pagination = query.paginate(page=page, per_page=per_page)
        tasks = pagination.items
        
        # 格式化结果
        result = {
            'success': True,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages,
            'tasks': []
        }
        
        for task in tasks:
            # 获取关联的数据集和模型信息
            dataset_name = task.dataset.name if task.dataset else None
            model_name = task.model.name if task.model else None
            username = task.user.username if task.user else None
            
            result['tasks'].append({
                'id': task.id,
                'name': task.name,
                'status': task.status,
                'dataset': dataset_name,
                'model': model_name,
                'username': username,
                'created_at': task.created_at.isoformat() if task.created_at else None,
                'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                'duration': task.duration,
                'metrics': task.metrics
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f'获取任务列表失败: {str(e)}')
        return jsonify({'success': False, 'message': f'获取任务列表失败: {str(e)}'}), 500

@prediction_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """
    获取单个预测任务详情
    """
    try:
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'success': False, 'message': '任务不存在'}), 404
        
        # 获取关联的数据集和模型信息
        dataset_name = task.dataset.name if task.dataset else None
        model_name = task.model.name if task.model else None
        username = task.user.username if task.user else None
        
        # 读取预测结果
        result = None
        if task.result_path and os.path.exists(task.result_path):
            with open(task.result_path, 'r') as f:
                result = json.load(f)
        
        return jsonify({
            'success': True,
            'task': {
                'id': task.id,
                'name': task.name,
                'status': task.status,
                'dataset': dataset_name,
                'model': model_name,
                'username': username,
                'hyperparams': task.hyperparams,
                'created_at': task.created_at.isoformat() if task.created_at else None,
                'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                'duration': task.duration,
                'metrics': task.metrics,
                'result': result
            }
        }), 200
        
    except Exception as e:
        logger.error(f'获取任务详情失败: {str(e)}')
        return jsonify({'success': False, 'message': f'获取任务详情失败: {str(e)}'}), 500

# 辅助函数
def get_model_id(model_type):
    """
    根据模型类型获取模型ID
    """
    model = Model.query.filter_by(model_type=model_type).first()
    if model:
        return model.id
    return None

def generate_mock_prediction(df, hyperparams):
    """
    生成模拟预测结果
    实际应用中应替换为真实的预测逻辑
    """
    # 获取数据长度
    data_length = len(df)
    
    # 获取预测长度
    prediction_length = hyperparams.get('predictionLength', 24)
    
    # 生成模拟的真实值和预测值
    real_values = np.sin(np.linspace(0, 10, data_length)).tolist()
    predicted_values = np.sin(np.linspace(0.1, 10.1, data_length)).tolist()
    print(real_values)
    print(predicted_values)
    
    # 生成预测区间的上下界
    upper_bound = [v + 0.2 for v in predicted_values]
    lower_bound = [v - 0.2 for v in predicted_values]
    
    # 计算误差指标
    errors = [abs(r - p) for r, p in zip(real_values, predicted_values)]
    mse = np.mean(np.square(errors))
    mae = np.mean(errors)
    rmse = np.sqrt(mse)
    
    # 构建结果
    result = {
        'data': {
            'timestamps': df.iloc[:, 0].tolist(),  # 假设第一列是时间戳
            'real_values': real_values,
            'predicted_values': predicted_values,
            'upper_bound': upper_bound,
            'lower_bound': lower_bound
        },
        'metrics': {
            'mse': round(mse, 4),
            'mae': round(mae, 4),
            'rmse': round(rmse, 4),
            'duration': round(np.random.uniform(1.5, 5.0), 2),
            'dataPoints': data_length,
            'confidence': round(np.random.uniform(0.85, 0.98), 2)
        }
    }
    
    return result