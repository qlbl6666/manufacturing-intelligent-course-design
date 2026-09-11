// 统计页面逻辑
const DEFECT_NAMES_CN = {
    'crazing': '裂纹', 'inclusion': '夹杂', 'patches': '斑块',
    'pitted_surface': '麻点', 'rolled-in_scale': '氧化皮', 'scratches': '划痕'
};
const DEFECT_COLORS = ['#dc3545', '#28a745', '#007bff', '#ffc107', '#6f42c1', '#17a2b8'];

let trendChart, distributionChart, modeChart, classConfChart;

// 初始化图表
function initCharts() {
    trendChart = echarts.init(document.getElementById('trend-chart'));
    distributionChart = echarts.init(document.getElementById('distribution-chart'));
    modeChart = echarts.init(document.getElementById('mode-chart'));
    classConfChart = echarts.init(document.getElementById('class-conf-chart'));
    window.addEventListener('resize', () => {
        trendChart.resize();
        distributionChart.resize();
        modeChart.resize();
        classConfChart.resize();
    });
}

// 加载统计数据
async function loadStats() {
    try {
        const [overviewRes, perfRes] = await Promise.all([
            axios.get('/api/stats/overview'),
            axios.get('/api/stats/model-performance')
        ]);

        renderOverview(overviewRes.data.overview);
        renderTrend(overviewRes.data.daily_trend);
        renderDistribution(overviewRes.data.defect_distribution);
        renderModeUsage(perfRes.data.detection_mode_usage);
        renderClassPerformance(perfRes.data.class_performance);
    } catch (error) {
        showToast('统计数据加载失败', 'error');
    }
}

// 渲染概览
function renderOverview(overview) {
    document.getElementById('stat-total').textContent = overview.total_records;
    document.getElementById('stat-defect').textContent = overview.defect_records;
    document.getElementById('stat-rate').textContent = overview.defect_rate + '%';
    document.getElementById('stat-conf').textContent = (overview.avg_confidence * 100).toFixed(1) + '%';
}

// 渲染趋势图
function renderTrend(dailyTrend) {
    trendChart.setOption({
        tooltip: { trigger: 'axis' },
        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
        xAxis: {
            type: 'category',
            data: dailyTrend.map(d => d.date.slice(5)),
            axisLine: { lineStyle: { color: '#999' } }
        },
        yAxis: { type: 'value', minInterval: 1 },
        series: [{
            name: '检测次数',
            type: 'line',
            smooth: true,
            data: dailyTrend.map(d => d.count),
            itemStyle: { color: '#1a3a5c' },
            areaStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: 'rgba(26,58,92,0.3)' },
                    { offset: 1, color: 'rgba(26,58,92,0.05)' }
                ])
            }
        }]
    });
}

// 渲染缺陷分布饼图
function renderDistribution(distribution) {
    const data = distribution
        .filter(d => d.count > 0)
        .map(d => ({ name: d.type_cn, value: d.count }));

    distributionChart.setOption({
        tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
        legend: { orient: 'vertical', left: 'left', textStyle: { fontSize: 11 } },
        series: [{
            type: 'pie',
            radius: ['40%', '70%'],
            center: ['60%', '50%'],
            avoidLabelOverlap: true,
            itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
            label: { show: true, formatter: '{b}\n{d}%', fontSize: 11 },
            data: data.length > 0 ? data : [{ name: '暂无数据', value: 1 }],
            color: DEFECT_COLORS
        }]
    });
}

// 渲染模式使用情况
function renderModeUsage(modeUsage) {
    modeChart.setOption({
        tooltip: { trigger: 'item' },
        series: [{
            type: 'pie',
            radius: '65%',
            data: [
                { name: '精确模式', value: modeUsage.precise, itemStyle: { color: '#1a3a5c' } },
                { name: '快速模式', value: modeUsage.fast, itemStyle: { color: '#ff6b35' } }
            ],
            label: { formatter: '{b}\n{c}次 ({d}%)', fontSize: 12 }
        }]
    });
}

// 渲染各类别置信度
function renderClassPerformance(classPerformance) {
    const classes = Object.keys(classPerformance);
    const values = classes.map(c => classPerformance[c].avg_confidence * 100);
    const names = classes.map(c => classPerformance[c].type_cn);

    classConfChart.setOption({
        tooltip: { trigger: 'axis', formatter: '{b}: {c}%' },
        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
        xAxis: { type: 'category', data: names, axisLabel: { fontSize: 11 } },
        yAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%' } },
        series: [{
            type: 'bar',
            data: values,
            itemStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: '#ff6b35' },
                    { offset: 1, color: '#1a3a5c' }
                ]),
                borderRadius: [4, 4, 0, 0]
            },
            barWidth: '50%'
        }]
    });
}

// 页面加载
document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    loadStats();
});
