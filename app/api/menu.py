from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import api_bp
# from ..models import Menu, Role
from .. import db

@api_bp.route('/system/menu/list', methods=['GET'])
@jwt_required()
def get_menu_list():
    query = Menu.query
    
    # 按条件筛选
    menu_name = request.args.get('menuName')
    if menu_name:
        query = query.filter(Menu.menu_name.like(f'%{menu_name}%'))
    
    status = request.args.get('status')
    if status:
        query = query.filter(Menu.status == status)
    
    menus = query.order_by(Menu.parent_id, Menu.order_num).all()
    
    return jsonify({
        'code': 200,
        'msg': '查询成功',
        'data': [{
            'menuId': menu.menu_id,
            'menuName': menu.menu_name,
            'parentId': menu.parent_id,
            'orderNum': menu.order_num,
            'path': menu.path,
            'component': menu.component,
            'isFrame': menu.is_frame,
            'isCache': menu.is_cache,
            'menuType': menu.menu_type,
            'visible': menu.visible,
            'status': menu.status,
            'perms': menu.perms,
            'icon': menu.icon,
            'createTime': menu.create_time.strftime('%Y-%m-%d %H:%M:%S') if menu.create_time else None
        } for menu in menus]
    })

@api_bp.route('/system/menu', methods=['POST'])
@jwt_required()
def add_menu():
    data = request.get_json()
    
    menu = Menu(
        menu_name=data.get('menuName'),
        parent_id=data.get('parentId'),
        order_num=data.get('orderNum', 0),
        path=data.get('path'),
        component=data.get('component'),
        is_frame=data.get('isFrame', 1),
        is_cache=data.get('isCache', 0),
        menu_type=data.get('menuType'),
        visible=data.get('visible', '0'),
        status=data.get('status', '0'),
        perms=data.get('perms'),
        icon=data.get('icon'),
        create_by=get_jwt_identity()
    )
    
    db.session.add(menu)
    
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

@api_bp.route('/system/menu', methods=['PUT'])
@jwt_required()
def update_menu():
    data = request.get_json()
    menu_id = data.get('menuId')
    
    menu = Menu.query.get(menu_id)
    if not menu:
        return jsonify({
            'code': 404,
            'msg': '菜单不存在'
        }), 404
    
    menu.menu_name = data.get('menuName', menu.menu_name)
    menu.parent_id = data.get('parentId', menu.parent_id)
    menu.order_num = data.get('orderNum', menu.order_num)
    menu.path = data.get('path', menu.path)
    menu.component = data.get('component', menu.component)
    menu.is_frame = data.get('isFrame', menu.is_frame)
    menu.is_cache = data.get('isCache', menu.is_cache)
    menu.menu_type = data.get('menuType', menu.menu_type)
    menu.visible = data.get('visible', menu.visible)
    menu.status = data.get('status', menu.status)
    menu.perms = data.get('perms', menu.perms)
    menu.icon = data.get('icon', menu.icon)
    menu.update_by = get_jwt_identity()
    
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

@api_bp.route('/system/menu/<int:menu_id>', methods=['DELETE'])
@jwt_required()
def delete_menu(menu_id):
    # 检查是否有子菜单
    if Menu.query.filter_by(parent_id=menu_id).first():
        return jsonify({
            'code': 400,
            'msg': '存在子菜单,不允许删除'
        }), 400
    
    menu = Menu.query.get(menu_id)
    if not menu:
        return jsonify({
            'code': 404,
            'msg': '菜单不存在'
        }), 404
    
    db.session.delete(menu)
    
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

@api_bp.route('/system/menu/treeselect', methods=['GET'])
@jwt_required()
def get_menu_tree():
    menus = Menu.query.filter_by(status='0').order_by(Menu.parent_id, Menu.order_num).all()
    
    def build_tree(parent_id=0):
        tree = []
        for menu in menus:
            if menu.parent_id == parent_id:
                node = {
                    'id': menu.menu_id,
                    'label': menu.menu_name,
                    'children': build_tree(menu.menu_id)
                }
                tree.append(node)
        return tree
    
    return jsonify({
        'code': 200,
        'msg': '查询成功',
        'data': build_tree()
    }) 