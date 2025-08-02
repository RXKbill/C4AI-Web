from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
import json

# 用户表
class User(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50), unique=True, nullable=False)  # 用户名
    nick_name = db.Column(db.String(50))  # 昵称
    email = db.Column(db.String(120), unique=True, nullable=False)
    phonenumber = db.Column(db.String(11))  # 手机号
    sex = db.Column(db.String(1), default='0')  # 0男 1女 2未知
    avatar = db.Column(db.String(100))  # 头像
    password_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey('roles_permissions.role_id'))
    last_login = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='0')  # 0正常 1停用
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, onupdate=datetime.now)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

# 用户角色关联表
user_role = db.Table('user_role',
    db.Column('user_id', db.Integer, db.ForeignKey('users.user_id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles_permissions.role_id'), primary_key=True)
)

# 角色与权限表
class RolePermission(db.Model):
    __tablename__ = 'roles_permissions'
    
    role_id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(50), unique=True, nullable=False)
    permissions = db.Column(db.JSON)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, onupdate=datetime.now)

# 设备台账表
class Device(db.Model):
    __tablename__ = 'devices'
    
    device_id = db.Column(db.Integer, primary_key=True)
    device_type = db.Column(db.String(50), nullable=False)
    sub_type = db.Column(db.String(50))
    serial_number = db.Column(db.String(100), unique=True)
    location = db.Column(db.String(200))
    manufacturer = db.Column(db.String(100))
    region = db.Column(db.String(50))
    health_status = db.Column(db.String(20))
    last_maintenance = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, onupdate=datetime.now)

# 设备维护记录表
class DeviceMaintenance(db.Model):
    __tablename__ = 'device_maintenance'
    
    record_id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.device_id'))
    work_order_id = db.Column(db.Integer, db.ForeignKey('work_orders.work_order_id'))
    maintenance_type = db.Column(db.String(50))
    description = db.Column(db.Text)
    duration_hours = db.Column(db.Float)
    performed_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    performed_at = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(20))

# 实时数据表
class RealtimeData(db.Model):
    __tablename__ = 'realtime_data'
    
    data_id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.device_id'))
    task_id = db.Column(db.Integer, db.ForeignKey('prediction_tasks.task_id'))
    timestamp = db.Column(db.DateTime, default=datetime.now)
    wind_speed = db.Column(db.Float)
    temperature = db.Column(db.Float)
    power_output = db.Column(db.Float)
    quality_status = db.Column(db.String(20))
    data_source = db.Column(db.String(50))

# 气象数据表
class WeatherData(db.Model):
    __tablename__ = 'weather_data'
    
    weather_id = db.Column(db.Integer, primary_key=True)
    station_id = db.Column(db.String(50))
    region = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.now)
    wind_speed = db.Column(db.Float)
    solar_radiation = db.Column(db.Float)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    quality_status = db.Column(db.String(20))

# 预测任务表
class PredictionTask(db.Model):
    __tablename__ = 'prediction_tasks'
    
    task_id = db.Column(db.Integer, primary_key=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    task_type = db.Column(db.String(50))
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    model_version = db.Column(db.String(50))
    parameters = db.Column(db.JSON)
    target = db.Column(db.String(100))
    scenario = db.Column(db.String(50))
    status = db.Column(db.String(20))

# 预测结果表
class PredictionResult(db.Model):
    __tablename__ = 'prediction_results'
    
    result_id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('prediction_tasks.task_id'))
    timestamp = db.Column(db.DateTime)
    predicted_value = db.Column(db.Float)
    confidence = db.Column(db.Float)
    actual_value = db.Column(db.Float)
    error_rate = db.Column(db.Float)

# 阈值配置表
class ThresholdConfiguration(db.Model):
    __tablename__ = 'threshold_configurations'
    
    threshold_id = db.Column(db.Integer, primary_key=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    name = db.Column(db.String(100))
    value = db.Column(db.Float)
    unit = db.Column(db.String(20))
    device_type = db.Column(db.String(50))
    scenario = db.Column(db.String(50))
    effective_from = db.Column(db.DateTime)
    effective_to = db.Column(db.DateTime)
    status = db.Column(db.String(20))

# 模型参数表
class ModelParameter(db.Model):
    __tablename__ = 'model_parameters'
    
    model_param_id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('prediction_tasks.task_id'))
    model_name = db.Column(db.String(100))
    param_name = db.Column(db.String(100))
    param_value = db.Column(db.String(500))
    version = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)

# 工单表
class WorkOrder(db.Model):
    __tablename__ = 'work_orders'
    
    work_order_id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.device_id'))
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    task_id = db.Column(db.Integer, db.ForeignKey('prediction_tasks.task_id'))
    alert_id = db.Column(db.Integer)
    title = db.Column(db.String(200))
    type = db.Column(db.String(50))
    priority = db.Column(db.String(20))
    status = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, onupdate=datetime.now)

