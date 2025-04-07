from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
import logging

from database.db import db
from database.models import User, SystemLog

# 创建蓝图
auth_bp = Blueprint('auth', __name__)

# 创建日志记录器
logger = logging.getLogger(__name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    用户注册
    """
    try:
        data = request.get_json()
        
        # 验证必要字段
        if not all(k in data for k in ('username', 'email', 'password')):
            return jsonify({'success': False, 'message': '缺少必要字段'}), 400
        
        # 检查用户名是否已存在
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'success': False, 'message': '用户名已存在'}), 400
        
        # 检查邮箱是否已存在
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'success': False, 'message': '邮箱已被注册'}), 400
        
        # 创建新用户
        new_user = User(
            username=data['username'],
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            is_admin=False,
            created_at=datetime.utcnow()
        )
        
        # 保存到数据库
        db.session.add(new_user)
        db.session.commit()
        
        # 记录系统日志
        log = SystemLog(
            level='INFO',
            message=f'新用户注册: {data["username"]}',
            source='auth.register'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '注册成功',
            'user': {
                'id': new_user.id,
                'username': new_user.username,
                'email': new_user.email
            }
        }), 201
        
    except Exception as e:
        logger.error(f'注册失败: {str(e)}')
        return jsonify({'success': False, 'message': f'注册失败: {str(e)}'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    用户登录
    """
    try:
        data = request.get_json()
        
        # 验证必要字段
        if not all(k in data for k in ('username', 'password')):
            return jsonify({'success': False, 'message': '缺少必要字段'}), 400
        
        # 查找用户
        user = User.query.filter_by(username=data['username']).first()
        
        # 验证用户和密码
        if not user or not check_password_hash(user.password_hash, data['password']):
            return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
        
        # 生成JWT令牌
        token_payload = {
            'user_id': user.id,
            'username': user.username,
            'is_admin': user.is_admin,
            'exp': datetime.utcnow() + timedelta(days=1)  # 令牌有效期1天
        }
        
        token = jwt.encode(
            token_payload,
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        
        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # 记录系统日志
        log = SystemLog(
            level='INFO',
            message=f'用户登录: {user.username}',
            source='auth.login',
            user_id=user.id
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '登录成功',
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_admin': user.is_admin
            }
        }), 200
        
    except Exception as e:
        logger.error(f'登录失败: {str(e)}')
        return jsonify({'success': False, 'message': f'登录失败: {str(e)}'}), 500

@auth_bp.route('/profile', methods=['GET'])
def get_profile():
    """
    获取用户个人资料
    需要JWT认证
    """
    try:
        # 从请求头获取令牌
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'message': '未提供有效的认证令牌'}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            # 解码令牌
            payload = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
            
            # 获取用户信息
            user_id = payload['user_id']
            user = User.query.get(user_id)
            
            if not user:
                return jsonify({'success': False, 'message': '用户不存在'}), 404
            
            return jsonify({
                'success': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_admin': user.is_admin,
                    'created_at': user.created_at.isoformat(),
                    'last_login': user.last_login.isoformat() if user.last_login else None
                }
            }), 200
            
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'message': '认证令牌已过期'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'message': '无效的认证令牌'}), 401
            
    except Exception as e:
        logger.error(f'获取用户资料失败: {str(e)}')
        return jsonify({'success': False, 'message': f'获取用户资料失败: {str(e)}'}), 500

@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    """
    修改密码
    需要JWT认证
    """
    try:
        # 从请求头获取令牌
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'message': '未提供有效的认证令牌'}), 401
        
        token = auth_header.split(' ')[1]
        data = request.get_json()
        
        # 验证必要字段
        if not all(k in data for k in ('old_password', 'new_password')):
            return jsonify({'success': False, 'message': '缺少必要字段'}), 400
        
        try:
            # 解码令牌
            payload = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
            
            # 获取用户信息
            user_id = payload['user_id']
            user = User.query.get(user_id)
            
            if not user:
                return jsonify({'success': False, 'message': '用户不存在'}), 404
            
            # 验证旧密码
            if not check_password_hash(user.password_hash, data['old_password']):
                return jsonify({'success': False, 'message': '旧密码错误'}), 400
            
            # 更新密码
            user.password_hash = generate_password_hash(data['new_password'])
            db.session.commit()
            
            # 记录系统日志
            log = SystemLog(
                level='INFO',
                message=f'用户修改密码: {user.username}',
                source='auth.change_password',
                user_id=user.id
            )
            db.session.add(log)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': '密码修改成功'
            }), 200
            
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'message': '认证令牌已过期'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'message': '无效的认证令牌'}), 401
            
    except Exception as e:
        logger.error(f'修改密码失败: {str(e)}')
        return jsonify({'success': False, 'message': f'修改密码失败: {str(e)}'}), 500