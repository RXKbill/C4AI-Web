from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import api_bp
from ..models import Notification, NotificationSubscription
from .. import db
from datetime import datetime

@api_bp.route('/notification/list', methods=['GET'])
@jwt_required()
def get_notifications():
    page = request.args.get('pageNum', 1, type=int)
    per_page = request.args.get('pageSize', 10, type=int)
    
    query = Notification.query.filter_by(user_id=get_jwt_identity())
    
    notification_type = request.args.get('type')
    if notification_type:
        query = query.filter(Notification.notification_type == notification_type)
    
    priority = request.args.get('priority')
    if priority:
        query = query.filter(Notification.priority == priority)
    
    read_status = request.args.get('readStatus')
    if read_status:
        query = query.filter(Notification.read_status == read_status)
    
    start_time = request.args.get('startTime')
    if start_time:
        query = query.filter(Notification.created_at >= start_time)
    
    end_time = request.args.get('endTime')
    if end_time:
        query = query.filter(Notification.created_at <= end_time)
    
    pagination = query.order_by(Notification.created_at.desc()).paginate(page=page, per_page=per_page)
    notifications = pagination.items
    
    return jsonify({
        'code': 200,
        'msg': '查询成功',
        'total': pagination.total,
        'rows': [{
            'notificationId': notification.notification_id,
            'type': notification.notification_type,
            'title': notification.title,
            'content': notification.content,
            'priority': notification.priority,
            'readStatus': notification.read_status,
            'createdAt': notification.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for notification in notifications]
    })

@api_bp.route('/notification/unread/count', methods=['GET'])
@jwt_required()
def get_unread_count():
    count = Notification.query.filter_by(
        user_id=get_jwt_identity(),
        read_status='unread'
    ).count()
    
    return jsonify({
        'code': 200,
        'msg': '查询成功',
        'data': {
            'unreadCount': count
        }
    })

@api_bp.route('/notification/<int:notification_id>/read', methods=['PUT'])
@jwt_required()
def mark_as_read(notification_id):
    notification = Notification.query.get(notification_id)
    
    if not notification:
        return jsonify({
            'code': 404,
            'msg': '通知不存在'
        }), 404
    
    if notification.user_id != get_jwt_identity():
        return jsonify({
            'code': 403,
            'msg': '无权限操作'
        }), 403
    
    notification.read_status = 'read'
    notification.read_time = datetime.now()
    
    try:
        db.session.commit()
        return jsonify({
            'code': 200,
            'msg': '标记成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'标记失败: {str(e)}'
        }), 500

@api_bp.route('/notification/subscription', methods=['GET'])
@jwt_required()
def get_subscriptions():
    subscriptions = NotificationSubscription.query.filter_by(
        user_id=get_jwt_identity()
    ).all()
    
    return jsonify({
        'code': 200,
        'msg': '查询成功',
        'data': [{
            'subscriptionId': sub.subscription_id,
            'type': sub.notification_type,
            'channel': sub.channel,
            'config': sub.config,
            'status': sub.status,
            'createdAt': sub.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for sub in subscriptions]
    })

@api_bp.route('/notification/subscription', methods=['POST'])
@jwt_required()
def create_subscription():
    data = request.get_json()
    
    subscription = NotificationSubscription(
        user_id=get_jwt_identity(),
        notification_type=data.get('type'),
        channel=data.get('channel'),
        config=data.get('config'),
        status='enabled'
    )
    
    db.session.add(subscription)
    
    try:
        db.session.commit()
        return jsonify({
            'code': 200,
            'msg': '订阅成功',
            'subscriptionId': subscription.subscription_id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'订阅失败: {str(e)}'
        }), 500

@api_bp.route('/notification/subscription/<int:subscription_id>', methods=['PUT'])
@jwt_required()
def update_subscription(subscription_id):
    data = request.get_json()
    subscription = NotificationSubscription.query.get(subscription_id)
    
    if not subscription:
        return jsonify({
            'code': 404,
            'msg': '订阅不存在'
        }), 404
    
    if subscription.user_id != get_jwt_identity():
        return jsonify({
            'code': 403,
            'msg': '无权限操作'
        }), 403
    
    subscription.channel = data.get('channel', subscription.channel)
    subscription.config = data.get('config', subscription.config)
    subscription.status = data.get('status', subscription.status)
    
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

@api_bp.route('/notification/subscription/<int:subscription_id>', methods=['DELETE'])
@jwt_required()
def delete_subscription(subscription_id):
    subscription = NotificationSubscription.query.get(subscription_id)
    
    if not subscription:
        return jsonify({
            'code': 404,
            'msg': '订阅不存在'
        }), 404
    
    if subscription.user_id != get_jwt_identity():
        return jsonify({
            'code': 403,
            'msg': '无权限操作'
        }), 403
    
    try:
        db.session.delete(subscription)
        db.session.commit()
        return jsonify({
            'code': 200,
            'msg': '取消订阅成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'取消订阅失败: {str(e)}'
        }), 500

def send_notification(user_id, notification_type, title, content, priority='normal'):
    """
    发送通知的内部函数
    """
    notification = Notification(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        content=content,
        priority=priority,
        read_status='unread'
    )
    
    db.session.add(notification)
    
    try:
        db.session.commit()
        
        # 获取用户的订阅配置
        subscriptions = NotificationSubscription.query.filter_by(
            user_id=user_id,
            notification_type=notification_type,
            status='enabled'
        ).all()
        
        # 根据订阅配置发送通知
        for sub in subscriptions:
            if sub.channel == 'email':
                # 发送邮件通知
                pass
            elif sub.channel == 'sms':
                # 发送短信通知
                pass
            elif sub.channel == 'app_push':
                # 发送APP推送
                pass
        
        return True
    except Exception as e:
        db.session.rollback()
        return False 