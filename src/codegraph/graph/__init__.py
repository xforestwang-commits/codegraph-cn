"""知识图谱构建模块."""

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterator
import networkx as nx

from codegraph.parser import CodeEntity, parse_codebase


@dataclass
class GraphNode:
    """图谱节点."""
    id: str
    name: str
    type: str  # function, class, struct, module
    file_path: str
    line: int
    language: str
    description: str = ""
    children: list[str] = None  # 子节点 ID 列表

    def __post_init__(self):
        if self.children is None:
            self.children = []


@dataclass
class GraphEdge:
    """图谱边（关系）."""
    source: str  # 源节点 ID
    target: str  # 目标节点 ID
    relation: str  # calls, contains, imports, extends


class KnowledgeGraph:
    """代码知识图谱.

    使用 NetworkX 构建双向关系图。
    """

    def __init__(self, name: str = "codebase"):
        self.name = name
        self.graph = nx.DiGraph()
        self.nodes: dict[str, GraphNode] = {}
        self.metadata: dict = {
            "version": "0.1.0",
            "tool": "CodeGraph-CN",
        }

    def add_node(self, entity: CodeEntity, description: str = "") -> str:
        """添加节点到图谱.

        Args:
            entity: 代码实体
            description: 实体描述（由 MiMo 生成）

        Returns:
            节点 ID
        """
        node_id = self._make_node_id(entity)
        node = GraphNode(
            id=node_id,
            name=entity.name,
            type=entity.type,
            file_path=entity.file_path,
            line=entity.start_line,
            language=entity.language,
            description=description,
        )
        self.nodes[node_id] = node
        self.graph.add_node(node_id, **asdict(node))
        return node_id

    def add_edge(self, source_id: str, target_id: str, relation: str = "contains") -> None:
        """添加边（关系）."""
        if source_id in self.nodes and target_id in self.nodes:
            self.graph.add_edge(source_id, target_id, relation=relation)

    def link_parent_child(self, parent_id: str, child_id: str) -> None:
        """链接父子节点."""
        self.add_edge(parent_id, child_id, "contains")

        # 更新父节点的 children 列表
        if child_id not in self.nodes[parent_id].children:
            self.nodes[parent_id].children.append(child_id)

    def _make_node_id(self, entity: CodeEntity) -> str:
        """生成唯一节点 ID."""
        return f"{entity.file_path}:{entity.name}:{entity.type}"

    def get_neighbors(self, node_id: str, depth: int = 1) -> list[GraphNode]:
        """获取邻居节点."""
        if node_id not in self.graph:
            return []

        neighbors = []
        for neighbor in self.graph.neighbors(node_id):
            if neighbor in self.nodes:
                neighbors.append(self.nodes[neighbor])

        return neighbors

    def search(self, query: str) -> list[GraphNode]:
        """搜索节点."""
        results = []
        query_lower = query.lower()

        for node in self.nodes.values():
            if query_lower in node.name.lower() or query_lower in node.description.lower():
                results.append(node)

        return results

    def get_architecture_layers(self) -> dict[str, list[GraphNode]]:
        """按架构层级分组节点.

        简单实现：按文件路径的目录层级分组。
        后续可以用 MiMo 分析更准确的架构分层。
        """
        layers: dict[str, list[GraphNode]] = {
            "api": [],
            "service": [],
            "data": [],
            "util": [],
            "other": [],
        }

        for node in self.nodes.values():
            path = node.file_path.lower()

            if "api" in path or "router" in path or "controller" in path:
                layers["api"].append(node)
            elif "service" in path or "business" in path:
                layers["service"].append(node)
            elif "db" in path or "data" in path or "model" in path or "repo" in path:
                layers["data"].append(node)
            elif "util" in path or "helper" in path or "common" in path:
                layers["util"].append(node)
            else:
                layers["other"].append(node)

        return {k: v for k, v in layers.items() if v}

    def export_json(self, file_path: str | Path) -> None:
        """导出图谱为 JSON."""
        data = {
            "metadata": self.metadata,
            "name": self.name,
            "nodes": {k: asdict(v) for k, v in self.nodes.items()},
            "edges": [
                {"source": u, "target": v, "relation": d.get("relation", "unknown")}
                for u, v, d in self.graph.edges(data=True)
            ],
        }

        Path(file_path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def from_json(cls, file_path: str | Path) -> "KnowledgeGraph":
        """从 JSON 加载图谱."""
        data = json.loads(Path(file_path).read_text(encoding="utf-8"))

        graph = cls(name=data.get("name", "codebase"))
        graph.metadata = data.get("metadata", {})
        graph.nodes = {k: GraphNode(**v) for k, v in data.get("nodes", {}).items()}

        for edge in data.get("edges", []):
            graph.graph.add_edge(edge["source"], edge["target"], relation=edge.get("relation", "unknown"))

        return graph

    def get_stats(self) -> dict:
        """获取图谱统计信息."""
        return {
            "total_nodes": len(self.nodes),
            "total_edges": self.graph.number_of_edges(),
            "by_type": {
                "functions": sum(1 for n in self.nodes.values() if n.type == "function"),
                "classes": sum(1 for n in self.nodes.values() if n.type in ("class", "struct")),
                "modules": sum(1 for n in self.nodes.values() if n.type == "module"),
            },
            "by_language": dict(
                zip(*[
                    (lang, sum(1 for n in self.nodes.values() if n.language == lang))
                    for lang in set(n.language for n in self.nodes.values())
                ])
            ) if self.nodes else {},
        }


def build_graph_from_codebase(
    root_path: str | Path,
    name: str = "codebase",
) -> KnowledgeGraph:
    """从代码库构建知识图谱.

    Args:
        root_path: 代码库根目录
        name: 图谱名称

    Returns:
        知识图谱对象
    """
    graph = KnowledgeGraph(name=name)

    # 解析代码库
    entities = parse_codebase(root_path)

    # 添加节点
    for entity in entities:
        graph.add_node(entity)

    # 建立父子关系
    for entity in entities:
        node_id = graph._make_node_id(entity)
        for child in entity.children:
            child_id = graph._make_node_id(child)
            if child_id in graph.nodes:
                graph.link_parent_child(node_id, child_id)

    return graph