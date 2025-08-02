from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import api_bp
from ..models import BusinessRule, BusinessStrategy, ControlCommand, DecisionLog
from .. import db
from datetime import datetime

@api_bp.route('/rule/list', methods=['GET'])
@jwt_required()
def get_rule_list():
    page = request.args.get('pageNum', 1, type=int)
    per_page = request.args.get('pageSize', 10, type=int)
    
    query = BusinessRule.query
    
    scenario = request.args.get('scenario')
    if scenario:
        query = query.filter(BusinessRule.scenario == scenario)
    
    action_type = request.args.get('actionType')
    if action_type:
        query = query.filter(BusinessRule.action_type == action_type)
    
    status = request.args.get('status')
    if status:
        query = query.filter(BusinessRule.status == status)
    
    pagination = query.order_by(BusinessRule.priority.asc()).paginate(page=page, per_page=per_page)
    rules = pagination.items
    
    return jsonify({
        'code': 200,
        'msg': '查询成功',
        'total': pagination.total,
        'rows': [{
            'ruleId': rule.rule_id,
            'ruleName': rule.rule_name,
            'scenario': rule.scenario,
            'conditionExpr': rule.condition_expr,
            'actionType': rule.action_type,
            'priority': rule.priority,
            'status': rule.status,
            'createdBy': rule.created_by,
            'createdAt': rule.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for rule in rules]
    })

@api_bp.route('/rule', methods=['POST'])
@jwt_required()
def create_rule():
    data = request.get_json()
    
    rule = BusinessRule(
        created_by=get_jwt_identity(),
        rule_name=data.get('ruleName'),
        scenario=data.get('scenario'),
        condition_expr=data.get('conditionExpr'),
        action_type=data.get('actionType'),
        priority=data.get('priority'),
        status='enabled'
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

@api_bp.route('/rule/<int:rule_id>', methods=['PUT'])
@jwt_required()
def update_rule(rule_id):
    data = request.get_json()
    rule = BusinessRule.query.get(rule_id)
    
    if not rule:
        return jsonify({
            'code': 404,
            'msg': '规则不存在'
        }), 404
    
    rule.rule_name = data.get('ruleName', rule.rule_name)
    rule.scenario = data.get('scenario', rule.scenario)
    rule.condition_expr = data.get('conditionExpr', rule.condition_expr)
    rule.action_type = data.get('actionType', rule.action_type)
    rule.priority = data.get('priority', rule.priority)
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

@api_bp.route('/rule/<int:rule_id>', methods=['DELETE'])
@jwt_required()
def delete_rule(rule_id):
    rule = BusinessRule.query.get(rule_id)
    
    if not rule:
        return jsonify({
            'code': 404,
            'msg': '规则不存在'
        }), 404
    
    try:
        db.session.delete(rule)
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

@api_bp.route('/rule/strategy/list', methods=['GET'])
@jwt_required()
def get_strategy_list():
    page = request.args.get('pageNum', 1, type=int)
    per_page = request.args.get('pageSize', 10, type=int)
    
    query = BusinessStrategy.query
    
    rule_id = request.args.get('ruleId', type=int)
    if rule_id:
        query = query.filter(BusinessStrategy.rule_id == rule_id)
    
    scenario = request.args.get('scenario')
    if scenario:
        query = query.filter(BusinessStrategy.scenario == scenario)
    
    status = request.args.get('status')
    if status:
        query = query.filter(BusinessStrategy.status == status)
    
    pagination = query.paginate(page=page, per_page=per_page)
    strategies = pagination.items
    
    return jsonify({
        'code': 200,
        'msg': '查询成功',
        'total': pagination.total,
        'rows': [{
            'strategyId': strategy.strategy_id,
            'ruleId': strategy.rule_id,
            'strategyName': strategy.strategy_name,
            'parameters': strategy.parameters,
            'version': strategy.version,
            'scenario': strategy.scenario,
            'status': strategy.status,
            'createdBy': strategy.created_by,
            'createdAt': strategy.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for strategy in strategies]
    })

@api_bp.route('/rule/execution/log', methods=['GET'])
@jwt_required()
def get_execution_log():
    page = request.args.get('pageNum', 1, type=int)
    per_page = request.args.get('pageSize', 10, type=int)
    
    query = DecisionLog.query
    
    rule_id = request.args.get('ruleId', type=int)
    if rule_id:
        query = query.filter(DecisionLog.rule_id == rule_id)
    
    execution_result = request.args.get('executionResult')
    if execution_result:
        query = query.filter(DecisionLog.execution_result == execution_result)
    
    start_time = request.args.get('startTime')
    if start_time:
        query = query.filter(DecisionLog.created_at >= start_time)
    
    end_time = request.args.get('endTime')
    if end_time:
        query = query.filter(DecisionLog.created_at <= end_time)
    
    pagination = query.order_by(DecisionLog.created_at.desc()).paginate(page=page, per_page=per_page)
    logs = pagination.items
    
    return jsonify({
        'code': 200,
        'msg': '查询成功',
        'total': pagination.total,
        'rows': [{
            'logId': log.log_id,
            'ruleId': log.rule_id,
            'userId': log.user_id,
            'inputData': log.input_data,
            'outputCommands': log.output_commands,
            'executionResult': log.execution_result,
            'errorDetails': log.error_details,
            'createdAt': log.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for log in logs]
    }) 