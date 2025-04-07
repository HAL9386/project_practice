from flask import Blueprint, request, jsonify, current_app
import os
import pandas as pd
from datetime import datetime
import logging
import jwt

from database.db import db
from database.models import Dataset, SystemLog

# 创建蓝图
dataset_bp = Blueprint('dataset', __name__)

# 创建日志记录器
logger = logging.getLogger(__name__)

# 数据集存储目录
DATASET_DIR = 'datasets'

@dataset_bp.route('/', methods=['GET'])
def get_datasets():
    """
    获取数据集列表
    """
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        category = request.args.get('category')
        is_preset = request.args.get('is_preset', type=lambda v: v.lower() == 'true')
        
        # 构建查询
        query = Dataset.query
        
        # 应用过滤条件
        if category:
            query = query.filter_by(category=category)
        if is_preset is not None:
            query = query.filter_by(is_preset=is_preset)
        
        # 执行分页查询
        pagination = query.paginate(page=page, per_page=per_page)
        datasets = pagination.items
        
        # 格式化结果
        result = {
            'success': True,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages,
            'datasets': []
        }
        
        for dataset in datasets:
            result['datasets'].append({
                'id': dataset.id,
                'name': dataset.name,
                'description': dataset.description,
                'category': dataset.category,
                'rows': dataset.rows,
                'columns': dataset.columns,
                'time_column': dataset.time_column,
                'value_column': dataset.value_column,
                'created_at': dataset.created_at.isoformat(),
                'is_preset': dataset.is_preset
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f'获取数据集列表失败: {str(e)}')
        return jsonify({'success': False, 'message': f'获取数据集列表失败: {str(e)}'}), 500

@dataset_bp.route('/<int:dataset_id>', methods=['GET'])
def get_dataset(dataset_id):
    """
    获取单个数据集详情
    """
    try:
        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            return jsonify({'success': False, 'message': '数据集不存在'}), 404
        
        # 读取数据集预览数据
        preview_data = None
        if dataset.file_path and os.path.exists(dataset.file_path):
            try:
                df = pd.read_csv(dataset.file_path)
                preview_data = df.head(10).to_dict('records')
            except Exception as e:
                logger.warning(f'读取数据集预览失败: {str(e)}')
        
        return jsonify({
            'success': True,
            'dataset': {
                'id': dataset.id,
                'name': dataset.name,
                'description': dataset.description,
                'category': dataset.category,
                'rows': dataset.rows,
                'columns': dataset.columns,
                'time_column': dataset.time_column,
                'value_column': dataset.value_column,
                'created_at': dataset.created_at.isoformat(),
                'is_preset': dataset.is_preset,
                'preview_data': preview_data
            }
        }), 200
        
    except Exception as e:
        logger.error(f'获取数据集详情失败: {str(e)}')
        return jsonify({'success': False, 'message': f'获取数据集详情失败: {str(e)}'}), 500

@dataset_bp.route('/', methods=['POST'])
def create_dataset():
    """
    创建新数据集（上传数据文件）
    需要JWT认证
    """
    try:
        # 确保数据集目录存在
        os.makedirs(DATASET_DIR, exist_ok=True)
        
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
                return jsonify({'success': False, 'message': '认证失败'}), 401
        else:
            return jsonify({'success': False, 'message': '需要认证'}), 401
        
        # 验证表单数据
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '未提供文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '未选择文件'}), 400
        
        # 验证文件类型
        if not file.filename.endswith('.csv'):
            return jsonify({'success': False, 'message': '仅支持CSV文件'}), 400
        
        # 保存文件
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        file_path = os.path.join(DATASET_DIR, f"{timestamp}_{file.filename}")
        file.save(file_path)
        
        # 解析CSV文件
        try:
            df = pd.read_csv(file_path)
            rows, columns = df.shape
            
            # 猜测时间列和值列
            time_column = df.columns[0]  # 假设第一列是时间列
            value_column = df.columns[1] if len(df.columns) > 1 else None  # 假设第二列是值列
            
            # 创建数据集记录
            dataset = Dataset(
                name=request.form.get('name', file.filename),
                description=request.form.get('description', ''),
                file_path=file_path,
                category=request.form.get('category', '其他'),
                rows=rows,
                columns=columns,
                time_column=time_column,
                value_column=value_column,
                is_preset=False,
                created_at=datetime.utcnow()
            )
            
            db.session.add(dataset)
            db.session.commit()
            
            # 记录系统日志
            log = SystemLog(
                level='INFO',
                message=f'上传数据集: {dataset.name}',
                source='dataset.create_dataset',
                user_id=user_id
            )
            db.session.add(log)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': '数据集创建成功',
                'dataset': {
                    'id': dataset.id,
                    'name': dataset.name,
                    'rows': rows,
                    'columns': columns
                }
            }), 201
            
        except Exception as e:
            # 如果解析失败，删除已上传的文件
            if os.path.exists(file_path):
                os.remove(file_path)
            logger.error(f'解析CSV文件失败: {str(e)}')
            return jsonify({'success': False, 'message': f'解析CSV文件失败: {str(e)}'}), 400
        
    except Exception as e:
        logger.error(f'创建数据集失败: {str(e)}')
        return jsonify({'success': False, 'message': f'创建数据集失败: {str(e)}'}), 500

@dataset_bp.route('/<int:dataset_id>', methods=['DELETE'])
def delete_dataset(dataset_id):
    """
    删除数据集
    需要JWT认证，且只有管理员或数据集创建者可以删除
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
        
        # 查找数据集
        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            return jsonify({'success': False, 'message': '数据集不存在'}), 404
        
        # 检查权限（预设数据集只有管理员可以删除）
        if dataset.is_preset and not is_admin:
            return jsonify({'success': False, 'message': '无权删除预设数据集'}), 403
        
        # 删除文件
        if dataset.file_path and os.path.exists(dataset.file_path) and not dataset.is_preset:
            os.remove(dataset.file_path)
        
        # 删除数据库记录
        db.session.delete(dataset)
        db.session.commit()
        
        # 记录系统日志
        log = SystemLog(
            level='INFO',
            message=f'删除数据集: {dataset.name}',
            source='dataset.delete_dataset',
            user_id=user_id
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '数据集删除成功'
        }), 200
        
    except Exception as e:
        logger.error(f'删除数据集失败: {str(e)}')
        return jsonify({'success': False, 'message': f'删除数据集失败: {str(e)}'}), 500