from datetime import datetime
from .db import db

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)  # 增加长度从512到1024
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # 关联关系
    tasks = db.relationship('Task', backref='user', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.username}>'

class Dataset(db.Model):
    """数据集模型"""
    __tablename__ = 'datasets'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(255))
    category = db.Column(db.String(50))  # 电力、交通、气候等
    rows = db.Column(db.Integer)
    columns = db.Column(db.Integer)
    time_column = db.Column(db.String(50))
    value_column = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_preset = db.Column(db.Boolean, default=False)
    
    # 关联关系
    tasks = db.relationship('Task', backref='dataset', lazy='dynamic')
    
    def __repr__(self):
        return f'<Dataset {self.name}>'

class Model(db.Model):
    """预测模型"""
    __tablename__ = 'models'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    model_type = db.Column(db.String(50))  # CrossGNN, HDMixer, LeRet等
    default_params = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联关系
    tasks = db.relationship('Task', backref='model', lazy='dynamic')
    
    def __repr__(self):
        return f'<Model {self.name}>'

class Task(db.Model):
    """预测任务"""
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    dataset_id = db.Column(db.Integer, db.ForeignKey('datasets.id'))
    model_id = db.Column(db.Integer, db.ForeignKey('models.id'))
    status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed
    hyperparams = db.Column(db.JSON)
    result_path = db.Column(db.String(255))
    metrics = db.Column(db.JSON)  # 存储MSE, MAE, RMSE等指标
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    duration = db.Column(db.Float)  # 执行时长（秒）
    
    def __repr__(self):
        return f'<Task {self.name}>'

# Template模型已移除，改为直接使用Task模型作为模板

class SystemLog(db.Model):
    """系统日志"""
    __tablename__ = 'system_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(20))  # INFO, WARNING, ERROR
    message = db.Column(db.Text)
    source = db.Column(db.String(100))  # 日志来源模块
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联
    user = db.relationship('User', backref='logs')
    
    def __repr__(self):
        return f'<SystemLog {self.id}: {self.level}>'