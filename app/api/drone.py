from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import api_bp
from ..models import Drone, DroneTask, DroneInspectionData
from .. import db
from datetime import datetime
import json

@api_bp.route('/drone/list', methods=['GET'])
@jwt_required()
def get_drone_list():
    page = request.args.get('pageNum', 1, type=int)
    per_page = request.args.get('pageSize', 10, type=int)
    
    query = Drone.query
    
    status = request.args.get('status')
    if status:
        query = query.filter(Drone.status == status)
    
    region = request.args.get('region')
    if region:
        query = query.filter(Drone.region == region)
    
    pagination = query.paginate(page=page, per_page=per_page)
    drones = pagination.items
    
    return jsonify({
        'code': 200,
        'msg': '查询成功',
        'total': pagination.total,
        'rows': [{
            'droneId': drone.drone_id,
            'droneCode': drone.drone_code,
            'model': drone.model,
            'status': drone.status,
            'batteryLevel': drone.battery_level,
            'region': drone.region,
            'currentLocation': drone.current_location,
            'lastMaintenance': drone.last_maintenance.strftime('%Y-%m-%d %H:%M:%S') if drone.last_maintenance else None
        } for drone in drones]
    })

@api_bp.route('/drone/task/create', methods=['POST'])
@jwt_required()
def create_drone_task():
    data = request.get_json()
    
    task = DroneTask(
        drone_id=data.get('droneId'),
        task_type=data.get('taskType'),
        priority=data.get('priority', 'normal'),
        inspection_route=data.get('inspectionRoute'),
        target_devices=data.get('targetDevices'),
        scheduled_start_time=datetime.strptime(data.get('scheduledStartTime'), '%Y-%m-%d %H:%M:%S') if data.get('scheduledStartTime') else None,
        status='pending',
        created_by=get_jwt_identity()
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

@api_bp.route('/drone/task/list', methods=['GET'])
@jwt_required()
def get_drone_tasks():
    page = request.args.get('pageNum', 1, type=int)
    per_page = request.args.get('pageSize', 10, type=int)
    
    query = DroneTask.query
    
    drone_id = request.args.get('droneId', type=int)
    if drone_id:
        query = query.filter(DroneTask.drone_id == drone_id)
    
    task_type = request.args.get('taskType')
    if task_type:
        query = query.filter(DroneTask.task_type == task_type)
    
    status = request.args.get('status')
    if status:
        query = query.filter(DroneTask.status == status)
    
    priority = request.args.get('priority')
    if priority:
        query = query.filter(DroneTask.priority == priority)
    
    pagination = query.order_by(DroneTask.created_at.desc()).paginate(page=page, per_page=per_page)
    tasks = pagination.items
    
    return jsonify({
        'code': 200,
        'msg': '查询成功',
        'total': pagination.total,
        'rows': [{
            'taskId': task.task_id,
            'droneId': task.drone_id,
            'taskType': task.task_type,
            'priority': task.priority,
            'inspectionRoute': task.inspection_route,
            'targetDevices': task.target_devices,
            'scheduledStartTime': task.scheduled_start_time.strftime('%Y-%m-%d %H:%M:%S') if task.scheduled_start_time else None,
            'actualStartTime': task.actual_start_time.strftime('%Y-%m-%d %H:%M:%S') if task.actual_start_time else None,
            'completedTime': task.completed_time.strftime('%Y-%m-%d %H:%M:%S') if task.completed_time else None,
            'status': task.status,
            'progress': task.progress,
            'createdBy': task.created_by,
            'createdAt': task.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for task in tasks]
    })

@api_bp.route('/drone/task/<int:task_id>/control', methods=['POST'])
@jwt_required()
def control_drone_task(task_id):
    data = request.get_json()
    task = DroneTask.query.get(task_id)
    
    if not task:
        return jsonify({
            'code': 404,
            'msg': '任务不存在'
        }), 404
    
    action = data.get('action')
    if action not in ['start', 'pause', 'resume', 'cancel']:
        return jsonify({
            'code': 400,
            'msg': '不支持的操作'
        }), 400
    
    try:
        if action == 'start':
            task.status = 'running'
            task.actual_start_time = datetime.now()
        elif action == 'pause':
            task.status = 'paused'
        elif action == 'resume':
            task.status = 'running'
        elif action == 'cancel':
            task.status = 'cancelled'
        
        db.session.commit()
        return jsonify({
            'code': 200,
            'msg': '操作成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'操作失败: {str(e)}'
        }), 500

@api_bp.route('/drone/inspection/data', methods=['POST'])
@jwt_required()
def upload_inspection_data():
    data = request.get_json()
    
    inspection_data = DroneInspectionData(
        task_id=data.get('taskId'),
        device_id=data.get('deviceId'),
        data_type=data.get('dataType'),
        data_content=data.get('dataContent'),
        location=data.get('location'),
        timestamp=datetime.now(),
        uploaded_by=get_jwt_identity()
    )
    
    db.session.add(inspection_data)
    
    try:
        db.session.commit()
        return jsonify({
            'code': 200,
            'msg': '上传成功',
            'dataId': inspection_data.data_id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'上传失败: {str(e)}'
        }), 500

@api_bp.route('/drone/inspection/data/list', methods=['GET'])
@jwt_required()
def get_inspection_data():
    page = request.args.get('pageNum', 1, type=int)
    per_page = request.args.get('pageSize', 10, type=int)
    
    query = DroneInspectionData.query
    
    task_id = request.args.get('taskId', type=int)
    if task_id:
        query = query.filter(DroneInspectionData.task_id == task_id)
    
    device_id = request.args.get('deviceId', type=int)
    if device_id:
        query = query.filter(DroneInspectionData.device_id == device_id)
    
    data_type = request.args.get('dataType')
    if data_type:
        query = query.filter(DroneInspectionData.data_type == data_type)
    
    start_time = request.args.get('startTime')
    if start_time:
        query = query.filter(DroneInspectionData.timestamp >= start_time)
    
    end_time = request.args.get('endTime')
    if end_time:
        query = query.filter(DroneInspectionData.timestamp <= end_time)
    
    pagination = query.order_by(DroneInspectionData.timestamp.desc()).paginate(page=page, per_page=per_page)
    data_list = pagination.items
    
    return jsonify({
        'code': 200,
        'msg': '查询成功',
        'total': pagination.total,
        'rows': [{
            'dataId': data.data_id,
            'taskId': data.task_id,
            'deviceId': data.device_id,
            'dataType': data.data_type,
            'dataContent': data.data_content,
            'location': data.location,
            'timestamp': data.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'uploadedBy': data.uploaded_by
        } for data in data_list]
    }) 