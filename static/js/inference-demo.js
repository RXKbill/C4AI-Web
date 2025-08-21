// 全局变量
let currentData = null;
let currentPage = 1;
let rowsPerPage = 10;
let trendChart = null;
let predictionChart = null;
let currentStep = 1;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeUploadArea();
    feather.replace();
});

// 初始化上传区域
function initializeUploadArea() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');

    // 点击上传
    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });

    // 文件选择
    fileInput.addEventListener('change', handleFileSelect);

    // 拖拽上传
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });
}

// 处理文件选择
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        handleFile(file);
    }
}

// 处理文件
function handleFile(file) {
    if (!file.name.toLowerCase().endsWith('.csv')) {
        alert('请选择CSV格式的文件');
        return;
    }

    const reader = new FileReader();
    reader.onload = function(e) {
        const csv = e.target.result;
        Papa.parse(csv, {
            header: true,
            complete: function(results) {
                if (results.errors.length > 0) {
                    alert('CSV文件解析错误：' + results.errors[0].message);
                    return;
                }
                currentData = results.data;
                showStep2();
            }
        });
    };
    reader.readAsText(file);
}

// 加载示例数据
function loadSampleData(datasetName) {
    fetch(`/api/inference/sample-data/${datasetName}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                currentData = data.data;
                showStep2();
            } else {
                alert('加载示例数据失败：' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('加载示例数据失败');
        });
}

// 显示步骤2
function showStep2() {
    updateStepIndicator(2);
    document.getElementById('step1-content').style.display = 'none';
    document.getElementById('step2-content').style.display = 'block';
    document.getElementById('step3-content').style.display = 'none';
    document.getElementById('step4-content').style.display = 'none';
    document.getElementById('step5-content').style.display = 'none';
    
    displayDataPreview();
}

// 显示数据预览
function displayDataPreview() {
    if (!currentData || currentData.length === 0) return;

    // 更新统计信息
    document.getElementById('totalRows').textContent = currentData.length;
    document.getElementById('totalColumns').textContent = Object.keys(currentData[0]).length;
    document.getElementById('dataType').textContent = 'CSV';
    
    // 计算缺失值
    let missingCount = 0;
    currentData.forEach(row => {
        Object.values(row).forEach(value => {
            if (value === '' || value === null || value === undefined) {
                missingCount++;
            }
        });
    });
    document.getElementById('missingValues').textContent = missingCount;

    // 显示表格
    displayDataTable();
}

// 显示数据表格
function displayDataTable() {
    const headers = Object.keys(currentData[0]);
    const tableHeader = document.getElementById('tableHeader');
    const tableBody = document.getElementById('tableBody');

    // 清空表格
    tableHeader.innerHTML = '';
    tableBody.innerHTML = '';

    // 添加表头
    const headerRow = document.createElement('tr');
    headers.forEach(header => {
        const th = document.createElement('th');
        th.textContent = header;
        headerRow.appendChild(th);
    });
    tableHeader.appendChild(headerRow);

    // 计算分页
    const totalPages = Math.ceil(currentData.length / rowsPerPage);
    document.getElementById('totalPages').textContent = totalPages;
    document.getElementById('currentPage').textContent = currentPage;

    // 显示当前页数据
    const startIndex = (currentPage - 1) * rowsPerPage;
    const endIndex = Math.min(startIndex + rowsPerPage, currentData.length);

    for (let i = startIndex; i < endIndex; i++) {
        const row = document.createElement('tr');
        headers.forEach(header => {
            const td = document.createElement('td');
            td.textContent = currentData[i][header] || '';
            row.appendChild(td);
        });
        tableBody.appendChild(row);
    }

    // 更新分页按钮状态
    document.getElementById('prevPage').disabled = currentPage === 1;
    document.getElementById('nextPage').disabled = currentPage === totalPages;
}

// 切换页面
function changePage(direction) {
    const totalPages = Math.ceil(currentData.length / rowsPerPage);
    const newPage = currentPage + direction;
    
    if (newPage >= 1 && newPage <= totalPages) {
        currentPage = newPage;
        displayDataTable();
    }
}

// 显示步骤3
function showStep3() {
    updateStepIndicator(3);
    document.getElementById('step1-content').style.display = 'none';
    document.getElementById('step2-content').style.display = 'none';
    document.getElementById('step3-content').style.display = 'block';
    document.getElementById('step4-content').style.display = 'none';
    document.getElementById('step5-content').style.display = 'none';
    
    populateVariableSelect();
}

// 填充变量选择下拉框
function populateVariableSelect() {
    const select = document.getElementById('targetVariable');
    select.innerHTML = '<option value="">请选择目标变量</option>';
    
    if (currentData && currentData.length > 0) {
        const headers = Object.keys(currentData[0]);
        headers.forEach(header => {
            const option = document.createElement('option');
            option.value = header;
            option.textContent = header;
            select.appendChild(option);
        });
    }

    // 添加选择事件
    select.addEventListener('change', function() {
        if (this.value) {
            showVariableInfo(this.value);
            showStep4();
        }
    });
}

// 显示变量信息
function showVariableInfo(variableName) {
    const values = currentData.map(row => parseFloat(row[variableName])).filter(val => !isNaN(val));
    
    if (values.length === 0) {
        document.getElementById('variableInfo').innerHTML = '<p class="text-danger">该变量没有有效的数值数据</p>';
        return;
    }

    const min = Math.min(...values);
    const max = Math.max(...values);
    const mean = values.reduce((a, b) => a + b, 0) / values.length;
    const std = Math.sqrt(values.reduce((sq, n) => sq + Math.pow(n - mean, 2), 0) / values.length);

    document.getElementById('variableInfo').innerHTML = `
        <p><strong>变量名：</strong>${variableName}</p>
        <p><strong>数据点数：</strong>${values.length}</p>
        <p><strong>最小值：</strong>${min.toFixed(4)}</p>
        <p><strong>最大值：</strong>${max.toFixed(4)}</p>
        <p><strong>平均值：</strong>${mean.toFixed(4)}</p>
        <p><strong>标准差：</strong>${std.toFixed(4)}</p>
    `;

    // 更新统计图表
    updateVariableStats(values);
}

// 更新变量统计
function updateVariableStats(values) {
    const statsDiv = document.getElementById('variableStats');
    
    // 简单的统计信息
    const sortedValues = values.sort((a, b) => a - b);
    const q25 = sortedValues[Math.floor(sortedValues.length * 0.25)];
    const q50 = sortedValues[Math.floor(sortedValues.length * 0.5)];
    const q75 = sortedValues[Math.floor(sortedValues.length * 0.75)];

    statsDiv.innerHTML = `
        <div class="row text-center">
            <div class="col-4">
                <h6 class="text-primary">Q1</h6>
                <p>${q25.toFixed(2)}</p>
            </div>
            <div class="col-4">
                <h6 class="text-success">中位数</h6>
                <p>${q50.toFixed(2)}</p>
            </div>
            <div class="col-4">
                <h6 class="text-warning">Q3</h6>
                <p>${q75.toFixed(2)}</p>
            </div>
        </div>
    `;
}

// 显示步骤4
function showStep4() {
    updateStepIndicator(4);
    document.getElementById('step1-content').style.display = 'none';
    document.getElementById('step2-content').style.display = 'none';
    document.getElementById('step3-content').style.display = 'none';
    document.getElementById('step4-content').style.display = 'block';
    document.getElementById('step5-content').style.display = 'none';
    
    drawTrendChart();
}

// 绘制趋势图
function drawTrendChart() {
    const variableName = document.getElementById('targetVariable').value;
    const values = currentData.map(row => parseFloat(row[variableName])).filter(val => !isNaN(val));
    const labels = Array.from({length: values.length}, (_, i) => i);

    const ctx = document.getElementById('trendChart').getContext('2d');
    
    if (trendChart) {
        trendChart.destroy();
    }

    trendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: variableName,
                data: values,
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: `${variableName} 趋势图`
                },
                zoom: {
                    zoom: {
                        wheel: {
                            enabled: true,
                        },
                        pinch: {
                            enabled: true
                        },
                        mode: 'xy',
                    },
                    pan: {
                        enabled: true,
                        mode: 'xy',
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: '时间步'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: variableName
                    }
                }
            }
        }
    });
}

// 放大图表
function zoomChart() {
    const start = parseInt(document.getElementById('zoomStart').value);
    const end = parseInt(document.getElementById('zoomEnd').value);
    
    if (isNaN(start) || isNaN(end) || start >= end) {
        alert('请输入有效的起始和结束位置');
        return;
    }

    if (trendChart) {
        trendChart.zoomScale('x', {min: start, max: end});
        trendChart.update();
    }
}

// 重置图表视图
function resetZoom() {
    if (trendChart) {
        trendChart.resetZoom();
    }
}

// 显示步骤5
function showStep5() {
    updateStepIndicator(5);
    document.getElementById('step1-content').style.display = 'none';
    document.getElementById('step2-content').style.display = 'none';
    document.getElementById('step3-content').style.display = 'none';
    document.getElementById('step4-content').style.display = 'none';
    document.getElementById('step5-content').style.display = 'block';
    
    // 设置默认值
    const dataLength = currentData.length;
    document.getElementById('startPosition').value = Math.floor(dataLength * 0.7);
    document.getElementById('midPosition').value = Math.floor(dataLength * 0.8);
    document.getElementById('forecastLength').value = Math.min(100, Math.floor(dataLength * 0.1));
}

// 开始预测
function startPrediction() {
    const startPosition = parseInt(document.getElementById('startPosition').value);
    const midPosition = parseInt(document.getElementById('midPosition').value);
    const forecastLength = parseInt(document.getElementById('forecastLength').value);
    const targetVariable = document.getElementById('targetVariable').value;

    if (!targetVariable) {
        alert('请先选择目标变量');
        return;
    }

    if (isNaN(startPosition) || isNaN(midPosition) || isNaN(forecastLength)) {
        alert('请输入有效的预测参数');
        return;
    }

    // 显示加载状态
    document.getElementById('predictionChartContainer').style.display = 'block';
    document.getElementById('predictionLoading').style.display = 'flex';

    // 准备预测数据
    const predictionData = {
        data: currentData,
        target_variable: targetVariable,
        start_position: startPosition,
        mid_position: midPosition,
        forecast_length: forecastLength
    };

    // 发送预测请求
    fetch('/api/inference/predict', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(predictionData)
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('predictionLoading').style.display = 'none';
        
        if (data.success) {
            displayPredictionResults(data.result);
        } else {
            alert('预测失败：' + data.message);
        }
    })
    .catch(error => {
        document.getElementById('predictionLoading').style.display = 'none';
        console.error('Error:', error);
        alert('预测请求失败');
    });
}

// 显示预测结果
function displayPredictionResults(result) {
    const ctx = document.getElementById('predictionChart').getContext('2d');
    
    if (predictionChart) {
        predictionChart.destroy();
    }

    predictionChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: result.labels,
            datasets: [
                {
                    label: '历史数据',
                    data: result.history,
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.1
                },
                {
                    label: '预测数据',
                    data: result.prediction,
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    tension: 0.1
                },
                {
                    label: '真实值',
                    data: result.groundtruth,
                    borderColor: 'rgb(54, 162, 235)',
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    tension: 0.1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: '时序预测结果'
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: '时间步'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: document.getElementById('targetVariable').value
                    }
                }
            }
        }
    });

    // 显示预测统计信息
    displayPredictionStats(result);
    document.getElementById('predictionResults').style.display = 'block';
}

// 显示预测统计信息
function displayPredictionStats(result) {
    const statsDiv = document.getElementById('predictionStats');
    const modelDiv = document.getElementById('modelInfo');

    // 计算预测误差
    const mse = calculateMSE(result.prediction, result.groundtruth);
    const mae = calculateMAE(result.prediction, result.groundtruth);
    const mape = calculateMAPE(result.prediction, result.groundtruth);

    statsDiv.innerHTML = `
        <p><strong>均方误差 (MSE)：</strong>${mse.toFixed(4)}</p>
        <p><strong>平均绝对误差 (MAE)：</strong>${mae.toFixed(4)}</p>
        <p><strong>平均绝对百分比误差 (MAPE)：</strong>${mape.toFixed(2)}%</p>
        <p><strong>预测长度：</strong>${result.prediction.length}</p>
    `;

    modelDiv.innerHTML = `
        <p><strong>模型：</strong>Predenergy</p>
        <p><strong>预测方法：</strong>零样本生成</p>
        <p><strong>输入长度：</strong>${result.history.length}</p>
        <p><strong>生成样本数：</strong>20</p>
    `;
}

// 计算MSE
function calculateMSE(pred, actual) {
    if (pred.length !== actual.length) return 0;
    return pred.reduce((sum, p, i) => sum + Math.pow(p - actual[i], 2), 0) / pred.length;
}

// 计算MAE
function calculateMAE(pred, actual) {
    if (pred.length !== actual.length) return 0;
    return pred.reduce((sum, p, i) => sum + Math.abs(p - actual[i]), 0) / pred.length;
}

// 计算MAPE
function calculateMAPE(pred, actual) {
    if (pred.length !== actual.length) return 0;
    return pred.reduce((sum, p, i) => sum + Math.abs((p - actual[i]) / actual[i]), 0) / pred.length * 100;
}

// 更新步骤指示器
function updateStepIndicator(step) {
    currentStep = step;
    
    // 重置所有步骤
    for (let i = 1; i <= 5; i++) {
        const stepElement = document.getElementById(`step${i}`);
        stepElement.classList.remove('active', 'completed');
    }
    
    // 设置当前步骤和已完成步骤
    for (let i = 1; i <= step; i++) {
        const stepElement = document.getElementById(`step${i}`);
        if (i === step) {
            stepElement.classList.add('active');
        } else {
            stepElement.classList.add('completed');
        }
    }
}

// 添加步骤导航功能
document.addEventListener('click', function(e) {
    if (e.target.closest('.step')) {
        const stepElement = e.target.closest('.step');
        const stepNumber = parseInt(stepElement.id.replace('step', ''));
        
        // 检查是否可以跳转到该步骤
        if (canNavigateToStep(stepNumber)) {
            navigateToStep(stepNumber);
        }
    }
});

// 检查是否可以导航到指定步骤
function canNavigateToStep(step) {
    switch(step) {
        case 1: return true;
        case 2: return currentData !== null;
        case 3: return currentData !== null;
        case 4: return currentData !== null && document.getElementById('targetVariable').value;
        case 5: return currentData !== null && document.getElementById('targetVariable').value;
        default: return false;
    }
}

// 导航到指定步骤
function navigateToStep(step) {
    switch(step) {
        case 1:
            document.getElementById('step1-content').style.display = 'block';
            document.getElementById('step2-content').style.display = 'none';
            document.getElementById('step3-content').style.display = 'none';
            document.getElementById('step4-content').style.display = 'none';
            document.getElementById('step5-content').style.display = 'none';
            updateStepIndicator(1);
            break;
        case 2:
            showStep2();
            break;
        case 3:
            showStep3();
            break;
        case 4:
            showStep4();
            break;
        case 5:
            showStep5();
            break;
    }
}
