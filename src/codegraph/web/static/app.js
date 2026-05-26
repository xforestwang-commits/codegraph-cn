// CodeGraph-CN Dashboard - 前端交互逻辑

const API_BASE = '/api';

// 初始化
document.addEventListener('DOMContentLoaded', async () => {
    await loadStats();
    await loadGraph();
    await loadLayers();
});

// 加载统计信息
async function loadStats() {
    try {
        const res = await fetch(`${API_BASE}/stats`);
        const data = await res.json();

        document.getElementById('stat-nodes').textContent = data.total_nodes;
        document.getElementById('stat-edges').textContent = data.total_edges;
        document.getElementById('stat-functions').textContent = data.by_type?.functions || 0;
        document.getElementById('stat-classes').textContent = (data.by_type?.classes || 0);
    } catch (e) {
        console.error('加载统计失败:', e);
    }
}

// 加载图谱数据
async function loadGraph() {
    try {
        const res = await fetch(`${API_BASE}/graph`);
        const data = await res.json();
        renderGraph(data);
    } catch (e) {
        console.error('加载图谱失败:', e);
    }
}

// 加载架构层级
async function loadLayers() {
    try {
        const res = await fetch(`${API_BASE}/layers`);
        const data = await res.json();
        renderLayers(data);
    } catch (e) {
        console.error('加载层级失败:', e);
    }
}

// D3.js 渲染图谱
function renderGraph(data) {
    const container = document.getElementById('graph-svg');
    const width = container.clientWidth;
    const height = 500;

    // 清空
    container.innerHTML = '';

    // 创建 SVG
    const svg = d3.select('#graph-svg')
        .append('svg')
        .attr('width', width)
        .attr('height', height);

    // 缩放
    const zoom = d3.zoom()
        .scaleExtent([0.1, 4])
        .on('zoom', (event) => {
            g.attr('transform', event.transform);
        });

    svg.call(zoom);

    const g = svg.append('g');

    // 力导向布局
    const simulation = d3.forceSimulation(data.nodes)
        .force('link', d3.forceLink(data.links).id(d => d.id).distance(50))
        .force('charge', d3.forceManyBody().strength(-100))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(30));

    // 绘制边
    const links = g.append('g')
        .selectAll('line')
        .data(data.links)
        .enter()
        .append('line')
        .attr('class', d => `link ${d.relation}`)
        .attr('stroke-width', 1);

    // 绘制节点
    const nodes = g.append('g')
        .selectAll('g')
        .data(data.nodes)
        .enter()
        .append('g')
        .attr('class', d => `node ${d.type}`)
        .call(d3.drag()
            .on('start', dragStart)
            .on('drag', drag)
            .on('end', dragEnd));

    // 节点圆圈
    nodes.append('circle')
        .attr('r', 10);

    // 节点标签
    nodes.append('text')
        .text(d => d.name)
        .attr('x', 15)
        .attr('y', 5);

    // 点击节点显示详情
    nodes.on('click', async (event, d) => {
        event.stopPropagation();
        await showNodeDetail(d.id);
    });

    // 点击空白关闭详情
    svg.on('click', () => {
        document.getElementById('node-detail').classList.remove('active');
    });

    // 更新位置
    simulation.on('tick', () => {
        links
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);

        nodes.attr('transform', d => `translate(${d.x},${d.y})`);
    });

    // 拖拽函数
    function dragStart(event) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        event.subject.fx = event.subject.x;
        event.subject.fy = event.subject.y;
    }

    function drag(event) {
        event.subject.fx = event.x;
        event.subject.fy = event.y;
    }

    function dragEnd(event) {
        if (!event.active) simulation.alphaTarget(0);
        event.subject.fx = null;
        event.subject.fy = null;
    }

    // 缩放按钮
    document.getElementById('zoom-in').onclick = () => {
        svg.transition().call(zoom.scaleBy, 1.5);
    };

    document.getElementById('zoom-out').onclick = () => {
        svg.transition().call(zoom.scaleBy, 0.67);
    };

    document.getElementById('reset').onclick = () => {
        svg.transition().call(zoom.transform, d3.zoomIdentity);
    };

    // 类型过滤
    document.getElementById('filter-type').onchange = (e) => {
        const type = e.target.value;
        nodes.style('opacity', d => type === 'all' || d.type === type ? 1 : 0.1);
        links.style('opacity', d => {
            const source = data.nodes.find(n => n.id === d.source.id);
            const target = data.nodes.find(n => n.id === d.target.id);
            if (type === 'all') return 0.6;
            return (source?.type === type || target?.type === type) ? 0.6 : 0.1;
        });
    };
}

// 显示节点详情
async function showNodeDetail(nodeId) {
    try {
        const res = await fetch(`${API_BASE}/node/${encodeURIComponent(nodeId)}`);
        const data = await res.json();

        const detail = document.getElementById('node-detail');
        detail.classList.add('active');
        detail.innerHTML = `
            <h3>${data.name}</h3>
            <p><span class="value">${data.type}</span></p>
            <p>文件: <span class="value">${data.file}:${data.line}</span></p>
            <p>语言: <span class="value">${data.language}</span></p>
            ${data.description ? `<p>描述: <span class="value">${data.description}</span></p>` : ''}
            ${data.neighbors?.length ? `
                <p>关联节点:</p>
                <div class="layer-items">
                    ${data.neighbors.map(n => `<span class="layer-item" onclick="highlightNode('${n.id}')">${n.name}</span>`).join('')}
                </div>
            ` : ''}
        `;
    } catch (e) {
        console.error('获取节点详情失败:', e);
    }
}

// 渲染架构层级
function renderLayers(data) {
    const container = document.getElementById('layers-content');
    container.innerHTML = '';

    const colors = {
        api: '#e94560',
        service: '#4ecca3',
        data: '#f5a623',
        util: '#0f3460',
        other: '#888',
    };

    for (const [layer, items] of Object.entries(data)) {
        const group = document.createElement('div');
        group.className = 'layer-group';
        group.innerHTML = `
            <div class="layer-title" style="color: ${colors[layer] || '#888'}">${layer.toUpperCase()} (${items.length})</div>
            <div class="layer-items">
                ${items.map(item => `<span class="layer-item" onclick="highlightNode('${item.id}')">${item.name}</span>`).join('')}
            </div>
        `;
        container.appendChild(group);
    }
}

// 搜索功能
document.getElementById('search-btn').onclick = async () => {
    const query = document.getElementById('search-input').value.trim();
    if (!query) return;

    try {
        const res = await fetch(`${API_BASE}/search?q=${encodeURIComponent(query)}`);
        const data = await res.json();

        const results = document.getElementById('search-results');
        results.classList.add('active');

        if (data.results.length === 0) {
            results.innerHTML = '<p style="color: #888">未找到匹配结果</p>';
        } else {
            results.innerHTML = data.results.map(r => `
                <div class="search-result-item" onclick="highlightNode('${r.id}')">
                    <strong>${r.name}</strong> <span style="color: #888">[${r.type}]</span>
                    <br><small style="color: #888">${r.file}:${r.line}</small>
                </div>
            `).join('');
        }
    } catch (e) {
        console.error('搜索失败:', e);
    }
};

// 高亮节点（TODO: 实现图谱高亮）
function highlightNode(nodeId) {
    console.log('高亮节点:', nodeId);
    // TODO: 在图谱中高亮指定节点
    showNodeDetail(nodeId);
}