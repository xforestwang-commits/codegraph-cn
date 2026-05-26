"""Web Dashboard - 可视化知识图谱."""

import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from ..graph import KnowledgeGraph


app = FastAPI(
    title="CodeGraph-CN Dashboard",
    description="中文代码知识图谱可视化",
    version="0.1.0",
)

# 静态文件和模板
BASE_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# 配置 Jinja2 模板（正确方式）
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# 全局图谱实例
_graph: Optional[KnowledgeGraph] = None
_graph_path: Optional[Path] = None


def load_graph(graph_path: str | Path) -> KnowledgeGraph:
    """加载知识图谱."""
    global _graph, _graph_path
    _graph_path = Path(graph_path)
    _graph = KnowledgeGraph.from_json(_graph_path)
    return _graph


def get_graph() -> KnowledgeGraph:
    """获取当前图谱."""
    if _graph is None:
        raise HTTPException(status_code=404, detail="图谱未加载，请先调用 /api/load")
    return _graph


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """主页."""
    # 直接读取 HTML 文件，绕过 Jinja2 缓存问题
    html_file = BASE_DIR / "templates" / "index.html"
    if not html_file.exists():
        raise HTTPException(status_code=404, detail="模板文件不存在")
    with open(html_file, "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)


@app.get("/api/stats")
async def api_stats():
    """获取图谱统计信息."""
    graph = get_graph()
    return graph.get_stats()


@app.get("/api/nodes")
async def api_nodes():
    """获取所有节点."""
    graph = get_graph()
    nodes = []
    for node in graph.nodes.values():
        nodes.append({
            "id": node.id,
            "name": node.name,
            "type": node.type,
            "file": node.file_path,
            "line": node.line,
            "language": node.language,
            "description": node.description,
        })
    return {"nodes": nodes}


@app.get("/api/edges")
async def api_edges():
    """获取所有边."""
    graph = get_graph()
    edges = []
    for u, v, data in graph.graph.edges(data=True):
        edges.append({
            "source": u,
            "target": v,
            "relation": data.get("relation", "unknown"),
        })
    return {"edges": edges}


@app.get("/api/graph")
async def api_graph():
    """获取完整图谱数据（用于 D3.js 可视化）."""
    graph = get_graph()

    # D3.js 格式
    nodes = []
    for node in graph.nodes.values():
        nodes.append({
            "id": node.id,
            "name": node.name,
            "type": node.type,
            "language": node.language,
            "file": node.file_path,
            "line": node.line,
        })

    links = []
    for u, v, data in graph.graph.edges(data=True):
        links.append({
            "source": u,
            "target": v,
            "relation": data.get("relation", "unknown"),
        })

    return {"nodes": nodes, "links": links}


@app.get("/api/search")
async def api_search(q: str):
    """搜索节点."""
    graph = get_graph()
    results = graph.search(q)
    return {
        "query": q,
        "results": [
            {
                "id": r.id,
                "name": r.name,
                "type": r.type,
                "file": r.file_path,
                "line": r.line,
            }
            for r in results
        ],
    }


@app.get("/api/layers")
async def api_layers():
    """获取架构层级."""
    graph = get_graph()
    layers = graph.get_architecture_layers()
    return {
        layer: [
            {"id": n.id, "name": n.name, "type": n.type}
            for n in nodes
        ]
        for layer, nodes in layers.items()
    }


@app.get("/api/node/{node_id}")
async def api_node_detail(node_id: str):
    """获取节点详情."""
    graph = get_graph()
    if node_id not in graph.nodes:
        raise HTTPException(status_code=404, detail="节点不存在")

    node = graph.nodes[node_id]
    neighbors = graph.get_neighbors(node_id)

    return {
        "id": node.id,
        "name": node.name,
        "type": node.type,
        "file": node.file_path,
        "line": node.line,
        "language": node.language,
        "description": node.description,
        "children": node.children,
        "neighbors": [
            {"id": n.id, "name": n.name, "type": n.type}
            for n in neighbors
        ],
    }


@app.post("/api/load")
async def api_load(path: str):
    """加载图谱文件."""
    try:
        graph = load_graph(path)
        return {"status": "ok", "stats": graph.get_stats()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def run_dashboard(
    graph_path: str | Path,
    host: str = "127.0.0.1",
    port: int = 8080,
):
    """启动 Dashboard 服务.

    Args:
        graph_path: 知识图谱 JSON 文件路径
        host: 主机地址
        port: 端口号
    """
    load_graph(graph_path)
    print(f"🚀 CodeGraph-CN Dashboard 启动中...")
    print(f"   图谱: {graph_path}")
    print(f"   地址: http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)