from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import api_bp
from ..models import User, RolePermission
from .. import db

@api_bp.route('/system/user/list', methods=['GET'])
@jwt_required()
def get_user_list():
    page = request.args.get('pageNum', 1, type=int)
    per_page = request.args.get('pageSize', 10, type=int)
    
    query = User.query.filter(User.del_flag == '0')
    
    # 按条件筛选
    username = request.args.get('userName')
    if username:
        query = query.filter(User.user_name.like(f'%{username}%'))
    
    phonenumber = request.args.get('phonenumber')
    if phonenumber:
        query = query.filter(User.phonenumber.like(f'%{phonenumber}%'))
    
    status = request.args.get('status')
    if status:
        query = query.filter(User.status == status)
    
    # 分页
    pagination = query.paginate(page=page, per_page=per_page)
    users = pagination.items
    
    return jsonify({
        'code': 200,
        'msg': '查询成功',
        'total': pagination.total,
        'rows': [{
            'userId': user.user_id,
            'userName': user.user_name,
            'nickName': user.nick_name,
            'email': user.email,
            'phonenumber': user.phonenumber,
            'sex': user.sex,
            'status': user.status,
            'createTime': user.create_time.strftime('%Y-%m-%d %H:%M:%S') if user.create_time else None
        } for user in users]
    })

@api_bp.route('/system/user', methods=['POST'])
@jwt_required()
def add_user():
    data = request.get_json()
    
    if User.query.filter_by(user_name=data.get('userName')).first():
        return jsonify({
            'code': 400,
            'msg': '用户名已存在'
        }), 400
    
    user = User(
        user_name=data.get('userName'),
        nick_name=data.get('nickName'),
        password=data.get('password'),
        email=data.get('email'),
        phonenumber=data.get('phonenumber'),
        sex=data.get('sex'),
        status=data.get('status', '0'),
        create_by=get_jwt_identity()
    )
    
    db.session.add(user)
    
    # 添加用户角色关系
    role_ids = data.get('roleIds', [])
    if role_ids:
        roles = RolePermission.query.filter(RolePermission.role_id.in_(role_ids)).all()
        for role in roles:
            user.roles.append(role)
    
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

@api_bp.route('/system/user', methods=['PUT'])
@jwt_required()
def update_user():
    data = request.get_json()
    user_id = data.get('userId')
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({
            'code': 404,
            'msg': '用户不存在'
        }), 404
    
    # 更新基本信息
    user.nick_name = data.get('nickName', user.nick_name)
    user.email = data.get('email', user.email)
    user.phonenumber = data.get('phonenumber', user.phonenumber)
    user.sex = data.get('sex', user.sex)
    user.status = data.get('status', user.status)
    user.update_by = get_jwt_identity()
    
    # 更新角色
    role_ids = data.get('roleIds')
    if role_ids is not None:
        user.roles = []
        roles = RolePermission.query.filter(RolePermission.role_id.in_(role_ids)).all()
        for role in roles:
            user.roles.append(role)
    
    try:
        db.session.commit()
        return jsonify({
            'code': 200,
            'msg': '修改成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'修改失败: {str(e)}'
        }), 500

@api_bp.route('/system/user/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({
            'code': 404,
            'msg': '用户不存在'
        }), 404
    
    user.del_flag = '2'  # 标记为删除
    user.update_by = get_jwt_identity()
    
    try:
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

@api_bp.route('/system/user/resetPwd', methods=['PUT'])
@jwt_required()
def reset_password():
    data = request.get_json()
    user_id = data.get('userId')
    new_password = data.get('password')
    
    if not new_password:
        return jsonify({
            'code': 400,
            'msg': '密码不能为空'
        }), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({
            'code': 404,
            'msg': '用户不存在'
        }), 404
    
    user.password = new_password
    user.update_by = get_jwt_identity()
    
    try:
        db.session.commit()
        return jsonify({
            'code': 200,
            'msg': '密码重置成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'密码重置失败: {str(e)}'
        }), 500 