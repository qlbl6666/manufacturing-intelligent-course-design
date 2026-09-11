// 历史记录页面逻辑
let currentPage = 1;
const perPage = 10;

const DEFECT_COLORS = {
    'crazing': '#dc3545', 'inclusion': '#28a745', 'patches': '#007bff',
    'pitted_surface': '#ffc107', 'rolled-in_scale': '#6f42c1', 'scratches': '#17a2b8'
};
const DEFECT_NAMES_CN = {
    'crazing': '裂纹', 'inclusion': '夹杂', 'patches': '斑块',
    'pitted_surface': '麻点', 'rolled-in_scale': '氧化皮', 'scratches': '划痕'
};

// 筛选变化时重新加载
['filter-defect', 'filter-has-defect', 'filter-start', 'filter-end'].forEach(id => {
    document.getElementById(id).addEventListener('change', () => {
        currentPage = 1;
        loadRecords();
    });
});

// 加载记录
async function loadRecords(page = 1) {
    currentPage = page;
    const params = new URLSearchParams({
        page: page,
        per_page: perPage,
    });

    const defectType = document.getElementById('filter-defect').value;
    const hasDefect = document.getElementById('filter-has-defect').value;
    const startDate = document.getElementById('filter-start').value;
    const endDate = document.getElementById('filter-end').value;

    if (defectType) params.append('defect_type', defectType);
    if (hasDefect) params.append('has_defect', hasDefect);
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    try {
        const response = await axios.get(`/api/records?${params}`);
        renderRecords(response.data.records);
        renderPagination(response.data.pagination);
    } catch (error) {
        document.getElementById('records-tbody').innerHTML =
            '<tr><td colspan="9" class="text-center text-danger">加载失败</td></tr>';
    }
}

// 渲染记录列表
function renderRecords(records) {
    const tbody = document.getElementById('records-tbody');
    if (records.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="text-center text-muted py-4">暂无检测记录</td></tr>';
        return;
    }

    tbody.innerHTML = records.map(r => {
        const defectTags = (r.defect_types || []).map(t =>
            `<span class="defect-tag" style="background-color:${DEFECT_COLORS[t] || '#666'}">${DEFECT_NAMES_CN[t] || t}</span>`
        ).join(' ');

        return `
            <tr>
                <td>${r.id}</td>
                <td><img src="${r.image_url}" style="width:50px;height:50px;object-fit:cover;border-radius:4px;cursor:pointer;" onclick="viewDetail(${r.id})"></td>
                <td class="small">${r.created_at}</td>
                <td><span class="badge bg-${r.detection_mode === 'precise' ? 'primary' : 'secondary'}">${r.detection_mode === 'precise' ? '精确' : '快速'}</span></td>
                <td>${r.has_defect ? '<span class="text-danger fw-semibold">有缺陷</span>' : '<span class="text-success fw-semibold">正常</span>'}</td>
                <td>${r.defect_count}</td>
                <td>${defectTags || '-'}</td>
                <td>${(r.confidence_avg * 100).toFixed(1)}%</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="viewDetail(${r.id})"><i class="bi bi-eye"></i></button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteRecord(${r.id})"><i class="bi bi-trash"></i></button>
                </td>
            </tr>
        `;
    }).join('');
}

// 渲染分页
function renderPagination(pagination) {
    const nav = document.getElementById('pagination-nav');
    if (pagination.pages <= 1) {
        nav.innerHTML = '';
        return;
    }

    let html = '<ul class="pagination pagination-sm justify-content-center">';
    html += `<li class="page-item ${pagination.has_prev ? '' : 'disabled'}"><a class="page-link" href="#" onclick="loadRecords(${currentPage - 1});return false;">上一页</a></li>`;

    for (let i = 1; i <= pagination.pages; i++) {
        html += `<li class="page-item ${i === currentPage ? 'active' : ''}"><a class="page-link" href="#" onclick="loadRecords(${i});return false;">${i}</a></li>`;
    }

    html += `<li class="page-item ${pagination.has_next ? '' : 'disabled'}"><a class="page-link" href="#" onclick="loadRecords(${currentPage + 1});return false;">下一页</a></li>`;
    html += '</ul>';
    html += `<div class="text-center small text-muted">共 ${pagination.total} 条记录</div>`;
    nav.innerHTML = html;
}

// 查看详情
async function viewDetail(recordId) {
    try {
        const response = await axios.get(`/api/records/${recordId}`);
        const record = response.data.record;
        const modalBody = document.getElementById('detail-modal-body');

        let defectDetails = '';
        if (record.details && record.details.length > 0) {
            defectDetails = `
                <h6 class="fw-semibold mt-3">缺陷详情</h6>
                <div class="table-responsive">
                    <table class="table table-sm">
                        <thead><tr><th>序号</th><th>类型</th><th>置信度</th><th>位置</th><th>尺寸</th><th>面积</th></tr></thead>
                        <tbody>
                            ${record.details.map((d, i) => `
                                <tr>
                                    <td>${i + 1}</td>
                                    <td><span class="defect-tag" style="background-color:${DEFECT_COLORS[d.defect_type] || '#666'}">${d.defect_type_cn}</span></td>
                                    <td>${(d.confidence * 100).toFixed(1)}%</td>
                                    <td>(${d.bbox.x}, ${d.bbox.y})</td>
                                    <td>${d.bbox.w} × ${d.bbox.h}</td>
                                    <td>${d.area} px²</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        }

        modalBody.innerHTML = `
            <div class="row">
                <div class="col-md-6 text-center">
                    <h6 class="fw-semibold">原始图片</h6>
                    <img src="${record.image_url}" class="img-fluid rounded mb-2" style="max-height:300px;">
                </div>
                <div class="col-md-6 text-center">
                    <h6 class="fw-semibold">检测结果</h6>
                    <img src="${record.result_image_url || record.image_url}" class="img-fluid rounded mb-2" style="max-height:300px;">
                </div>
            </div>
            <div class="mt-3">
                <p><strong>记录ID：</strong>${record.id}</p>
                <p><strong>检测时间：</strong>${record.created_at}</p>
                <p><strong>检测模式：</strong>${record.detection_mode === 'precise' ? '精确模式' : '快速模式'}</p>
                <p><strong>检测结果：</strong>${record.has_defect ? '<span class="text-danger">检测到缺陷</span>' : '<span class="text-success">未检测到缺陷</span>'}</p>
                <p><strong>缺陷数量：</strong>${record.defect_count}</p>
                <p><strong>平均置信度：</strong>${(record.confidence_avg * 100).toFixed(1)}%</p>
            </div>
            ${defectDetails}
            <div class="text-end mt-3">
                <a class="btn btn-sm btn-outline-primary" href="/api/records/${record.id}/export" target="_blank"><i class="bi bi-download me-1"></i>导出CSV</a>
            </div>
        `;

        new bootstrap.Modal(document.getElementById('detail-modal')).show();
    } catch (error) {
        showToast('加载详情失败', 'error');
    }
}

// 删除记录
async function deleteRecord(recordId) {
    if (!confirm('确定要删除这条记录吗？')) return;
    try {
        await axios.delete(`/api/records/${recordId}`);
        showToast('记录已删除');
        loadRecords(currentPage);
    } catch (error) {
        showToast('删除失败', 'error');
    }
}

// 导出全部
function exportAll() {
    window.open('/api/records/export/all', '_blank');
}

// 页面加载
document.addEventListener('DOMContentLoaded', () => loadRecords());
