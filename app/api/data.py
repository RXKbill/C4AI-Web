from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import api_bp
from ..models import RealtimeData, WeatherData, PredictionTask, PredictionResult
from .. import db
from datetime import datetime

@api_bp.route('/data/realtime/list', methods=['GET'])
@jwt_required()
def get_realtime_data():
    page = request.args.get('pageNum', 1, type=int)
    per_page = request.args.get('pageSize', 10, type=int)
    
    query = RealtimeData.query
    
    device_id = request.args.get('deviceId', type=int)
    if device_id:
        query = query.filter(RealtimeData.device_id == device_id)
    
    start_time = request.args.get('startTime')
    if start_time:
        query = query.filter(RealtimeData.timestamp >= start_time)
    
    end_time = request.args.get('endTime')
    if end_time:
        query = query.filter(RealtimeData.timestamp <= end_time)
    
    pagination = query.order_by(RealtimeData.timestamp.desc()).paginate(page=page, per_page=per_page)
    data_list = pagination.items
    
    return jsonify({
        'code': 200,
        'msg': '查询成功',
        'total': pagination.total,
        'rows': [{
            'dataId': data.data_id,
            'deviceId': data.device_id,
            'timestamp': data.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'windSpeed': data.wind_speed,
            'temperature': data.temperature,
            'powerOutput': data.power_output,
            'qualityStatus': data.quality_status
        } for data in data_list]
    })

@api_bp.route('/data/weather/list', methods=['GET'])
@jwt_required()
def get_weather_data():
    page = request.args.get('pageNum', 1, type=int)
    per_page = request.args.get('pageSize', 10, type=int)
    
    query = WeatherData.query
    
    region = request.args.get('region')
    if region:
        query = query.filter(WeatherData.region == region)
    
    start_time = request.args.get('startTime')
    if start_time:
        query = query.filter(WeatherData.timestamp >= start_time)
    
    end_time = request.args.get('endTime')
    if end_time:
        query = query.filter(WeatherData.timestamp <= end_time)
    
    pagination = query.order_by(WeatherData.timestamp.desc()).paginate(page=page, per_page=per_page)
    data_list = pagination.items
    
    return jsonify({
        'code': 200,
        'msg': '查询成功',
        'total': pagination.total,
        'rows': [{
            'weatherId': data.weather_id,
            'stationId': data.station_id,
            'region': data.region,
            'timestamp': data.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'windSpeed': data.wind_speed,
            'solarRadiation': data.solar_radiation,
            'temperature': data.temperature,
            'humidity': data.humidity,
            'qualityStatus': data.quality_status
        } for data in data_list]
    })

@api_bp.route('/prediction/task/list', methods=['GET'])
@jwt_required()
def get_prediction_tasks():
    page = request.args.get('pageNum', 1, type=int)
    per_page = request.args.get('pageSize', 10, type=int)
    
    query = PredictionTask.query
    
    task_type = request.args.get('taskType')
    if task_type:
        query = query.filter(PredictionTask.task_type == task_type)
    
    status = request.args.get('status')
    if status:
        query = query.filter(PredictionTask.status == status)
    
    pagination = query.order_by(PredictionTask.start_time.desc()).paginate(page=page, per_page=per_page)
    tasks = pagination.items
    
    return jsonify({
        'code': 200,
        'msg': '查询成功',
        'total': pagination.total,
        'rows': [{
            'taskId': task.task_id,
            'taskType': task.task_type,
            'startTime': task.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'endTime': task.end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'modelVersion': task.model_version,
            'target': task.target,
            'scenario': task.scenario,
            'status': task.status
        } for task in tasks]
    })

@api_bp.route('/prediction/task', methods=['POST'])
@jwt_required()
def create_prediction_task():
    data = request.get_json()
    
    task = PredictionTask(
        created_by=get_jwt_identity(),
        task_type=data.get('taskType'),
        start_time=datetime.strptime(data.get('startTime'), '%Y-%m-%d %H:%M:%S'),
        end_time=datetime.strptime(data.get('endTime'), '%Y-%m-%d %H:%M:%S'),
        model_version=data.get('modelVersion'),
        parameters=data.get('parameters'),
        target=data.get('target'),
        scenario=data.get('scenario'),
        status='pending'
    )
    
    db.session.add(task)
    
    try:
        db.session.commit()
        return jsonify({
            'code': 200,
            'msg': '创建成功',
            'taskId': task.task_id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'创建失败: {str(e)}'
        }), 500

@api_bp.route('/prediction/result/list', methods=['GET'])
@jwt_required()
def get_prediction_results():
    page = request.args.get('pageNum', 1, type=int)
    per_page = request.args.get('pageSize', 10, type=int)
    
    query = PredictionResult.query
    
    task_id = request.args.get('taskId', type=int)
    if task_id:
        query = query.filter(PredictionResult.task_id == task_id)
    
    pagination = query.order_by(PredictionResult.timestamp.desc()).paginate(page=page, per_page=per_page)
    results = pagination.items
    
    return jsonify({
        'code': 200,
        'msg': '查询成功',
        'total': pagination.total,
        'rows': [{
            'resultId': result.result_id,
            'taskId': result.task_id,
            'timestamp': result.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'predictedValue': result.predicted_value,
            'confidence': result.confidence,
            'actualValue': result.actual_value,
            'errorRate': result.error_rate
        } for result in results]
    })

@api_bp.route('/prediction/result', methods=['POST'])
@jwt_required()
def add_prediction_result():
    data = request.get_json()
    
    result = PredictionResult(
        task_id=data.get('taskId'),
        timestamp=datetime.strptime(data.get('timestamp'), '%Y-%m-%d %H:%M:%S'),
        predicted_value=data.get('predictedValue'),
        confidence=data.get('confidence'),
        actual_value=data.get('actualValue'),
        error_rate=data.get('errorRate')
    )
    
    db.session.add(result)
    
    try:
        db.session.commit()
        return jsonify({
            'code': 200,
            'msg': '添加成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'添加失败: {str(e)}'
        }), 500 