# 无人机任务表
class DroneTask(db.Model):
    __tablename__ = 'drone_tasks'
    
    drone_task_id = db.Column(db.Integer, primary_key=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    task_type = db.Column(db.String(50))
    device_ids = db.Column(db.JSON)
    path_coordinates = db.Column(db.JSON)
    status = db.Column(db.String(20))
    alert_flag = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    completed_at = db.Column(db.DateTime)

# 无人机数据表
class DroneData(db.Model):
    __tablename__ = 'drone_data'
    
    drone_data_id = db.Column(db.Integer, primary_key=True)
    drone_task_id = db.Column(db.Integer, db.ForeignKey('drone_tasks.drone_task_id'))
    device_id = db.Column(db.Integer, db.ForeignKey('devices.device_id'))
    sensor_data = db.Column(db.JSON)
    image_path = db.Column(db.String(500))
    video_path = db.Column(db.String(500))
    quality_status = db.Column(db.String(20))
    collected_at = db.Column(db.DateTime, default=datetime.now)

# 系统日志表
class SystemLog(db.Model):
    __tablename__ = 'system_logs'
    
    log_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    operation_type = db.Column(db.String(50))
    related_id = db.Column(db.Integer)
    ip_address = db.Column(db.String(50))
    device_type = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.now)
    details = db.Column(db.JSON)

# 能源交易记录表
class EnergyTrade(db.Model):
    __tablename__ = 'energy_trades'
    
    trade_id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    seller_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    prediction_id = db.Column(db.Integer, db.ForeignKey('prediction_results.result_id'))
    trade_time = db.Column(db.DateTime, default=datetime.now)
    trade_type = db.Column(db.String(50))
    price = db.Column(db.Float)
    volume = db.Column(db.Float)
    market_type = db.Column(db.String(50))
    status = db.Column(db.String(20))

# 市场数据表
class MarketData(db.Model):
    __tablename__ = 'market_data'
    
    market_data_id = db.Column(db.Integer, primary_key=True)
    market_type = db.Column(db.String(50))
    price = db.Column(db.Float)
    supply_demand = db.Column(db.Float)
    region = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.now)

# 分时电价策略表
class TimeBasedPricing(db.Model):
    __tablename__ = 'time_based_pricing'
    
    pricing_id = db.Column(db.Integer, primary_key=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    strategy_name = db.Column(db.String(100))
    time_periods = db.Column(db.JSON)
    region = db.Column(db.String(50))
    status = db.Column(db.String(20))
    effective_from = db.Column(db.DateTime)
    effective_to = db.Column(db.DateTime)

# 规则配置表
class BusinessRule(db.Model):
    __tablename__ = 'business_rules'
    
    rule_id = db.Column(db.Integer, primary_key=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    rule_name = db.Column(db.String(100))
    scenario = db.Column(db.String(50))
    condition_expr = db.Column(db.Text)
    action_type = db.Column(db.String(50))
    priority = db.Column(db.Integer)
    status = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.now)

# 控制指令表
class ControlCommand(db.Model):
    __tablename__ = 'control_commands'
    
    command_id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('prediction_tasks.task_id'))
    rule_id = db.Column(db.Integer, db.ForeignKey('business_rules.rule_id'))
    command_type = db.Column(db.String(50))
    target_device_id = db.Column(db.Integer, db.ForeignKey('devices.device_id'))
    parameters = db.Column(db.JSON)
    status = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.now)
    executed_at = db.Column(db.DateTime)

# 决策日志表
class DecisionLog(db.Model):
    __tablename__ = 'decision_logs'
    
    log_id = db.Column(db.Integer, primary_key=True)
    rule_id = db.Column(db.Integer, db.ForeignKey('business_rules.rule_id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    input_data = db.Column(db.JSON)
    output_commands = db.Column(db.JSON)
    execution_result = db.Column(db.String(20))
    error_details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)

# 策略配置表
class BusinessStrategy(db.Model):
    __tablename__ = 'business_strategies'
    
    strategy_id = db.Column(db.Integer, primary_key=True)
    rule_id = db.Column(db.Integer, db.ForeignKey('business_rules.rule_id'))
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    strategy_name = db.Column(db.String(100))
    parameters = db.Column(db.JSON)
    version = db.Column(db.String(50))
    scenario = db.Column(db.String(50))
    status = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.now)

# 异常处理记录表
class ExceptionHandling(db.Model):
    __tablename__ = 'exception_handling'
    
    exception_id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.device_id'))
    command_id = db.Column(db.Integer, db.ForeignKey('control_commands.command_id'))
    exception_type = db.Column(db.String(50))
    description = db.Column(db.Text)
    status = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.now)
    resolved_at = db.Column(db.DateTime)

