from flask import request, jsonify
from flask_jwt_extended import jwt_required
from . import api_bp
from ..models import Device, RealtimeData, WeatherData, EnergyTrade, Alarm
from .. import db
from sqlalchemy import func
from datetime import datetime, timedelta

@api_bp.route('/statistics/device/overview', methods=['GET'])
@jwt_required()
def get_device_overview():
    # 设备总数统计
    total_devices = Device.query.count()
    
    # 按设备类型统计
    device_type_stats = db.session.query(
        Device.device_type,
        func.count(Device.device_id).label('count')
    ).group_by(Device.device_type).all()
    
    # 按健康状态统计
    health_status_stats = db.session.query(
        Device.health_status,
        func.count(Device.device_id).label('count')
    ).group_by(Device.health_status).all()
    
    return jsonify({
        'code': 200,
        'msg': '查询成功',
        'data': {
            'totalDevices': total_devices,
            'deviceTypeStats': [{
                'deviceType': stat[0],
                'count': stat[1]
            } for stat in device_type_stats],
            'healthStatusStats': [{
                'healthStatus': stat[0],
                'count': stat[1]
            } for stat in health_status_stats]
        }
    })

@api_bp.route('/statistics/power/generation', methods=['GET'])
@jwt_required()
def get_power_generation_stats():
    time_range = request.args.get('timeRange', 'day')  # day, week, month, year
    region = request.args.get('region')
    device_type = request.args.get('deviceType')
    
    now = datetime.now()
    
    if time_range == 'day':
        start_time = now - timedelta(days=1)
        group_by = func.date_format(RealtimeData.timestamp, '%Y-%m-%d %H:00:00')
    elif time_range == 'week':
        start_time = now - timedelta(weeks=1)
        group_by = func.date_format(RealtimeData.timestamp, '%Y-%m-%d')
    elif time_range == 'month':
        start_time = now - timedelta(days=30)
        group_by = func.date_format(RealtimeData.timestamp, '%Y-%m-%d')
    else:  # year
        start_time = now - timedelta(days=365)
        group_by = func.date_format(RealtimeData.timestamp, '%Y-%m')
    
    query = db.session.query(
        group_by.label('time_point'),
        func.sum(RealtimeData.power_output).label('total_power')
    ).join(Device, RealtimeData.device_id == Device.device_id)
    
    if region:
        query = query.filter(Device.region == region)
    if device_type:
        query = query.filter(Device.device_type == device_type)
    
    query = query.filter(RealtimeData.timestamp >= start_time)
    query = query.group_by('time_point').order_by('time_point')
    
    stats = query.all()
    
    return jsonify({
        'code': 200,
        'msg': '查询成功',
        'data': [{
            'timePoint': stat[0],
            'totalPower': float(stat[1]) if stat[1] else 0
        } for stat in stats]
    })

@api_bp.route('/statistics/alarm/analysis', methods=['GET'])
@jwt_required()
def get_alarm_analysis():
    time_range = request.args.get('timeRange', 'month')  # week, month, year
    
    now = datetime.now()
    
    if time_range == 'week':
        start_time = now - timedelta(weeks=1)
    elif time_range == 'month':
        start_time = now - timedelta(days=30)
    else:  # year
        start_time = now - timedelta(days=365)
    
    # 按告警类型统计
    alarm_type_stats = db.session.query(
        Alarm.alarm_type,
        func.count(Alarm.alarm_id).label('count')
    ).filter(Alarm.alarm_time >= start_time).group_by(Alarm.alarm_type).all()
    
    # 按严重程度统计
    severity_stats = db.session.query(
        Alarm.severity,
        func.count(Alarm.alarm_id).label('count')
    ).filter(Alarm.alarm_time >= start_time).group_by(Alarm.severity).all()
    
    # 按设备类型统计
    device_type_stats = db.session.query(
        Device.device_type,
        func.count(Alarm.alarm_id).label('count')
    ).join(Device, Alarm.device_id == Device.device_id)\
    .filter(Alarm.alarm_time >= start_time)\
    .group_by(Device.device_type).all()
    
    return jsonify({
        'code': 200,
        'msg': '查询成功',
        'data': {
            'alarmTypeStats': [{
                'alarmType': stat[0],
                'count': stat[1]
            } for stat in alarm_type_stats],
            'severityStats': [{
                'severity': stat[0],
                'count': stat[1]
            } for stat in severity_stats],
            'deviceTypeStats': [{
                'deviceType': stat[0],
                'count': stat[1]
            } for stat in device_type_stats]
        }
    })

@api_bp.route('/statistics/trade/analysis', methods=['GET'])
@jwt_required()
def get_trade_analysis():
    time_range = request.args.get('timeRange', 'month')  # week, month, year
    
    now = datetime.now()
    
    if time_range == 'week':
        start_time = now - timedelta(weeks=1)
        group_by = func.date_format(EnergyTrade.trade_time, '%Y-%m-%d')
    elif time_range == 'month':
        start_time = now - timedelta(days=30)
        group_by = func.date_format(EnergyTrade.trade_time, '%Y-%m-%d')
    else:  # year
        start_time = now - timedelta(days=365)
        group_by = func.date_format(EnergyTrade.trade_time, '%Y-%m')
    
    # 交易量统计
    volume_stats = db.session.query(
        group_by.label('time_point'),
        func.sum(EnergyTrade.volume).label('total_volume'),
        func.avg(EnergyTrade.price).label('avg_price')
    ).filter(EnergyTrade.trade_time >= start_time)\
    .group_by('time_point').order_by('time_point').all()
    
    # 按交易类型统计
    trade_type_stats = db.session.query(
        EnergyTrade.trade_type,
        func.count(EnergyTrade.trade_id).label('count'),
        func.sum(EnergyTrade.volume).label('total_volume')
    ).filter(EnergyTrade.trade_time >= start_time)\
    .group_by(EnergyTrade.trade_type).all()
    
    return jsonify({
        'code': 200,
        'msg': '查询成功',
        'data': {
            'volumeStats': [{
                'timePoint': stat[0],
                'totalVolume': float(stat[1]) if stat[1] else 0,
                'avgPrice': float(stat[2]) if stat[2] else 0
            } for stat in volume_stats],
            'tradeTypeStats': [{
                'tradeType': stat[0],
                'count': stat[1],
                'totalVolume': float(stat[2]) if stat[2] else 0
            } for stat in trade_type_stats]
        }
    }) 