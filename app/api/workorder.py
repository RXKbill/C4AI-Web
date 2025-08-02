from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import api_bp
from ..models import WorkOrder, WorkOrderImage
from .. import db
from datetime import datetime

@api_bp.route('/workorder/list', methods=['GET'])
@jwt_required()
def get_workorder_list():
    page = request.args.get('pageNum', 1, type=int)
    per_page = request.args.get('pageSize', 10, type=int)
    
    query = WorkOrder.query
    
    device_id = request.args.get('deviceId', type=int)
    if device_id:
        query = query.filter(WorkOrder.device_id == device_id)
    
    order_type = request.args.get('orderType')
    if order_type:
        query = query.filter(WorkOrder.order_type == order_type)
    
    priority = request.args.get('priority')
    if priority:
        query = query.filter(WorkOrder.priority == priority)
    
    status = request.args.get('status')
    if status:
        query = query.filter(WorkOrder.status == status)
    
    assigned_to = request.args.get('assignedTo')
    if assigned_to:
        query = query.filter(WorkOrder.assigned_to == assigned_to)
    
    start_time = request.args.get('startTime')
    if start_time:
        query = query.filter(WorkOrder.created_at >= start_time)
    
    end_time = request.args.get('endTime')
    if end_time:
        query = query.filter(WorkOrder.created_at <= end_time)
    
    pagination = query.order_by(WorkOrder.created_at.desc()).paginate(page=page, per_page=per_page)
    orders = pagination.items
    
    return jsonify({
        'code': 200,
        'msg': '查询成功',
        'total': pagination.total,
        'rows': [{
            'orderId': order.order_id,
            'deviceId': order.device_id,
            'orderType': order.order_type,
            'title': order.title,
            'description': order.description,
            'priority': order.priority,
            'status': order.status,
            'assignedTo': order.assigned_to,
            'createdBy': order.created_by,
            'createdAt': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'scheduledTime': order.scheduled_time.strftime('%Y-%m-%d %H:%M:%S') if order.scheduled_time else None,
            'completedTime': order.completed_time.strftime('%Y-%m-%d %H:%M:%S') if order.completed_time else None
        } for order in orders]
    })

@api_bp.route('/workorder', methods=['POST'])
@jwt_required()
def create_workorder():
    data = request.get_json()
    
    order = WorkOrder(
        device_id=data.get('deviceId'),
        order_type=data.get('orderType'),
        title=data.get('title'),
        description=data.get('description'),
        priority=data.get('priority', 'normal'),
        status='pending',
        assigned_to=data.get('assignedTo'),
        scheduled_time=datetime.strptime(data.get('scheduledTime'), '%Y-%m-%d %H:%M:%S') if data.get('scheduledTime') else None,
        created_by=get_jwt_identity()
    )
    
    db.session.add(order)
    
    try:
        db.session.commit()
        return jsonify({
            'code': 200,
            'msg': '创建成功',
            'orderId': order.order_id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'创建失败: {str(e)}'
        }), 500

@api_bp.route('/workorder/<int:order_id>', methods=['PUT'])
@jwt_required()
def update_workorder(order_id):
    data = request.get_json()
    order = WorkOrder.query.get(order_id)
    
    if not order:
        return jsonify({
            'code': 404,
            'msg': '工单不存在'
        }), 404
    
    order.title = data.get('title', order.title)
    order.description = data.get('description', order.description)
    order.priority = data.get('priority', order.priority)
    order.status = data.get('status', order.status)
    order.assigned_to = data.get('assignedTo', order.assigned_to)
    
    if data.get('scheduledTime'):
        order.scheduled_time = datetime.strptime(data.get('scheduledTime'), '%Y-%m-%d %H:%M:%S')
    
    if data.get('status') == 'completed':
        order.completed_time = datetime.now()
        order.completed_by = get_jwt_identity()
    
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

@api_bp.route('/workorder/<int:order_id>/images', methods=['POST'])
@jwt_required()
def upload_workorder_images(order_id):
    if 'images' not in request.files:
        return jsonify({
            'code': 400,
            'msg': '未上传图片'
        }), 400
    
    order = WorkOrder.query.get(order_id)
    if not order:
        return jsonify({
            'code': 404,
            'msg': '工单不存在'
        }), 404
    
    try:
        uploaded_files = request.files.getlist('images')
        for file in uploaded_files:
            image = WorkOrderImage(
                order_id=order_id,
                image_type=request.form.get('imageType', 'repair'),
                image_path=file.filename,  # 实际应用中需要保存文件并返回路径
                description=request.form.get('description'),
                uploaded_by=get_jwt_identity()
            )
            db.session.add(image)
        
        db.session.commit()
        return jsonify({
            'code': 200,
            'msg': '上传成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'上传失败: {str(e)}'
        }), 500

@api_bp.route('/workorder/<int:order_id>/images', methods=['GET'])
@jwt_required()
def get_workorder_images(order_id):
    order = WorkOrder.query.get(order_id)
    if not order:
        return jsonify({
            'code': 404,
            'msg': '工单不存在'
        }), 404
    
    images = WorkOrderImage.query.filter_by(order_id=order_id).all()
    
    return jsonify({
        'code': 200,
        'msg': '查询成功',
        'data': [{
            'imageId': image.image_id,
            'imageType': image.image_type,
            'imagePath': image.image_path,
            'description': image.description,
            'uploadedBy': image.uploaded_by,
            'uploadedAt': image.uploaded_at.strftime('%Y-%m-%d %H:%M:%S')
        } for image in images]
    }) 