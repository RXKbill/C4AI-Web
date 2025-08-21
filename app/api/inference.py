import os
import pandas as pd
import numpy as np
import torch
from flask import request, jsonify
from transformers import AutoModelForCausalLM
from . import api_bp
import json

# 全局变量存储模型
model = None

def load_model():
    """加载Predenergy模型"""
    global model
    if model is None:
        try:
            # 从本地 Predenergy 目录加载自定义模型实现
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            local_model_path = os.path.join(project_root, 'Predenergy')
            model = AutoModelForCausalLM.from_pretrained(local_model_path, trust_remote_code=True)
            print("Predenergy 模型加载成功")
        except Exception as e:
            print(f"模型加载失败: {e}")
            model = None
    return model

@api_bp.route('/inference/sample-data/<dataset_name>', methods=['GET'])
def get_sample_data(dataset_name):
    """获取示例数据集"""
    try:
        # 数据集文件路径
        dataset_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'dataset')
        
        # 支持的数据集
        datasets = {
            'ETTh2': 'ETTh2.csv',
            'Electricity': 'Electricity.csv',
            'Wind': 'Wind.csv',
            'ETTh1': 'ETTh1.csv',
            'ETTm1': 'ETTm1.csv',
            'ETTm2': 'ETTm2.csv'
        }
        
        if dataset_name not in datasets:
            return jsonify({
                'success': False,
                'message': f'不支持的数据集: {dataset_name}'
            })
        
        file_path = os.path.join(dataset_path, datasets[dataset_name])
        
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'message': f'数据集文件不存在: {file_path}'
            })
        
        # 读取CSV文件
        df = pd.read_csv(file_path)
        
        # 转换为字典列表格式
        data = df.to_dict('records')
        
        return jsonify({
            'success': True,
            'data': data,
            'message': f'成功加载数据集: {dataset_name}'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'加载数据集失败: {str(e)}'
        })

@api_bp.route('/inference/predict', methods=['POST'])
def inference_predict():
    """执行时序预测"""
    try:
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据为空'
            })
        
        # 提取参数
        csv_data = data.get('data', [])
        target_variable = data.get('target_variable')
        start_position = data.get('start_position', 0)
        mid_position = data.get('mid_position', 0)
        forecast_length = data.get('forecast_length', 100)
        
        if not csv_data or not target_variable:
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            })
        
        # 转换为DataFrame
        df = pd.DataFrame(csv_data)
        
        # 检查目标变量是否存在
        if target_variable not in df.columns:
            return jsonify({
                'success': False,
                'message': f'目标变量 {target_variable} 不存在'
            })
        
        # 提取目标变量的数值数据
        target_values = pd.to_numeric(df[target_variable], errors='coerce').dropna().values
        
        if len(target_values) == 0:
            return jsonify({
                'success': False,
                'message': '目标变量没有有效的数值数据'
            })
        
        # 加载模型
        model = load_model()
        if model is None:
            return jsonify({
                'success': False,
                'message': '模型加载失败'
            })
        
        # 准备输入数据
        lookback_length = min(1024, len(target_values) - forecast_length)
        if start_position + lookback_length > len(target_values):
            start_position = len(target_values) - lookback_length - forecast_length
        
        if start_position < 0:
            start_position = 0
        
        # 提取历史数据
        lookback_data = target_values[start_position:start_position + lookback_length]
        lookback_tensor = torch.tensor(lookback_data).unsqueeze(0).float()
        
        # 执行预测 - 使用正确的 Predenergy pipeline
        with torch.no_grad():
            forecast = model.generate(
                lookback_tensor, 
                max_new_tokens=forecast_length, 
                num_samples=20
            )
        
        # 处理预测结果 - forecast shape: [1, 20, forecast_length]
        forecast_values = forecast[0].mean(dim=0).numpy()  # 取20个样本的平均值
        
        # 获取真实值（如果存在）
        groundtruth_start = start_position + lookback_length
        groundtruth_end = min(groundtruth_start + forecast_length, len(target_values))
        groundtruth = target_values[groundtruth_start:groundtruth_end]
        
        # 如果真实值不足，用NaN填充
        if len(groundtruth) < forecast_length:
            groundtruth = np.concatenate([
                groundtruth,
                np.full(forecast_length - len(groundtruth), np.nan)
            ])
        
        # 准备返回数据
        history_labels = list(range(start_position, start_position + lookback_length))
        forecast_labels = list(range(start_position + lookback_length, start_position + lookback_length + forecast_length))
        
        result = {
            'labels': history_labels + forecast_labels,
            'history': lookback_data.tolist(),
            'prediction': forecast_values.tolist(),
            'groundtruth': groundtruth.tolist(),
            'start_position': start_position,
            'lookback_length': lookback_length,
            'forecast_length': forecast_length
        }
        
        return jsonify({
            'success': True,
            'result': result,
            'message': '预测完成'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'预测失败: {str(e)}'
        })

@api_bp.route('/inference/model-info', methods=['GET'])
def get_model_info():
    """获取模型信息"""
    try:
        model = load_model()
        if model is None:
            return jsonify({
                'success': False,
                'message': '模型未加载'
            })
        
        info = {
            'model_name': 'Predenergy',
            'model_type': 'Causal Language Model',
            'parameters': '128M',
            'framework': 'Transformers',
            'capabilities': ['Zero-shot Time Series Forecasting', 'Multi-step Prediction'],
            'supported_formats': ['CSV'],
            'max_input_length': 1024,
            'max_forecast_length': 1000
        }
        
        return jsonify({
            'success': True,
            'info': info
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取模型信息失败: {str(e)}'
        })
