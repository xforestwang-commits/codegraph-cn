# CodeGraph-CN

基于 MiMo 大模型的中文代码知识图谱工具，帮助中文开发者快速理解大型项目的架构和代码逻辑。

## 核心能力

- 代码解析：提取函数、类、依赖、注释
- 中文语义理解：使用 MiMo V2.5 生成中文代码解释
- 知识图谱：可视化展示代码结构和关系
- 自然语言查询：用中文问代码问题

## 技术栈

- Python 3.10+
- MiMo API (V2.5)
- 网络可视化：D3.js / PyVis

## 安装

```bash
cd codegraph-cn
pip install -e .
```

## 使用

```bash
# 分析代码目录
codograph analyze ./src

# 启动可视化
codograph visualize

# 查询代码
codograph query "登录流程怎么实现的"
```

## 项目结构

```
codegraph-cn/
├── src/
│   ├── parser/        # 代码解析器
│   ├── mimo/         # MiMo API 调用
│   ├── graph/        # 知识图谱构建
│   ├── cli/         # 命令行工具
│   └── web/         # 可视化界面
├── tests/
└── docs/
```

## License

MIT