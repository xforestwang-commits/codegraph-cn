"""命令行工具."""

import argparse
import sys
from pathlib import Path

from codegraph.parser import parse_codebase, CodeEntity
from codegraph.graph import KnowledgeGraph, build_graph_from_codebase


def cmd_analyze(args: argparse.Namespace) -> int:
    """分析代码库命令."""
    root_path = Path(args.path).resolve()

    if not root_path.exists():
        print(f"错误: 路径不存在: {root_path}", file=sys.stderr)
        return 1

    print(f"🔍 正在分析: {root_path}")

    # 解析代码库
    entities = parse_codebase(root_path)

    if not entities:
        print("未找到可解析的代码文件")
        return 0

    # 按类型统计
    stats = {
        "function": 0,
        "class": 0,
        "struct": 0,
        "interface": 0,
        "module": 0,
    }
    for e in entities:
        stats[e.type] = stats.get(e.type, 0) + 1

    print(f"\n📊 分析结果:")
    print(f"   总实体数: {len(entities)}")
    for etype, count in stats.items():
        if count > 0:
            print(f"   - {etype}: {count}")

    # 构建图谱
    graph = build_graph_from_codebase(root_path)

    # 保存图谱
    output_path = root_path / ".codegraph-cn" / "knowledge-graph.json"
    output_path.parent.mkdir(exist_ok=True)
    graph.export_json(output_path)

    print(f"\n💾 知识图谱已保存: {output_path}")
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    """显示统计信息命令."""
    root_path = Path(args.path).resolve()

    graph_file = root_path / ".codegraph-cn" / "knowledge-graph.json"
    if not graph_file.exists():
        print("错误: 未找到知识图谱文件，请先运行 analyze 命令", file=sys.stderr)
        return 1

    graph = KnowledgeGraph.from_json(graph_file)
    stats = graph.get_stats()

    print(f"\n📊 代码库统计:")
    print(f"   总节点数: {stats['total_nodes']}")
    print(f"   总边数: {stats['total_edges']}")

    if stats["by_type"]:
        print(f"\n   按类型:")
        for etype, count in stats["by_type"].items():
            if count > 0:
                print(f"   - {etype}: {count}")

    if stats["by_language"]:
        print(f"\n   按语言:")
        for lang, count in stats["by_language"].items():
            print(f"   - {lang}: {count}")

    return 0


def cmd_search(args: argparse.Namespace) -> int:
    """搜索代码实体."""
    root_path = Path(args.path).resolve()

    graph_file = root_path / ".codegraph-cn" / "knowledge-graph.json"
    if not graph_file.exists():
        print("错误: 未找到知识图谱文件，请先运行 analyze 命令", file=sys.stderr)
        return 1

    graph = KnowledgeGraph.from_json(graph_file)
    results = graph.search(args.query)

    if not results:
        print(f"未找到匹配 '{args.query}' 的实体")
        return 0

    print(f"🔍 找到 {len(results)} 个匹配结果:\n")
    for node in results[:10]:  # 限制显示数量
        print(f"  [{node.type}] {node.name}")
        print(f"     文件: {node.file_path}:{node.line}")
        if node.description:
            print(f"     描述: {node.description[:100]}...")
        print()

    return 0


def cmd_layers(args: argparse.Namespace) -> int:
    """显示架构层级."""
    root_path = Path(args.path).resolve()

    graph_file = root_path / ".codegraph-cn" / "knowledge-graph.json"
    if not graph_file.exists():
        print("错误: 未找到知识图谱文件，请先运行 analyze 命令", file=sys.stderr)
        return 1

    graph = KnowledgeGraph.from_json(graph_file)
    layers = graph.get_architecture_layers()

    print(f"\n🏗️ 架构层级:\n")
    for layer, nodes in layers.items():
        print(f"  【{layer.upper()}】 ({len(nodes)} 个实体)")
        for node in nodes[:5]:  # 每层显示前5个
            print(f"    - {node.name} ({node.type})")
        if len(nodes) > 5:
            print(f"    ... 还有 {len(nodes) - 5} 个")
        print()

    return 0


def cmd_visualize(args: argparse.Namespace) -> int:
    """启动可视化服务."""
    print("🚧 可视化功能开发中...")
    print("   预计支持: Web Dashboard 展示代码知识图谱")
    print("   可以先用 cmd_stats 查看分析结果")
    return 0


def main() -> int:
    """主入口."""
    parser = argparse.ArgumentParser(
        prog="codograph",
        description="CodeGraph-CN: 基于 MiMo 的中文代码知识图谱工具",
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # analyze 命令
    parser_analyze = subparsers.add_parser("analyze", help="分析代码库")
    parser_analyze.add_argument("path", nargs="?", default=".", help="代码库路径 (默认: 当前目录)")
    parser_analyze.set_defaults(func=cmd_analyze)

    # stats 命令
    parser_stats = subparsers.add_parser("stats", help="显示统计信息")
    parser_stats.add_argument("path", nargs="?", default=".", help="代码库路径")
    parser_stats.set_defaults(func=cmd_stats)

    # search 命令
    parser_search = subparsers.add_parser("search", help="搜索代码实体")
    parser_search.add_argument("path", nargs="?", default=".", help="代码库路径")
    parser_search.add_argument("query", help="搜索关键词")
    parser_search.set_defaults(func=cmd_search)

    # layers 命令
    parser_layers = subparsers.add_parser("layers", help="显示架构层级")
    parser_layers.add_argument("path", nargs="?", default=".", help="代码库路径")
    parser_layers.set_defaults(func=cmd_layers)

    # visualize 命令
    parser_visualize = subparsers.add_parser("visualize", help="启动可视化")
    parser_visualize.add_argument("path", nargs="?", default=".", help="代码库路径")
    parser_visualize.add_argument("--port", type=int, default=8080, help="端口号")
    parser_visualize.set_defaults(func=cmd_visualize)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())