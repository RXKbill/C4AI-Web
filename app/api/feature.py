from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import api_bp
# from ..models import FeatureEngineering, DataPreprocessing, Dataset
from .. import db
from datetime import datetime
import pandas as pd
import numpy as np
import requests

# 模型服务配置
MODEL_SERVICE_URL = "http://model-service:8000"  # 时序预测大模型服务的地址

@api_bp.route('/feature/preprocess', methods=['POST'])
@jwt_required()
def preprocess_data():
    data = request.get_json()
    
    preprocessing = DataPreprocessing(
        dataset_id=data.get('datasetId'),
        config={
            'missing_value_strategy': data.get('missingValueStrategy', 'mean'),
            'outlier_strategy': data.get('outlierStrategy', 'iqr'),
            'scaling_method': data.get('scalingMethod', 'standard'),
            'encoding_method': data.get('encodingMethod', 'label')
        },
        status='pending',
        created_by=get_jwt_identity()
    )
    
    db.session.add(preprocessing)
    
    try:
        db.session.commit()
        
        # 调用数据预处理服务
        try:
            response = requests.post(
                f"{MODEL_SERVICE_URL}/preprocess",
                json={
                    'preprocessingId': preprocessing.preprocessing_id,
                    'datasetId': preprocessing.dataset_id,
                    'config': preprocessing.config
                }
            )
            
            if response.status_code == 200:
                return jsonify({
                    'code': 200,
                    'msg': '预处理任务已提交',
                    'preprocessingId': preprocessing.preprocessing_id
                })
            else:
                raise Exception(f"预处理服务返回错误: {response.text}")
                
        except Exception as e:
            preprocessing.status = 'failed'
            preprocessing.error_message = str(e)
            db.session.commit()
            
            return jsonify({
                'code': 500,
                'msg': f'提交预处理任务失败: {str(e)}'
            }), 500
            
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'创建预处理记录失败: {str(e)}'
        }), 500

@api_bp.route('/feature/engineer', methods=['POST'])
@jwt_required()
def engineer_features():
    data = request.get_json()
    
    feature_engineering = FeatureEngineering(
        dataset_id=data.get('datasetId'),
        config={
            'time_features': data.get('timeFeatures', []),
            'statistical_features': data.get('statisticalFeatures', []),
            'window_features': data.get('windowFeatures', []),
            'custom_features': data.get('customFeatures', [])
        },
        status='pending',
        created_by=get_jwt_identity()
    )
    
    db.session.add(feature_engineering)
    
    try:
        db.session.commit()
        
        # 调用特征工程服务
        try:
            response = requests.post(
                f"{MODEL_SERVICE_URL}/feature-engineering",
                json={
                    'engineeringId': feature_engineering.engineering_id,
                    'datasetId': feature_engineering.dataset_id,
                    'config': feature_engineering.config
                }
            )
            
            if response.status_code == 200:
                return jsonify({
                    'code': 200,
                    'msg': '特征工程任务已提交',
                    'engineeringId': feature_engineering.engineering_id
                })
            else:
                raise Exception(f"特征工程服务返回错误: {response.text}")
                
        except Exception as e:
            feature_engineering.status = 'failed'
            feature_engineering.error_message = str(e)
            db.session.commit()
            
            return jsonify({
                'code': 500,
                'msg': f'提交特征工程任务失败: {str(e)}'
            }), 500
            
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'创建特征工程记录失败: {str(e)}'
        }), 500

@api_bp.route('/feature/dataset', methods=['POST'])
@jwt_required()
def create_dataset():
    data = request.get_json()
    
    dataset = Dataset(
        name=data.get('name'),
        description=data.get('description'),
        source_type=data.get('sourceType'),
        source_config=data.get('sourceConfig'),
        feature_config=data.get('featureConfig'),
        status='pending',
        created_by=get_jwt_identity()
    )
    
    db.session.add(dataset)
    
    try:
        db.session.commit()
        
        # 调用数据集创建服务
        try:
            response = requests.post(
                f"{MODEL_SERVICE_URL}/dataset",
                json={
                    'datasetId': dataset.dataset_id,
                    'sourceType': dataset.source_type,
                    'sourceConfig': dataset.source_config,
                    'featureConfig': dataset.feature_config
                }
            )
            
            if response.status_code == 200:
                return jsonify({
                    'code': 200,
                    'msg': '数据集创建任务已提交',
                    'datasetId': dataset.dataset_id
                })
            else:
                raise Exception(f"数据集服务返回错误: {response.text}")
                
        except Exception as e:
            dataset.status = 'failed'
            dataset.error_message = str(e)
            db.session.commit()
            
            return jsonify({
                'code': 500,
                'msg': f'提交数据集创建任务失败: {str(e)}'
            }), 500
            
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'创建数据集记录失败: {str(e)}'
        }), 500

@api_bp.route('/feature/dataset/<int:dataset_id>', methods=['GET'])
@jwt_required()
def get_dataset_info(dataset_id):
    dataset = Dataset.query.get(dataset_id)
    
    if not dataset:
        return jsonify({
            'code': 404,
            'msg': '数据集不存在'
        }), 404
    
    try:
        # 从数据集服务获取最新状态
        response = requests.get(f"{MODEL_SERVICE_URL}/dataset/{dataset_id}/info")
        
        if response.status_code == 200:
            info_data = response.json()
            
            # 更新数据集信息
            dataset.status = info_data.get('status', dataset.status)
            dataset.statistics = info_data.get('statistics', dataset.statistics)
            dataset.schema = info_data.get('schema', dataset.schema)
            dataset.error_message = info_data.get('errorMessage', dataset.error_message)
            
            db.session.commit()
            
            return jsonify({
                'code': 200,
                'msg': '查询成功',
                'data': {
                    'datasetId': dataset.dataset_id,
                    'name': dataset.name,
                    'description': dataset.description,
                    'sourceType': dataset.source_type,
                    'status': dataset.status,
                    'statistics': dataset.statistics,
                    'schema': dataset.schema,
                    'errorMessage': dataset.error_message,
                    'createdBy': dataset.created_by,
                    'createdAt': dataset.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'updatedAt': dataset.updated_at.strftime('%Y-%m-%d %H:%M:%S') if dataset.updated_at else None
                }
            })
        else:
            raise Exception(f"数据集服务返回错误: {response.text}")
            
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'获取数据集信息失败: {str(e)}'
        }), 500

@api_bp.route('/feature/dataset/<int:dataset_id>/preview', methods=['GET'])
@jwt_required()
def preview_dataset(dataset_id):
    limit = request.args.get('limit', 100, type=int)
    
    dataset = Dataset.query.get(dataset_id)
    
    if not dataset:
        return jsonify({
            'code': 404,
            'msg': '数据集不存在'
        }), 404
    
    try:
        # 从数据集服务获取预览数据
        response = requests.get(
            f"{MODEL_SERVICE_URL}/dataset/{dataset_id}/preview",
            params={'limit': limit}
        )
        
        if response.status_code == 200:
            preview_data = response.json()
            
            return jsonify({
                'code': 200,
                'msg': '查询成功',
                'data': {
                    'columns': preview_data.get('columns', []),
                    'records': preview_data.get('records', [])
                }
            })
        else:
            raise Exception(f"数据集服务返回错误: {response.text}")
            
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'获取数据集预览失败: {str(e)}'
        }), 500 