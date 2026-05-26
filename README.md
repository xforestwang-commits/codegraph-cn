# CodeGraph-CN

基于 MiMo 大模型的中文代码知识图谱工具，帮助中文开发者快速理解大型项目的架构和代码逻辑。

## 核心能力

- **代码解析**：提取函数、类、依赖、注释（支持 Python/JavaScript/Go）
- **中文语义理解**：使用 MiMo V2.5 生成中文代码解释
- **知识图谱**：可视化展示代码结构和关系
- **自然语言查询**：用中文问代码问题
- **Web Dashboard**：交互式可视化界面

## 技术栈

- Python 3.10+
- MiMo API (V2.5)
- NetworkX（知识图谱）
- FastAPI + D3.js（可视化）

## 安装

```bash
cd codegraph-cn
pip install -e .
```

## 使用

### 1. 分析代码库

```bash
# 分析当前目录
codograph analyze

# 分析指定目录
codograph analyze ./src
```

### 2. 查看统计信息

```bash
codograph stats ./src
```

### 3. 搜索代码实体

```bash
codograph search ./src "login"
```

### 4. 显示架构层级

```bash
codograph layers ./src
```

### 5. 启动可视化 Dashboard

```bash
# 默认端口 8080
codograph visualize ./src

# 自定义端口
codograph visualize ./src --port 3000
```

打开浏览器访问 http://127.0.0.1:8080

## Web Dashboard 功能

- 📊 **统计面板**：显示节点、边、函数、类数量
- 🔍 **搜索功能**：按名称或语义搜索代码实体
- 🌐 **图谱可视化**：D3.js 力导向图，支持缩放、拖拽、过滤
- 🏗️ **架构层级**：按 API/Service/Data/Util 分组展示
- 📝 **节点详情**：点击节点查看详细信息

## 项目结构

```
codegraph-cn/
├── src/
│   └── codegraph/
│       ├── parser/      # 代码解析器
│       ├── mimo/        # MiMo API 调用
│       ├── graph/       # 知识图谱构建
│       ├── cli/         # 命令行工具
│       └── web/         # Web Dashboard
│           ├── templates/   # HTML 模板
│           └── static/      # CSS/JS
├── tests/
└── docs/
```

## MiMo API 集成（待 Token）

项目已预留 MiMo API 客户端模块。获取 MiMo Token 后：

```python
from codegraph.mimo import MiMoClient, explain_code_with_mimo

client = MiMoClient(api_key="your-mimo-token")
explanation = explain_code_with_mimo(client, code_snippet, language="python")
```

## License

MIT