# 策略执行记录表
class StrategyExecution(db.Model):
    __tablename__ = 'strategy_execution'
    
    execution_id = db.Column(db.Integer, primary_key=True)
    strategy_id = db.Column(db.Integer, db.ForeignKey('business_strategies.strategy_id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    execution_time = db.Column(db.DateTime, default=datetime.now)
    input_params = db.Column(db.JSON)
    output_result = db.Column(db.JSON)
    status = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.now)

class Notification(db.Model):
    """通知表"""
    __tablename__ = 'sys_notification'
    
    notification_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('sys_user.user_id'), nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # 通知类型：system/alarm/task等
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), nullable=False, default='normal')  # high/normal/low
    read_status = db.Column(db.String(20), nullable=False, default='unread')  # read/unread
    read_time = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<Notification {self.notification_id}>'

class NotificationSubscription(db.Model):
    """通知订阅表"""
    __tablename__ = 'sys_notification_subscription'
    
    subscription_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('sys_user.user_id'), nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # 订阅的通知类型
    channel = db.Column(db.String(20), nullable=False)  # email/sms/app_push
    config = db.Column(db.JSON)  # 渠道配置，如邮箱地址、手机号等
    status = db.Column(db.String(20), nullable=False, default='enabled')  # enabled/disabled
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<NotificationSubscription {self.subscription_id}>'

# 部门表
class Department(db.Model):
    __tablename__ = 'sys_dept'
    
    dept_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    parent_id = db.Column(db.Integer, default=0)
    dept_name = db.Column(db.String(50), nullable=False)
    order_num = db.Column(db.Integer, default=0)
    leader = db.Column(db.String(20))
    phone = db.Column(db.String(11))
    email = db.Column(db.String(50))
    status = db.Column(db.String(1), default='0')  # 0正常 1停用
    del_flag = db.Column(db.String(1), default='0')  # 0存在 2删除
    create_by = db.Column(db.String(64))
    create_time = db.Column(db.DateTime, default=datetime.now)
    update_by = db.Column(db.String(64))
    update_time = db.Column(db.DateTime, onupdate=datetime.now)

    def __repr__(self):
        return f'<Department {self.dept_name}>'

# 告警表
class Alarm(db.Model):
    __tablename__ = 'sys_alarm'
    
    alarm_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.device_id'), nullable=False)
    alarm_type = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20), nullable=False)  # high/medium/low
    description = db.Column(db.Text, nullable=False)
    alarm_time = db.Column(db.DateTime, nullable=False, default=datetime.now)
    status = db.Column(db.String(20), default='active')  # active/handled
    handled_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    handle_time = db.Column(db.DateTime)
    handle_result = db.Column(db.Text)

    def __repr__(self):
        return f'<Alarm {self.alarm_id}>'

# 告警规则表
class AlarmRule(db.Model):
    __tablename__ = 'sys_alarm_rule'
    
    rule_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rule_name = db.Column(db.String(100), nullable=False)
    device_type = db.Column(db.String(50), nullable=False)
    alarm_type = db.Column(db.String(50), nullable=False)
    conditions = db.Column(db.JSON, nullable=False)
    severity = db.Column(db.String(20), default='medium')
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='enabled')  # enabled/disabled
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<AlarmRule {self.rule_name}>'

# 无人机表
class Drone(db.Model):
    __tablename__ = 'sys_drone'
    
    drone_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    drone_code = db.Column(db.String(50), unique=True, nullable=False)
    model = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='available')  # available/maintenance/offline
    battery_level = db.Column(db.Float, default=100.0)
    region = db.Column(db.String(50))
    current_location = db.Column(db.String(200))
    last_maintenance = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, onupdate=datetime.now)

    def __repr__(self):
        return f'<Drone {self.drone_code}>'

# 无人机巡检数据表
class DroneInspectionData(db.Model):
    __tablename__ = 'sys_drone_inspection_data'
    
    data_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_id = db.Column(db.Integer, db.ForeignKey('drone_tasks.drone_task_id'), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.device_id'), nullable=False)
    data_type = db.Column(db.String(50), nullable=False)  # image/video/sensor
    data_content = db.Column(db.JSON, nullable=False)
    location = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.now)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))

    def __repr__(self):
        return f'<DroneInspectionData {self.data_id}>'

# 工单图片表
class WorkOrderImage(db.Model):
    __tablename__ = 'sys_workorder_image'
    
    image_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    work_order_id = db.Column(db.Integer, db.ForeignKey('work_orders.work_order_id'), nullable=False)
    image_path = db.Column(db.String(500), nullable=False)
    image_type = db.Column(db.String(50))  # before/after/other
    description = db.Column(db.Text)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    uploaded_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<WorkOrderImage {self.image_id}>'

