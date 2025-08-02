from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import api_bp
# from ..models import ModelService, ModelVersion, ModelTraining, ModelDeployment
from .. import db
from datetime import datetime
import requests
import json

# 模型服务配置
MODEL_SERVICE_URL = "http://model-service:8000"  # 时序预测大模型服务的地址

@api_bp.route('/model/versions', methods=['GET'])
@jwt_required()
def get_model_versions():
    page = request.args.get('pageNum', 1, type=int)
    per_page = request.args.get('pageSize', 10, type=int)
    
    query = ModelVersion.query
    
    model_type = request.args.get('modelType')
    if model_type:
        query = query.filter(ModelVersion.model_type == model_type)
    
    status = request.args.get('status')
    if status:
        query = query.filter(ModelVersion.status == status)
    
    pagination = query.order_by(ModelVersion.created_at.desc()).paginate(page=page, per_page=per_page)
    versions = pagination.items
    
    return jsonify({
        'code': 200,
        'msg': '查询成功',
        'total': pagination.total,
        'rows': [{
            'versionId': version.version_id,
            'modelType': version.model_type,
            'versionNumber': version.version_number,
            'description': version.description,
            'parameters': version.parameters,
            'performance': version.performance_metrics,
            'status': version.status,
            'createdBy': version.created_by,
            'createdAt': version.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for version in versions]
    })

@api_bp.route('/model/train', methods=['POST'])
@jwt_required()
def start_model_training():
    data = request.get_json()
    
    # 创建训练记录
    training = ModelTraining(
        model_type=data.get('modelType'),
        dataset_config=data.get('datasetConfig'),
        training_params=data.get('trainingParams'),
        status='pending',
        created_by=get_jwt_identity()
    )
    
    db.session.add(training)
    
    try:
        db.session.commit()
        
        # 异步调用模型服务进行训练
        try:
            response = requests.post(
                f"{MODEL_SERVICE_URL}/train",
                json={
                    'trainingId': training.training_id,
                    'modelType': training.model_type,
                    'datasetConfig': training.dataset_config,
                    'trainingParams': training.training_params
                }
            )
            
            if response.status_code == 200:
                return jsonify({
                    'code': 200,
                    'msg': '训练任务已提交',
                    'trainingId': training.training_id
                })
            else:
                raise Exception(f"模型服务返回错误: {response.text}")
                
        except Exception as e:
            training.status = 'failed'
            training.error_message = str(e)
            db.session.commit()
            
            return jsonify({
                'code': 500,
                'msg': f'提交训练任务失败: {str(e)}'
            }), 500
            
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'创建训练记录失败: {str(e)}'
        }), 500

@api_bp.route('/model/train/<int:training_id>', methods=['GET'])
@jwt_required()
def get_training_status(training_id):
    training = ModelTraining.query.get(training_id)
    
    if not training:
        return jsonify({
            'code': 404,
            'msg': '训练记录不存在'
        }), 404
    
    try:
        # 从模型服务获取最新状态
        response = requests.get(f"{MODEL_SERVICE_URL}/train/{training_id}/status")
        
        if response.status_code == 200:
            status_data = response.json()
            
            # 更新训练记录
            training.status = status_data.get('status', training.status)
            training.progress = status_data.get('progress', training.progress)
            training.metrics = status_data.get('metrics', training.metrics)
            training.error_message = status_data.get('errorMessage', training.error_message)
            
            db.session.commit()
            
            return jsonify({
                'code': 200,
                'msg': '查询成功',
                'data': {
                    'trainingId': training.training_id,
                    'modelType': training.model_type,
                    'status': training.status,
                    'progress': training.progress,
                    'metrics': training.metrics,
                    'errorMessage': training.error_message,
                    'createdAt': training.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'updatedAt': training.updated_at.strftime('%Y-%m-%d %H:%M:%S') if training.updated_at else None
                }
            })
        else:
            raise Exception(f"模型服务返回错误: {response.text}")
            
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'获取训练状态失败: {str(e)}'
        }), 500

