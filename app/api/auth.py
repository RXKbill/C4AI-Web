from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from . import api_bp
from ..models import User, RolePermission
from .. import db

@api_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({
            'code': 400,
            'msg': '用户名和密码不能为空'
        }), 400
    
    user = User.query.filter_by(user_name=username).first()
    if user is None or not user.verify_password(password):
        return jsonify({
            'code': 401,
            'msg': '用户名或密码错误'
        }), 401
    
    if user.status != '0':
        return jsonify({
            'code': 403,
            'msg': '用户已被禁用'
        }), 403
    
    # 生成token
    access_token = create_access_token(identity=user.user_id)
    
    return jsonify({
        'code': 200,
        'msg': '登录成功',
        'token': access_token
    })

@api_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    return jsonify({
        'code': 200,
        'msg': '退出成功'
    })

@api_bp.route('/info', methods=['GET'])
@jwt_required()
def get_info():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({
            'code': 404,
            'msg': '用户不存在'
        }), 404
    
    # 获取用户角色
    from ..models import user_role
    roles = RolePermission.query.join(user_role).filter(user_role.c.user_id == user_id).all()
    role_keys = [role.role_name for role in roles]
    
    return jsonify({
        'code': 200,
        'msg': '操作成功',
        'user': {
            'userId': user.user_id,
            'userName': user.user_name,
            'nickName': user.nick_name,
            'avatar': user.avatar,
            'email': user.email,
            'phonenumber': user.phonenumber,
            'sex': user.sex,
            'roles': role_keys
        }
    }) 