# 菜单表
class Menu(db.Model):
    __tablename__ = 'sys_menu'
    
    menu_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    menu_name = db.Column(db.String(50), nullable=False)
    parent_id = db.Column(db.Integer, default=0)
    order_num = db.Column(db.Integer, default=0)
    path = db.Column(db.String(200))
    component = db.Column(db.String(255))
    is_frame = db.Column(db.Integer, default=1)
    is_cache = db.Column(db.Integer, default=0)
    menu_type = db.Column(db.String(1), default='')  # M目录 C菜单 F按钮
    visible = db.Column(db.String(1), default='0')  # 0显示 1隐藏
    status = db.Column(db.String(1), default='0')  # 0正常 1停用
    perms = db.Column(db.String(100))
    icon = db.Column(db.String(100), default='#')
    create_by = db.Column(db.String(64))
    create_time = db.Column(db.DateTime, default=datetime.now)
    update_by = db.Column(db.String(64))
    update_time = db.Column(db.DateTime, onupdate=datetime.now)
    remark = db.Column(db.String(500))

    def __repr__(self):
        return f'<Menu {self.menu_name}>'

# 特征工程表
class FeatureEngineering(db.Model):
    __tablename__ = 'sys_feature_engineering'
    
    engineering_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    dataset_id = db.Column(db.Integer, nullable=False)
    config = db.Column(db.JSON, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending/running/completed/failed
    error_message = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, onupdate=datetime.now)

    def __repr__(self):
        return f'<FeatureEngineering {self.engineering_id}>'

# 数据预处理表
class DataPreprocessing(db.Model):
    __tablename__ = 'sys_data_preprocessing'
    
    preprocessing_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    dataset_id = db.Column(db.Integer, nullable=False)
    config = db.Column(db.JSON, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending/running/completed/failed
    error_message = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, onupdate=datetime.now)

    def __repr__(self):
        return f'<DataPreprocessing {self.preprocessing_id}>'

# 数据集表
class Dataset(db.Model):
    __tablename__ = 'sys_dataset'
    
    dataset_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    source_type = db.Column(db.String(50), nullable=False)  # database/file/api
    source_config = db.Column(db.JSON, nullable=False)
    feature_config = db.Column(db.JSON)
    status = db.Column(db.String(20), default='pending')  # pending/processing/completed/failed
    statistics = db.Column(db.JSON)  # 数据集统计信息
    schema = db.Column(db.JSON)  # 数据模式
    error_message = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, onupdate=datetime.now)

    def __repr__(self):
        return f'<Dataset {self.name}>'

# 模型服务表
class ModelService(db.Model):
    __tablename__ = 'sys_model_service'
    
    service_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    service_name = db.Column(db.String(100), nullable=False)
    model_type = db.Column(db.String(50), nullable=False)
    version = db.Column(db.String(50), nullable=False)
    endpoint = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='active')  # active/inactive
    config = db.Column(db.JSON)
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, onupdate=datetime.now)

    def __repr__(self):
        return f'<ModelService {self.service_name}>'

# 模型版本表
class ModelVersion(db.Model):
    __tablename__ = 'sys_model_version'
    
    version_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    model_type = db.Column(db.String(50), nullable=False)
    version_number = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    parameters = db.Column(db.JSON)
    performance_metrics = db.Column(db.JSON)
    status = db.Column(db.String(20), default='active')  # active/inactive
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<ModelVersion {self.version_number}>'

# 模型训练表
class ModelTraining(db.Model):
    __tablename__ = 'sys_model_training'
    
    training_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    model_type = db.Column(db.String(50), nullable=False)
    dataset_config = db.Column(db.JSON, nullable=False)
    training_params = db.Column(db.JSON, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending/running/completed/failed
    progress = db.Column(db.Float, default=0.0)  # 训练进度 0-100
    metrics = db.Column(db.JSON)  # 训练指标
    error_message = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, onupdate=datetime.now)

    def __repr__(self):
        return f'<ModelTraining {self.training_id}>'

# 模型部署表
class ModelDeployment(db.Model):
    __tablename__ = 'sys_model_deployment'
    
    deployment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    version_id = db.Column(db.Integer, db.ForeignKey('sys_model_version.version_id'), nullable=False)
    environment = db.Column(db.String(50), default='production')  # production/staging/test
    config = db.Column(db.JSON)
    status = db.Column(db.String(20), default='pending')  # pending/deploying/active/failed
    error_message = db.Column(db.Text)
    deployed_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    deployed_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, onupdate=datetime.now)

    def __repr__(self):
        return f'<ModelDeployment {self.deployment_id}>' 