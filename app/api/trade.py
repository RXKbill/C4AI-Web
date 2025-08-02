from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import api_bp
from ..models import EnergyTrade, MarketData, TimeBasedPricing
from .. import db
from datetime import datetime

@api_bp.route('/trade/list', methods=['GET'])
@jwt_required()
def get_trade_list():
    page = request.args.get('pageNum', 1, type=int)
    per_page = request.args.get('pageSize', 10, type=int)
    
    query = EnergyTrade.query
    
    user_id = get_jwt_identity()
    role = request.args.get('role')  # buyer/seller
    if role == 'buyer':
        query = query.filter(EnergyTrade.buyer_id == user_id)
    elif role == 'seller':
        query = query.filter(EnergyTrade.seller_id == user_id)
    
    trade_type = request.args.get('tradeType')
    if trade_type:
        query = query.filter(EnergyTrade.trade_type == trade_type)
    
    market_type = request.args.get('marketType')
    if market_type:
        query = query.filter(EnergyTrade.market_type == market_type)
    
    status = request.args.get('status')
    if status:
        query = query.filter(EnergyTrade.status == status)
    
    start_time = request.args.get('startTime')
    if start_time:
        query = query.filter(EnergyTrade.trade_time >= start_time)
    
    end_time = request.args.get('endTime')
    if end_time:
        query = query.filter(EnergyTrade.trade_time <= end_time)
    
    pagination = query.order_by(EnergyTrade.trade_time.desc()).paginate(page=page, per_page=per_page)
    trades = pagination.items
    
    return jsonify({
        'code': 200,
        'msg': '查询成功',
        'total': pagination.total,
        'rows': [{
            'tradeId': trade.trade_id,
            'buyerId': trade.buyer_id,
            'sellerId': trade.seller_id,
            'predictionId': trade.prediction_id,
            'tradeTime': trade.trade_time.strftime('%Y-%m-%d %H:%M:%S'),
            'tradeType': trade.trade_type,
            'price': trade.price,
            'volume': trade.volume,
            'marketType': trade.market_type,
            'status': trade.status
        } for trade in trades]
    })

@api_bp.route('/trade', methods=['POST'])
@jwt_required()
def create_trade():
    data = request.get_json()
    user_id = get_jwt_identity()
    
    trade = EnergyTrade(
        buyer_id=data.get('buyerId', user_id),
        seller_id=data.get('sellerId'),
        prediction_id=data.get('predictionId'),
        trade_type=data.get('tradeType'),
        price=data.get('price'),
        volume=data.get('volume'),
        market_type=data.get('marketType'),
        status='pending'
    )
    
    db.session.add(trade)
    
    try:
        db.session.commit()
        return jsonify({
            'code': 200,
            'msg': '创建成功',
            'tradeId': trade.trade_id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'创建失败: {str(e)}'
        }), 500

@api_bp.route('/trade/<int:trade_id>/status', methods=['PUT'])
@jwt_required()
def update_trade_status(trade_id):
    data = request.get_json()
    trade = EnergyTrade.query.get(trade_id)
    
    if not trade:
        return jsonify({
            'code': 404,
            'msg': '交易不存在'
        }), 404
    
    user_id = get_jwt_identity()
    if trade.buyer_id != user_id and trade.seller_id != user_id:
        return jsonify({
            'code': 403,
            'msg': '无权限操作'
        }), 403
    
    new_status = data.get('status')
    if new_status not in ['completed', 'cancelled']:
        return jsonify({
            'code': 400,
            'msg': '状态无效'
        }), 400
    
    trade.status = new_status
    
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

@api_bp.route('/market/data', methods=['GET'])
@jwt_required()
def get_market_data():
    page = request.args.get('pageNum', 1, type=int)
    per_page = request.args.get('pageSize', 10, type=int)
    
    query = MarketData.query
    
    market_type = request.args.get('marketType')
    if market_type:
        query = query.filter(MarketData.market_type == market_type)
    
    region = request.args.get('region')
    if region:
        query = query.filter(MarketData.region == region)
    
    start_time = request.args.get('startTime')
    if start_time:
        query = query.filter(MarketData.timestamp >= start_time)
    
    end_time = request.args.get('endTime')
    if end_time:
        query = query.filter(MarketData.timestamp <= end_time)
    
    pagination = query.order_by(MarketData.timestamp.desc()).paginate(page=page, per_page=per_page)
    data_list = pagination.items
    
    return jsonify({
        'code': 200,
        'msg': '查询成功',
        'total': pagination.total,
        'rows': [{
            'marketDataId': data.market_data_id,
            'marketType': data.market_type,
            'price': data.price,
            'supplyDemand': data.supply_demand,
            'region': data.region,
            'timestamp': data.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        } for data in data_list]
    })

@api_bp.route('/pricing/time-based', methods=['GET'])
@jwt_required()
def get_time_based_pricing():
    page = request.args.get('pageNum', 1, type=int)
    per_page = request.args.get('pageSize', 10, type=int)
    
    query = TimeBasedPricing.query
    
    region = request.args.get('region')
    if region:
        query = query.filter(TimeBasedPricing.region == region)
    
    status = request.args.get('status')
    if status:
        query = query.filter(TimeBasedPricing.status == status)
    
    pagination = query.paginate(page=page, per_page=per_page)
    pricing_list = pagination.items
    
    return jsonify({
        'code': 200,
        'msg': '查询成功',
        'total': pagination.total,
        'rows': [{
            'pricingId': pricing.pricing_id,
            'strategyName': pricing.strategy_name,
            'timePeriods': pricing.time_periods,
            'region': pricing.region,
            'status': pricing.status,
            'effectiveFrom': pricing.effective_from.strftime('%Y-%m-%d %H:%M:%S'),
            'effectiveTo': pricing.effective_to.strftime('%Y-%m-%d %H:%M:%S') if pricing.effective_to else None
        } for pricing in pricing_list]
    }) 