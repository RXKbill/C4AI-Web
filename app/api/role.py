from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import api_bp
from ..models import RolePermission
from .. import db

@api_bp.route('/system/role/list', methods=['GET'])
@jwt_required()
def get_role_list():
    page = request.args.get('pageNum', 1, type=int)
    per_page = request.args.get('pageSize', 10, type=int)
    
    query = RolePermission.query.filter(RolePermission.del_flag == '0')
    
    # 按条件筛选
    role_name = request.args.get('roleName')
    if role_name:
        query = query.filter(RolePermission.role_name.like(f'%{role_name}%'))
    
    role_key = request.args.get('roleKey')
    if role_key:
        query = query.filter(RolePermission.role_key.like(f'%{role_key}%'))
    
    status = request.args.get('status')
    if status:
        query = query.filter(RolePermission.status == status)
    
    # 分页
    pagination = query.paginate(page=page, per_page=per_page)
    roles = pagination.items
    
    return jsonify({
        'code': 200,
        'msg': '查询成功',
        'total': pagination.total,
        'rows': [{
            'roleId': role.role_id,
            'roleName': role.role_name,
            'roleKey': role.role_key,
            'roleSort': role.role_sort,
            'status': role.status,
            'createTime': role.create_time.strftime('%Y-%m-%d %H:%M:%S') if role.create_time else None,
            'remark': role.remark
        } for role in roles]
    })

@api_bp.route('/system/role', methods=['POST'])
@jwt_required()
def add_role():
    data = request.get_json()
    
    if RolePermission.query.filter_by(role_name=data.get('roleName')).first():
        return jsonify({
            'code': 400,
            'msg': '角色名称已存在'
        }), 400
    
    if RolePermission.query.filter_by(role_key=data.get('roleKey')).first():
        return jsonify({
            'code': 400,
            'msg': '角色权限已存在'
        }), 400
    
    role = RolePermission(
        role_name=data.get('roleName'),
        role_key=data.get('roleKey'),
        role_sort=data.get('roleSort', 0),
        status=data.get('status', '0'),
        remark=data.get('remark'),
        create_by=get_jwt_identity()
    )
    
    db.session.add(role)
    
    # 添加角色菜单关系
    menu_ids = data.get('menuIds', [])
    if menu_ids:
        # Assuming Menu model is available or needs to be imported
        # from ..models import Menu
        # menus = Menu.query.filter(Menu.menu_id.in_(menu_ids)).all()
        # for menu in menus:
        #     role.menus.append(menu)
        pass # Placeholder for menu assignment logic
    
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

@api_bp.route('/system/role', methods=['PUT'])
@jwt_required()
def update_role():
    data = request.get_json()
    role_id = data.get('roleId')
    
    role = RolePermission.query.get(role_id)
    if not role:
        return jsonify({
            'code': 404,
            'msg': '角色不存在'
        }), 404
    
    # 更新基本信息
    role.role_name = data.get('roleName', role.role_name)
    role.role_key = data.get('roleKey', role.role_key)
    role.role_sort = data.get('roleSort', role.role_sort)
    role.status = data.get('status', role.status)
    role.remark = data.get('remark', role.remark)
    role.update_by = get_jwt_identity()
    
    # 更新菜单
    menu_ids = data.get('menuIds')
    if menu_ids is not None:
        # Assuming Menu model is available or needs to be imported
        # from ..models import Menu
        # role.menus = []
        # menus = Menu.query.filter(Menu.menu_id.in_(menu_ids)).all()
        # for menu in menus:
        #     role.menus.append(menu)
        pass # Placeholder for menu assignment logic
    
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

@api_bp.route('/system/role/<int:role_id>', methods=['DELETE'])
@jwt_required()
def delete_role(role_id):
    role = RolePermission.query.get(role_id)
    if not role:
        return jsonify({
            'code': 404,
            'msg': '角色不存在'
        }), 404
    
    role.del_flag = '2'  # 标记为删除
    role.update_by = get_jwt_identity()
    
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