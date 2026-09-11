// 检测页面逻辑
const DEFECT_COLORS = {
    'crazing': '#dc3545',
    'inclusion': '#28a745',
    'patches': '#007bff',
    'pitted_surface': '#ffc107',
    'rolled-in_scale': '#6f42c1',
    'scratches': '#17a2b8'
};

const DEFECT_NAMES_CN = {
    'crazing': '裂纹',
    'inclusion': '夹杂',
    'patches': '斑块',
    'pitted_surface': '麻点',
    'rolled-in_scale': '氧化皮',
    'scratches': '划痕'
};

let selectedFile = null;

// DOM 元素
const uploadArea = document.getElementById('upload-area');
const fileInput = document.getElementById('file-input');
const detectBtn = document.getElementById('detect-btn');
const confThreshold = document.getElementById('conf-threshold');
const confValue = document.getElementById('conf-value');

// 置信度滑块
confThreshold.addEventListener('input', () => {
    confValue.textContent = confThreshold.value;
});

// 点击上传
uploadArea.addEventListener('click', () => fileInput.click());

// 文件选择
fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
});

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
    if (e.dataTransfer.files.length > 0) {
        handleFile(e.dataTransfer.files[0]);
    }
});

// 处理选择的文件
function handleFile(file) {
    const allowedTypes = ['image/jpeg', 'image/png', 'image/bmp'];
    if (!allowedTypes.includes(file.type)) {
        showToast('不支持的文件格式，请上传 JPG/PNG/BMP 图片', 'error');
        return;
    }
    if (file.size > 10 * 1024 * 1024) {
        showToast('文件大小不能超过 10MB', 'error');
        return;
    }

    selectedFile = file;
    detectBtn.disabled = false;

    // 预览原图
    const reader = new FileReader();
    reader.onload = (e) => {
        document.getElementById('original-image').src = e.target.result;
        document.getElementById('original-card').style.display = '';
    };
    reader.readAsDataURL(file);

    // 重置结果
    resetResult();
}

// 重置结果显示
function resetResult() {
    document.getElementById('no-result').style.display = '';
    document.getElementById('result-details').style.display = 'none';
    document.getElementById('result-image-container').style.display = 'none';
    document.getElementById('result-badge').className = 'result-badge normal';
    document.getElementById('result-badge').textContent = '等待检测';
}

// 检测按钮
detectBtn.addEventListener('click', async () => {
    if (!selectedFile) {
        showToast('请先选择图片', 'error');
        return;
    }

    const mode = document.querySelector('input[name="mode"]:checked').value;
    const conf = confThreshold.value;

    const formData = new FormData();
    formData.append('image', selectedFile);
    formData.append('mode', mode);
    formData.append('conf_threshold', conf);

    showLoading('AI 检测中，请稍候...');
    try {
        const response = await axios.post('/api/detect/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
        displayResult(response.data);
        showToast('检测完成');
    } catch (error) {
        const msg = error.response?.data?.error || '检测失败';
        showToast(msg, 'error');
    } finally {
        hideLoading();
    }
});

// 显示检测结果
function displayResult(data) {
    document.getElementById('no-result').style.display = 'none';
    document.getElementById('result-details').style.display = '';

    // 结果徽章
    const badge = document.getElementById('result-badge');
    if (data.has_defect) {
        badge.className = 'result-badge defect';
        badge.textContent = `检测到 ${data.defect_count} 处缺陷`;
    } else {
        badge.className = 'result-badge normal';
        badge.textContent = '未检测到缺陷';
    }

    // 结果图片
    if (data.result_image_url) {
        document.getElementById('result-image').src = data.result_image_url + '?t=' + Date.now();
        document.getElementById('result-image-container').style.display = '';
    }

    // 统计数据
    document.getElementById('defect-count').textContent = data.defect_count;
    document.getElementById('confidence-avg').textContent = (data.confidence_avg * 100).toFixed(1) + '%';
    document.getElementById('inference-time').textContent = data.inference_time + 's';

    // 预测类别
    const predictedClass = document.getElementById('predicted-class');
    if (data.predicted_class_cn) {
        const color = DEFECT_COLORS[data.predicted_class] || '#666';
        predictedClass.innerHTML = `
            <span class="defect-tag" style="background-color:${color}">
                ${data.predicted_class_cn} (${data.predicted_class})
            </span>
        `;
    }

    // 概率分布
    const probList = document.getElementById('probability-list');
    probList.innerHTML = '';
    if (data.class_probabilities) {
        Object.entries(data.class_probabilities)
            .sort((a, b) => b[1] - a[1])
            .forEach(([cls, prob]) => {
                const color = DEFECT_COLORS[cls] || '#666';
                const nameCn = DEFECT_NAMES_CN[cls] || cls;
                probList.innerHTML += `
                    <div class="mb-2">
                        <div class="d-flex justify-content-between small">
                            <span>${nameCn}</span>
                            <span>${(prob * 100).toFixed(1)}%</span>
                        </div>
                        <div class="probability-bar">
                            <div class="probability-fill" style="width:${prob * 100}%;background-color:${color}"></div>
                        </div>
                    </div>
                `;
            });
    }

    // 缺陷详情列表
    const defectListContainer = document.getElementById('defect-list-container');
    const tbody = document.getElementById('defect-table-body');
    if (data.detections && data.detections.length > 0) {
        defectListContainer.style.display = '';
        tbody.innerHTML = '';
        data.detections.forEach((det, idx) => {
            const color = DEFECT_COLORS[det.class_name] || '#666';
            tbody.innerHTML += `
                <tr>
                    <td>${idx + 1}</td>
                    <td><span class="defect-tag" style="background-color:${color}">${det.class_name_cn}</span></td>
                    <td>${(det.confidence * 100).toFixed(1)}%</td>
                    <td>(${det.bbox[0]}, ${det.bbox[1]})</td>
                    <td>${det.bbox[2]} × ${det.bbox[3]}</td>
                    <td>${det.area} px²</td>
                </tr>
            `;
        });
    } else {
        defectListContainer.style.display = 'none';
    }
}