@api_bp.route('/model/deploy', methods=['POST'])
@jwt_required()
def deploy_model():
    data = request.get_json()
    
    # 创建部署记录
    deployment = ModelDeployment(
        version_id=data.get('versionId'),
        environment=data.get('environment', 'production'),
        config=data.get('config'),
        status='pending',
        deployed_by=get_jwt_identity()
    )
    
    db.session.add(deployment)
    
    try:
        db.session.commit()
        
        # 调用模型服务进行部署
        try:
            response = requests.post(
                f"{MODEL_SERVICE_URL}/deploy",
                json={
                    'deploymentId': deployment.deployment_id,
                    'versionId': deployment.version_id,
                    'environment': deployment.environment,
                    'config': deployment.config
                }
            )
            
            if response.status_code == 200:
                return jsonify({
                    'code': 200,
                    'msg': '部署任务已提交',
                    'deploymentId': deployment.deployment_id
                })
            else:
                raise Exception(f"模型服务返回错误: {response.text}")
                
        except Exception as e:
            deployment.status = 'failed'
            deployment.error_message = str(e)
            db.session.commit()
            
            return jsonify({
                'code': 500,
                'msg': f'提交部署任务失败: {str(e)}'
            }), 500
            
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'创建部署记录失败: {str(e)}'
        }), 500

@api_bp.route('/model/predict', methods=['POST'])
@jwt_required()
def predict():
    data = request.get_json()
    
    try:
        # 调用模型服务进行预测
        response = requests.post(
            f"{MODEL_SERVICE_URL}/predict",
            json={
                'modelType': data.get('modelType'),
                'inputData': data.get('inputData'),
                'parameters': data.get('parameters')
            }
        )
        
        if response.status_code == 200:
            prediction_result = response.json()
            
            return jsonify({
                'code': 200,
                'msg': '预测成功',
                'data': {
                    'predictions': prediction_result.get('predictions'),
                    'confidence': prediction_result.get('confidence'),
                    'metadata': prediction_result.get('metadata')
                }
            })
        else:
            raise Exception(f"模型服务返回错误: {response.text}")
            
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'预测失败: {str(e)}'
        }), 500

@api_bp.route('/model/batch-predict', methods=['POST'])
@jwt_required()
def batch_predict():
    data = request.get_json()
    
    try:
        # 调用模型服务进行批量预测
        response = requests.post(
            f"{MODEL_SERVICE_URL}/batch-predict",
            json={
                'modelType': data.get('modelType'),
                'inputDataList': data.get('inputDataList'),
                'parameters': data.get('parameters')
            }
        )
        
        if response.status_code == 200:
            prediction_results = response.json()
            
            return jsonify({
                'code': 200,
                'msg': '批量预测成功',
                'data': {
                    'predictions': prediction_results.get('predictions'),
                    'metadata': prediction_results.get('metadata')
                }
            })
        else:
            raise Exception(f"模型服务返回错误: {response.text}")
            
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'批量预测失败: {str(e)}'
        }), 500

@api_bp.route('/model/evaluate', methods=['POST'])
@jwt_required()
def evaluate_model():
    data = request.get_json()
    
    try:
        # 调用模型服务进行评估
        response = requests.post(
            f"{MODEL_SERVICE_URL}/evaluate",
            json={
                'modelType': data.get('modelType'),
                'versionId': data.get('versionId'),
                'testData': data.get('testData'),
                'metrics': data.get('metrics', ['mse', 'mae', 'rmse', 'mape'])
            }
        )
        
        if response.status_code == 200:
            evaluation_result = response.json()
            
            return jsonify({
                'code': 200,
                'msg': '评估成功',
                'data': {
                    'metrics': evaluation_result.get('metrics'),
                    'details': evaluation_result.get('details'),
                    'metadata': evaluation_result.get('metadata')
                }
            })
        else:
            raise Exception(f"模型服务返回错误: {response.text}")
            
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'评估失败: {str(e)}'
        }), 500 