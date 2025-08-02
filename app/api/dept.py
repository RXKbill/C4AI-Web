from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import api_bp
from ..models import Department
from .. import db

@api_bp.route('/system/dept/list', methods=['GET'])
@jwt_required()
def get_dept_list():
    query = Department.query.filter(Department.del_flag == '0')
    
    # 按条件筛选
    dept_name = request.args.get('deptName')
    if dept_name:
        query = query.filter(Department.dept_name.like(f'%{dept_name}%'))
    
    status = request.args.get('status')
    if status:
        query = query.filter(Department.status == status)
    
    depts = query.order_by(Department.parent_id, Department.order_num).all()
    
    return jsonify({
        'code': 200,
        'msg': '查询成功',
        'data': [{
            'deptId': dept.dept_id,
            'parentId': dept.parent_id,
            'deptName': dept.dept_name,
            'orderNum': dept.order_num,
            'leader': dept.leader,
            'phone': dept.phone,
            'email': dept.email,
            'status': dept.status,
            'createTime': dept.create_time.strftime('%Y-%m-%d %H:%M:%S') if dept.create_time else None
        } for dept in depts]
    })

@api_bp.route('/system/dept', methods=['POST'])
@jwt_required()
def add_dept():
    data = request.get_json()
    
    dept = Department(
        dept_name=data.get('deptName'),
        parent_id=data.get('parentId'),
        order_num=data.get('orderNum', 0),
        leader=data.get('leader'),
        phone=data.get('phone'),
        email=data.get('email'),
        status=data.get('status', '0'),
        create_by=get_jwt_identity()
    )
    
    db.session.add(dept)
    
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

@api_bp.route('/system/dept', methods=['PUT'])
@jwt_required()
def update_dept():
    data = request.get_json()
    dept_id = data.get('deptId')
    
    dept = Department.query.get(dept_id)
    if not dept:
        return jsonify({
            'code': 404,
            'msg': '部门不存在'
        }), 404
    
    dept.dept_name = data.get('deptName', dept.dept_name)
    dept.parent_id = data.get('parentId', dept.parent_id)
    dept.order_num = data.get('orderNum', dept.order_num)
    dept.leader = data.get('leader', dept.leader)
    dept.phone = data.get('phone', dept.phone)
    dept.email = data.get('email', dept.email)
    dept.status = data.get('status', dept.status)
    dept.update_by = get_jwt_identity()
    
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

@api_bp.route('/system/dept/<int:dept_id>', methods=['DELETE'])
@jwt_required()
def delete_dept(dept_id):
    # 检查是否有子部门
    if Department.query.filter_by(parent_id=dept_id, del_flag='0').first():
        return jsonify({
            'code': 400,
            'msg': '存在下级部门,不允许删除'
        }), 400
    
    dept = Department.query.get(dept_id)
    if not dept:
        return jsonify({
            'code': 404,
            'msg': '部门不存在'
        }), 404
    
    dept.del_flag = '2'  # 标记为删除
    dept.update_by = get_jwt_identity()
    
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

@api_bp.route('/system/dept/treeselect', methods=['GET'])
@jwt_required()
def get_dept_tree():
    depts = Department.query.filter_by(del_flag='0', status='0').order_by(Department.parent_id, Department.order_num).all()
    
    def build_tree(parent_id=0):
        tree = []
        for dept in depts:
            if dept.parent_id == parent_id:
                node = {
                    'id': dept.dept_id,
                    'label': dept.dept_name,
                    'children': build_tree(dept.dept_id)
                }
                tree.append(node)
        return tree
    
    return jsonify({
        'code': 200,
        'msg': '查询成功',
        'data': build_tree()
    }) 