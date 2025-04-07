from flask import Blueprint, request, jsonify, current_app
import os
import json
import logging
import jwt
from datetime import datetime

from database.db import db
from database.models import Task, SystemLog

# 创建蓝图
task_bp = Blueprint('task', __name__)

# 创建日志记录器
logger = logging.getLogger(__name__)

@task_bp.route('/', methods=['GET'])
def get_tasks():
    """
    获取任务列表
    """
    try:
        # 获取用户ID（如果有认证）
        user_id = None
        is_admin = False
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
        
        # 过滤条件
        status = request.args.get('status')
        if status:
            query = query.filter_by(status=status)
        
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

@task_bp.route('/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """
    获取单个任务详情
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

@task_bp.route('/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """
    删除任务
    需要JWT认证，且只有管理员或任务创建者可以删除
    """
    try:
        # 获取用户ID和管理员状态
        user_id = None
        is_admin = False
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
                return jsonify({'success': False, 'message': '认证失败'}), 401
        else:
            return jsonify({'success': False, 'message': '需要认证'}), 401
        
        # 查找任务
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'success': False, 'message': '任务不存在'}), 404
        
        # 检查权限
        if not is_admin and task.user_id != user_id:
            return jsonify({'success': False, 'message': '无权删除此任务'}), 403
        
        # 删除结果文件
        if task.result_path and os.path.exists(task.result_path):
            os.remove(task.result_path)
        
        # 删除数据库记录
        db.session.delete(task)
        db.session.commit()
        
        # 记录系统日志
        log = SystemLog(
            level='INFO',
            message=f'删除任务: {task.name}',
            source='task.delete_task',
            user_id=user_id
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '任务删除成功'
        }), 200
        
    except Exception as e:
        logger.error(f'删除任务失败: {str(e)}')
        return jsonify({'success': False, 'message': f'删除任务失败: {str(e)}'}), 500

@task_bp.route('/<int:task_id>/rerun', methods=['POST'])
def rerun_task(task_id):
    """
    重新运行任务
    需要JWT认证，且只有管理员或任务创建者可以重新运行
    """
    try:
        # 获取用户ID和管理员状态
        user_id = None
        is_admin = False
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
                return jsonify({'success': False, 'message': '认证失败'}), 401
        else:
            return jsonify({'success': False, 'message': '需要认证'}), 401
        
        # 查找任务
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'success': False, 'message': '任务不存在'}), 404
        
        # 检查权限
        if not is_admin and task.user_id != user_id:
            return jsonify({'success': False, 'message': '无权重新运行此任务'}), 403
        
        # 创建新任务
        new_task = Task(
            name=f"{task.name} (重新运行)",
            user_id=user_id,
            dataset_id=task.dataset_id,
            model_id=task.model_id,
            status='pending',
            hyperparams=task.hyperparams,
            created_at=datetime.utcnow()
        )
        
        db.session.add(new_task)
        db.session.commit()
        
        # 记录系统日志
        log = SystemLog(
            level='INFO',
            message=f'重新运行任务: {task.name}',
            source='task.rerun_task',
            user_id=user_id
        )
        db.session.add(log)
        db.session.commit()
        
        # 这里应该调用预测服务来执行任务
        # 为简化示例，这里只返回新创建的任务ID
        
        return jsonify({
            'success': True,
            'message': '任务已重新提交',
            'task_id': new_task.id
        }), 200
        
    except Exception as e:
        logger.error(f'重新运行任务失败: {str(e)}')
        return jsonify({'success': False, 'message': f'重新运行任务失败: {str(e)}'}), 500

@task_bp.route('/statistics', methods=['GET'])
def get_task_statistics():
    """
    获取任务统计信息
    """
    try:
        # 获取用户ID（如果有认证）
        user_id = None
        is_admin = False
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
        
        # 构建查询
        query = Task.query
        
        # 如果不是管理员，只统计自己的任务
        if user_id and not is_admin:
            query = query.filter_by(user_id=user_id)
        
        # 统计总任务数
        total_tasks = query.count()
        
        # 统计各状态任务数
        status_counts = {}
        for status in ['pending', 'running', 'completed', 'failed']:
            status_counts[status] = query.filter_by(status=status).count()
        
        # 统计各模型使用次数
        model_counts = db.session.query(
            Task.model_id,
            db.func.count(Task.id).label('count')
        ).group_by(Task.model_id).all()
        
        model_usage = []
        for model_id, count in model_counts:
            model = db.session.query(db.models.Model.name).filter_by(id=model_id).first()
            if model:
                model_usage.append({
                    'model': model[0],
                    'count': count
                })
        
        return jsonify({
            'success': True,
            'statistics': {
                'total_tasks': total_tasks,
                'status_counts': status_counts,
                'model_usage': model_usage
            }
        }), 200
        
    except Exception as e:
        logger.error(f'获取任务统计信息失败: {str(e)}')
        return jsonify({'success': False, 'message': f'获取任务统计信息失败: {str(e)}'}), 500