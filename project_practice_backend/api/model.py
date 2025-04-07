from flask import Blueprint, request, jsonify, current_app
import logging
import jwt
from datetime import datetime

from database.db import db
from database.models import Model, SystemLog

# 创建蓝图
model_bp = Blueprint('model', __name__)

# 创建日志记录器
logger = logging.getLogger(__name__)

@model_bp.route('/', methods=['GET'])
def get_models():
    """
    获取预测模型列表
    """
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        model_type = request.args.get('model_type')
        
        # 构建查询
        query = Model.query
        
        # 应用过滤条件
        if model_type:
            query = query.filter_by(model_type=model_type)
        
        # 执行分页查询
        pagination = query.paginate(page=page, per_page=per_page)
        models = pagination.items
        
        # 格式化结果
        result = {
            'success': True,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages,
            'models': []
        }
        
        for model in models:
            result['models'].append({
                'id': model.id,
                'name': model.name,
                'description': model.description,
                'model_type': model.model_type,
                'default_params': model.default_params,
                'created_at': model.created_at.isoformat()
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f'获取模型列表失败: {str(e)}')
        return jsonify({'success': False, 'message': f'获取模型列表失败: {str(e)}'}), 500

@model_bp.route('/<int:model_id>', methods=['GET'])
def get_model(model_id):
    """
    获取单个模型详情
    """
    try:
        model = Model.query.get(model_id)
        if not model:
            return jsonify({'success': False, 'message': '模型不存在'}), 404
        
        return jsonify({
            'success': True,
            'model': {
                'id': model.id,
                'name': model.name,
                'description': model.description,
                'model_type': model.model_type,
                'default_params': model.default_params,
                'created_at': model.created_at.isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f'获取模型详情失败: {str(e)}')
        return jsonify({'success': False, 'message': f'获取模型详情失败: {str(e)}'}), 500

@model_bp.route('/', methods=['POST'])
def create_model():
    """
    创建新模型
    需要JWT认证，且只有管理员可以创建
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
        
        # 检查权限
        if not is_admin:
            return jsonify({'success': False, 'message': '只有管理员可以创建模型'}), 403
        
        # 获取请求数据
        data = request.get_json()
        
        # 验证必要字段
        if not all(k in data for k in ('name', 'model_type')):
            return jsonify({'success': False, 'message': '缺少必要字段'}), 400
        
        # 创建模型记录
        model = Model(
            name=data['name'],
            description=data.get('description', ''),
            model_type=data['model_type'],
            default_params=data.get('default_params', {}),
            created_at=datetime.utcnow()
        )
        
        db.session.add(model)
        db.session.commit()
        
        # 记录系统日志
        log = SystemLog(
            level='INFO',
            message=f'创建模型: {model.name}',
            source='model.create_model',
            user_id=user_id
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '模型创建成功',
            'model': {
                'id': model.id,
                'name': model.name,
                'model_type': model.model_type
            }
        }), 201
        
    except Exception as e:
        logger.error(f'创建模型失败: {str(e)}')
        return jsonify({'success': False, 'message': f'创建模型失败: {str(e)}'}), 500

@model_bp.route('/<int:model_id>', methods=['PUT'])
def update_model(model_id):
    """
    更新模型信息
    需要JWT认证，且只有管理员可以更新
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
        
        # 检查权限
        if not is_admin:
            return jsonify({'success': False, 'message': '只有管理员可以更新模型'}), 403
        
        # 查找模型
        model = Model.query.get(model_id)
        if not model:
            return jsonify({'success': False, 'message': '模型不存在'}), 404
        
        # 获取请求数据
        data = request.get_json()
        
        # 更新模型信息
        if 'name' in data:
            model.name = data['name']
        if 'description' in data:
            model.description = data['description']
        if 'default_params' in data:
            model.default_params = data['default_params']
        
        db.session.commit()
        
        # 记录系统日志
        log = SystemLog(
            level='INFO',
            message=f'更新模型: {model.name}',
            source='model.update_model',
            user_id=user_id
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '模型更新成功',
            'model': {
                'id': model.id,
                'name': model.name,
                'model_type': model.model_type
            }
        }), 200
        
    except Exception as e:
        logger.error(f'更新模型失败: {str(e)}')
        return jsonify({'success': False, 'message': f'更新模型失败: {str(e)}'}), 500

@model_bp.route('/types', methods=['GET'])
def get_model_types():
    """
    获取所有可用的模型类型
    """
    try:
        # 查询所有不同的模型类型
        model_types = db.session.query(Model.model_type).distinct().all()
        
        # 格式化结果
        types = [t[0] for t in model_types]
        
        return jsonify({
            'success': True,
            'model_types': types
        }), 200
        
    except Exception as e:
        logger.error(f'获取模型类型失败: {str(e)}')
        return jsonify({'success': False, 'message': f'获取模型类型失败: {str(e)}'}), 500