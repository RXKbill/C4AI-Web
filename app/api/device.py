from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import api_bp
from ..models import Device, DeviceMaintenance, WorkOrder
from .. import db
from datetime import datetime

@api_bp.route('/device/list', methods=['GET'])
@jwt_required()
def get_device_list():
    page = request.args.get('pageNum', 1, type=int)
    per_page = request.args.get('pageSize', 10, type=int)
    
    query = Device.query
    
    device_type = request.args.get('deviceType')
    if device_type:
        query = query.filter(Device.device_type == device_type)
    
    sub_type = request.args.get('subType')
    if sub_type:
        query = query.filter(Device.sub_type == sub_type)
    
    region = request.args.get('region')
    if region:
        query = query.filter(Device.region == region)
    
    health_status = request.args.get('healthStatus')
    if health_status:
        query = query.filter(Device.health_status == health_status)
    
    pagination = query.paginate(page=page, per_page=per_page)
    devices = pagination.items
    
    return jsonify({
        'code': 200,
        'msg': '查询成功',
        'total': pagination.total,
        'rows': [{
            'deviceId': device.device_id,
            'deviceType': device.device_type,
            'subType': device.sub_type,
            'serialNumber': device.serial_number,
            'location': device.location,
            'manufacturer': device.manufacturer,
            'region': device.region,
            'healthStatus': device.health_status,
            'lastMaintenance': device.last_maintenance.strftime('%Y-%m-%d %H:%M:%S') if device.last_maintenance else None,
            'createdAt': device.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for device in devices]
    })

@api_bp.route('/device', methods=['POST'])
@jwt_required()
def create_device():
    data = request.get_json()
    
    device = Device(
        device_type=data.get('deviceType'),
        sub_type=data.get('subType'),
        serial_number=data.get('serialNumber'),
        location=data.get('location'),
        manufacturer=data.get('manufacturer'),
        region=data.get('region'),
        health_status='normal'
    )
    
    db.session.add(device)
    
    try:
        db.session.commit()
        return jsonify({
            'code': 200,
            'msg': '创建成功',
            'deviceId': device.device_id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'创建失败: {str(e)}'
        }), 500

@api_bp.route('/device/<int:device_id>', methods=['PUT'])
@jwt_required()
def update_device(device_id):
    data = request.get_json()
    device = Device.query.get(device_id)
    
    if not device:
        return jsonify({
            'code': 404,
            'msg': '设备不存在'
        }), 404
    
    device.device_type = data.get('deviceType', device.device_type)
    device.sub_type = data.get('subType', device.sub_type)
    device.location = data.get('location', device.location)
    device.manufacturer = data.get('manufacturer', device.manufacturer)
    device.region = data.get('region', device.region)
    device.health_status = data.get('healthStatus', device.health_status)
    
    try:
        db.session.commit()
        return jsonify({
            'code': 200,
            'msg': '更新成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'更新失败: {str(e)}'
        }), 500

@api_bp.route('/device/<int:device_id>', methods=['DELETE'])
@jwt_required()
def delete_device(device_id):
    device = Device.query.get(device_id)
    
    if not device:
        return jsonify({
            'code': 404,
            'msg': '设备不存在'
        }), 404
    
    try:
        db.session.delete(device)
        db.session.commit()
        return jsonify({
            'code': 200,
            'msg': '删除成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'删除失败: {str(e)}'
        }), 500

@api_bp.route('/device/<int:device_id>/maintenance', methods=['GET'])
@jwt_required()
def get_device_maintenance(device_id):
    page = request.args.get('pageNum', 1, type=int)
    per_page = request.args.get('pageSize', 10, type=int)
    
    query = DeviceMaintenance.query.filter_by(device_id=device_id)
    
    maintenance_type = request.args.get('maintenanceType')
    if maintenance_type:
        query = query.filter(DeviceMaintenance.maintenance_type == maintenance_type)
    
    status = request.args.get('status')
    if status:
        query = query.filter(DeviceMaintenance.status == status)
    
    pagination = query.order_by(DeviceMaintenance.performed_at.desc()).paginate(page=page, per_page=per_page)
    records = pagination.items
    
    return jsonify({
        'code': 200,
        'msg': '查询成功',
        'total': pagination.total,
        'rows': [{
            'recordId': record.record_id,
            'deviceId': record.device_id,
            'workOrderId': record.work_order_id,
            'maintenanceType': record.maintenance_type,
            'description': record.description,
            'durationHours': record.duration_hours,
            'performedBy': record.performed_by,
            'performedAt': record.performed_at.strftime('%Y-%m-%d %H:%M:%S'),
            'status': record.status
        } for record in records]
    })

@api_bp.route('/device/<int:device_id>/maintenance', methods=['POST'])
@jwt_required()
def add_maintenance_record(device_id):
    data = request.get_json()
    
    record = DeviceMaintenance(
        device_id=device_id,
        work_order_id=data.get('workOrderId'),
        maintenance_type=data.get('maintenanceType'),
        description=data.get('description'),
        duration_hours=data.get('durationHours'),
        performed_by=get_jwt_identity(),
        status=data.get('status', 'completed')
    )
    
    db.session.add(record)
    
    try:
        # 更新设备的最后维护时间
        device = Device.query.get(device_id)
        if device:
            device.last_maintenance = datetime.now()
        
        db.session.commit()
        return jsonify({
            'code': 200,
            'msg': '添加成功',
            'recordId': record.record_id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'添加失败: {str(e)}'
        }), 500 