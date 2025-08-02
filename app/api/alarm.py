from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import api_bp
from ..models import Alarm, AlarmRule
from .. import db
from datetime import datetime

@api_bp.route('/alarm/list', methods=['GET'])
@jwt_required()
def get_alarm_list():
    page = request.args.get('pageNum', 1, type=int)
    per_page = request.args.get('pageSize', 10, type=int)
    
    query = Alarm.query
    
    device_id = request.args.get('deviceId', type=int)
    if device_id:
        query = query.filter(Alarm.device_id == device_id)
    
    alarm_type = request.args.get('alarmType')
    if alarm_type:
        query = query.filter(Alarm.alarm_type == alarm_type)
    
    severity = request.args.get('severity')
    if severity:
        query = query.filter(Alarm.severity == severity)
    
    status = request.args.get('status')
    if status:
        query = query.filter(Alarm.status == status)
    
    start_time = request.args.get('startTime')
    if start_time:
        query = query.filter(Alarm.alarm_time >= start_time)
    
    end_time = request.args.get('endTime')
    if end_time:
        query = query.filter(Alarm.alarm_time <= end_time)
    
    pagination = query.order_by(Alarm.alarm_time.desc()).paginate(page=page, per_page=per_page)
    alarms = pagination.items
    
    return jsonify({
        'code': 200,
        'msg': '查询成功',
        'total': pagination.total,
        'rows': [{
            'alarmId': alarm.alarm_id,
            'deviceId': alarm.device_id,
            'alarmType': alarm.alarm_type,
            'severity': alarm.severity,
            'description': alarm.description,
            'alarmTime': alarm.alarm_time.strftime('%Y-%m-%d %H:%M:%S'),
            'status': alarm.status,
            'handledBy': alarm.handled_by,
            'handleTime': alarm.handle_time.strftime('%Y-%m-%d %H:%M:%S') if alarm.handle_time else None,
            'handleResult': alarm.handle_result
        } for alarm in alarms]
    })

@api_bp.route('/alarm/rule/list', methods=['GET'])
@jwt_required()
def get_alarm_rules():
    page = request.args.get('pageNum', 1, type=int)
    per_page = request.args.get('pageSize', 10, type=int)
    
    query = AlarmRule.query
    
    device_type = request.args.get('deviceType')
    if device_type:
        query = query.filter(AlarmRule.device_type == device_type)
    
    alarm_type = request.args.get('alarmType')
    if alarm_type:
        query = query.filter(AlarmRule.alarm_type == alarm_type)
    
    status = request.args.get('status')
    if status:
        query = query.filter(AlarmRule.status == status)
    
    pagination = query.paginate(page=page, per_page=per_page)
    rules = pagination.items
    
    return jsonify({
        'code': 200,
        'msg': '查询成功',
        'total': pagination.total,
        'rows': [{
            'ruleId': rule.rule_id,
            'ruleName': rule.rule_name,
            'deviceType': rule.device_type,
            'alarmType': rule.alarm_type,
            'conditions': rule.conditions,
            'severity': rule.severity,
            'description': rule.description,
            'status': rule.status,
            'createdBy': rule.created_by,
            'createdAt': rule.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for rule in rules]
    })

@api_bp.route('/alarm/rule', methods=['POST'])
@jwt_required()
def create_alarm_rule():
    data = request.get_json()
    
    rule = AlarmRule(
        rule_name=data.get('ruleName'),
        device_type=data.get('deviceType'),
        alarm_type=data.get('alarmType'),
        conditions=data.get('conditions'),
        severity=data.get('severity'),
        description=data.get('description'),
        status=data.get('status', 'enabled'),
        created_by=get_jwt_identity()
    )
    
    db.session.add(rule)
    
    try:
        db.session.commit()
        return jsonify({
            'code': 200,
            'msg': '创建成功',
            'ruleId': rule.rule_id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'创建失败: {str(e)}'
        }), 500

@api_bp.route('/alarm/rule/<int:rule_id>', methods=['PUT'])
@jwt_required()
def update_alarm_rule(rule_id):
    data = request.get_json()
    rule = AlarmRule.query.get(rule_id)
    
    if not rule:
        return jsonify({
            'code': 404,
            'msg': '告警规则不存在'
        }), 404
    
    rule.rule_name = data.get('ruleName', rule.rule_name)
    rule.device_type = data.get('deviceType', rule.device_type)
    rule.alarm_type = data.get('alarmType', rule.alarm_type)
    rule.conditions = data.get('conditions', rule.conditions)
    rule.severity = data.get('severity', rule.severity)
    rule.description = data.get('description', rule.description)
    rule.status = data.get('status', rule.status)
    
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

@api_bp.route('/alarm/<int:alarm_id>/handle', methods=['POST'])
@jwt_required()
def handle_alarm(alarm_id):
    data = request.get_json()
    alarm = Alarm.query.get(alarm_id)
    
    if not alarm:
        return jsonify({
            'code': 404,
            'msg': '告警记录不存在'
        }), 404
    
    if alarm.status == 'handled':
        return jsonify({
            'code': 400,
            'msg': '告警已处理'
        }), 400
    
    alarm.status = 'handled'
    alarm.handled_by = get_jwt_identity()
    alarm.handle_time = datetime.now()
    alarm.handle_result = data.get('handleResult')
    
    try:
        db.session.commit()
        return jsonify({
            'code': 200,
            'msg': '处理成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'处理失败: {str(e)}'
        }), 500 