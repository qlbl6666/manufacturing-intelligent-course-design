// 认证相关功能
// 注意：请求路径直接写 /api/...，不设置 baseURL 避免路径重复

// 响应拦截器：处理 401 未授权
axios.interceptors.response.use(
    response => response,
    error => {
        if (error.response && error.response.status === 401) {
            // 未登录，跳转到登录页
            if (!window.location.pathname.includes('/login') && !window.location.pathname.includes('/register')) {
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

// 显示 Toast 通知
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'primary'} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    container.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
    bsToast.show();
    toast.addEventListener('hidden.bs.toast', () => toast.remove());
}

// 显示/隐藏加载动画
function showLoading(text = '处理中...') {
    let overlay = document.getElementById('loading-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'loading-overlay';
        overlay.className = 'loading-overlay';
        overlay.innerHTML = `
            <div class="text-center">
                <div class="spinner-border" role="status"></div>
                <p class="mt-3 text-muted">${text}</p>
            </div>
        `;
        document.body.appendChild(overlay);
    }
    overlay.classList.add('active');
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.classList.remove('active');
}

// 检查登录状态
async function checkAuth() {
    try {
        const response = await axios.get('/api/auth/me');
        const user = response.data.user;
        // 更新导航栏用户名
        const usernameEl = document.getElementById('nav-username');
        if (usernameEl) usernameEl.textContent = user.username;
        // 管理员显示模型管理菜单
        if (user.role === 'admin') {
            document.querySelectorAll('.admin-only').forEach(el => el.style.display = '');
        }
        return user;
    } catch (error) {
        return null;
    }
}

// 登出
async function logout() {
    try {
        await axios.post('/api/auth/logout');
        showToast('已退出登录');
        setTimeout(() => window.location.href = '/login', 500);
    } catch (error) {
        showToast('退出失败', 'error');
    }
}

// 页面加载时检查登录状态（登录注册页除外）
document.addEventListener('DOMContentLoaded', () => {
    const path = window.location.pathname;
    if (!path.includes('/login') && !path.includes('/register')) {
        checkAuth().then(user => {
            if (!user) {
                window.location.href = '/login';
            }
        });
    }
});
