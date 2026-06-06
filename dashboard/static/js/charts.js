/**
 * AI Analytics Agent — Chart Configurations (Plotly.js)
 */

const COLORS = {
    green: '#10b981',
    yellow: '#f59e0b',
    red: '#ef4444',
    blue: '#3b82f6',
    purple: '#8b5cf6',
    cyan: '#06b6d4',
    palette: ['#3b82f6', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#ec4899', '#f97316'],
};

const LAYOUT_DEFAULTS = {
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: { family: 'Inter, sans-serif', color: '#94a3b8', size: 12 },
    margin: { l: 50, r: 20, t: 40, b: 40 },
    xaxis: { gridcolor: 'rgba(255,255,255,0.05)', zerolinecolor: 'rgba(255,255,255,0.1)' },
    yaxis: { gridcolor: 'rgba(255,255,255,0.05)', zerolinecolor: 'rgba(255,255,255,0.1)' },
    showlegend: true,
    legend: { font: { size: 11 }, bgcolor: 'rgba(0,0,0,0)' },
};

const CONFIG = { responsive: true, displayModeBar: false };

function statusColor(status) {
    return status === 'green' ? COLORS.green : status === 'yellow' ? COLORS.yellow : COLORS.red;
}

function renderProfitabilityBar(elementId, projects) {
    if (!document.getElementById(elementId)) return;
    const sorted = [...projects].sort((a, b) => a.margin - b.margin);
    const trace = {
        x: sorted.map(p => p.margin),
        y: sorted.map(p => p.project_name),
        type: 'bar',
        orientation: 'h',
        marker: { color: sorted.map(p => statusColor(p.status)), borderRadius: 4 },
        text: sorted.map(p => `${p.margin.toFixed(1)}%`),
        textposition: 'outside',
        textfont: { size: 11, color: '#94a3b8' },
    };
    const layout = {
        ...LAYOUT_DEFAULTS,
        title: { text: 'Маржинальность проектов', font: { size: 16, color: '#f1f5f9' } },
        xaxis: { ...LAYOUT_DEFAULTS.xaxis, title: 'Маржа, %' },
        yaxis: { ...LAYOUT_DEFAULTS.yaxis, automargin: true },
        height: Math.max(350, sorted.length * 40),
        shapes: [{ type: 'line', x0: 0, x1: 0, y0: -0.5, y1: sorted.length - 0.5, line: { color: 'rgba(255,255,255,0.2)', width: 1, dash: 'dash' } }],
    };
    Plotly.newPlot(elementId, [trace], layout, CONFIG);
}

function renderStackComparison(elementId, stacks) {
    if (!document.getElementById(elementId)) return;
    const trace1 = {
        x: stacks.map(s => s.stack),
        y: stacks.map(s => s.total_revenue),
        name: 'Доход',
        type: 'bar',
        marker: { color: COLORS.blue, borderRadius: 4 },
    };
    const trace2 = {
        x: stacks.map(s => s.stack),
        y: stacks.map(s => s.total_costs),
        name: 'Расходы',
        type: 'bar',
        marker: { color: COLORS.red, opacity: 0.7, borderRadius: 4 },
    };
    const layout = {
        ...LAYOUT_DEFAULTS,
        title: { text: 'Доход vs Расходы по стекам', font: { size: 16, color: '#f1f5f9' } },
        barmode: 'group',
        height: 400,
    };
    Plotly.newPlot(elementId, [trace1, trace2], layout, CONFIG);
}

function renderProfitPie(elementId, projects) {
    if (!document.getElementById(elementId)) return;
    const profitable = projects.filter(p => p.profit > 0);
    const lossy = projects.filter(p => p.profit <= 0);
    const trace = {
        labels: ['Прибыльные', 'Убыточные'],
        values: [profitable.length, lossy.length],
        type: 'pie',
        hole: 0.55,
        marker: { colors: [COLORS.green, COLORS.red] },
        textinfo: 'label+value',
        textfont: { size: 13, color: '#f1f5f9' },
    };
    const layout = {
        ...LAYOUT_DEFAULTS,
        title: { text: 'Соотношение проектов', font: { size: 16, color: '#f1f5f9' } },
        height: 350,
    };
    Plotly.newPlot(elementId, [trace], layout, CONFIG);
}

function renderBurnRate(elementId, projects) {
    if (!document.getElementById(elementId)) return;
    const sorted = [...projects].sort((a, b) => b.burn_rate - a.burn_rate).slice(0, 10);
    const trace = {
        x: sorted.map(p => p.project_name),
        y: sorted.map(p => p.burn_rate),
        type: 'bar',
        marker: {
            color: sorted.map((_, i) => COLORS.palette[i % COLORS.palette.length]),
            borderRadius: 4,
        },
        text: sorted.map(p => `$${(p.burn_rate / 1000).toFixed(1)}k`),
        textposition: 'outside',
        textfont: { size: 11, color: '#94a3b8' },
    };
    const layout = {
        ...LAYOUT_DEFAULTS,
        title: { text: 'Burn Rate по проектам ($/мес)', font: { size: 16, color: '#f1f5f9' } },
        height: 400,
    };
    Plotly.newPlot(elementId, [trace], layout, CONFIG);
}

function renderOvertimeChart(elementId, taskTypes) {
    if (!document.getElementById(elementId)) return;
    const trace = {
        x: taskTypes.map(t => t.task_type),
        y: taskTypes.map(t => t.overtime_ratio),
        type: 'bar',
        marker: { color: taskTypes.map(t => statusColor(t.status)), borderRadius: 4 },
        text: taskTypes.map(t => `${t.overtime_ratio.toFixed(2)}x`),
        textposition: 'outside',
        textfont: { size: 11, color: '#94a3b8' },
    };
    const layout = {
        ...LAYOUT_DEFAULTS,
        title: { text: 'Перерасход часов по типам задач', font: { size: 16, color: '#f1f5f9' } },
        shapes: [{ type: 'line', x0: -0.5, x1: taskTypes.length - 0.5, y0: 1, y1: 1, line: { color: 'rgba(255,255,255,0.2)', width: 1, dash: 'dash' } }],
        height: 380,
    };
    Plotly.newPlot(elementId, [trace], layout, CONFIG);
}
