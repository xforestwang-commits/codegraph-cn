"""代码解析器模块 - 支持 Python/JavaScript/Go."""

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator
import re


@dataclass
class CodeEntity:
    """代码实体：函数、类、模块."""
    name: str
    type: str  # function, class, module
    file_path: str
    start_line: int
    end_line: int
    docstring: str = ""
    language: str = ""
    children: list["CodeEntity"] = None

    def __post_init__(self):
        if self.children is None:
            self.children = []


class CodeParser:
    """代码解析器基类."""

    LANGUAGE_EXTENSIONS = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".go": "go",
        ".java": "java",
    }

    def __init__(self, root_path: str | Path):
        self.root_path = Path(root_path)

    def scan(self, extensions: list[str] | None = None) -> Iterator[Path]:
        """扫描目录下的代码文件."""
        if extensions is None:
            extensions = list(self.LANGUAGE_EXTENSIONS.keys())

        for ext in extensions:
            yield from self.root_path.rglob(f"*{ext}")

    def parse_file(self, file_path: Path) -> list[CodeEntity]:
        """解析单个文件，返回代码实体列表."""
        raise NotImplementedError


class PythonParser(CodeParser):
    """Python 代码解析器."""

    def parse_file(self, file_path: Path) -> list[CodeEntity]:
        """解析 Python 文件，提取函数和类."""
        entities = []
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        # 匹配函数定义
        func_pattern = re.compile(r"^(\s*)def (\w+)\(.*?\):")
        # 匹配类定义
        class_pattern = re.compile(r"^(\s*)class (\w+).*?:")

        current_indent = 0
        stack = []

        for i, line in enumerate(lines, 1):
            # 跳过注释和空行
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            # 计算缩进
            indent = len(line) - len(line.lstrip())

            # 匹配类
            class_match = class_pattern.match(line)
            if class_match:
                cls_name = class_match.group(2)
                entity = CodeEntity(
                    name=cls_name,
                    type="class",
                    file_path=str(file_path),
                    start_line=i,
                    end_line=i,
                    language="python",
                )
                # 处理缩进层级
                while stack and stack[-1][1] >= indent:
                    stack.pop()
                if stack:
                    stack[-1][0].children.append(entity)
                else:
                    entities.append(entity)
                stack.append((entity, indent))
                continue

            # 匹配函数
            func_match = func_pattern.match(line)
            if func_match:
                func_name = func_match.group(2)
                entity = CodeEntity(
                    name=func_name,
                    type="function",
                    file_path=str(file_path),
                    start_line=i,
                    end_line=i,
                    language="python",
                )
                # 处理缩进层级
                while stack and stack[-1][1] >= indent:
                    stack.pop()
                if stack:
                    stack[-1][0].children.append(entity)
                else:
                    entities.append(entity)
                stack.append((entity, indent))

        return entities


class JavaScriptParser(CodeParser):
    """JavaScript 代码解析器."""

    def parse_file(self, file_path: Path) -> list[CodeEntity]:
        """解析 JavaScript/TypeScript 文件."""
        entities = []
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        # 匹配函数：function name() {} 或 const name = () => {}
        func_pattern = re.compile(
            r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(|"
            r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>|"
            r"(?:export\s+)?(?:async\s+)?(\w+)\s*\([^)]*\)\s*\{"
        )

        # 匹配类
        class_pattern = re.compile(
            r"(?:export\s+)?class\s+(\w+)(?:\s+extends\s+\w+)?"
        )

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("//"):
                continue

            # 匹配类
            class_match = class_pattern.search(line)
            if class_match:
                entities.append(CodeEntity(
                    name=class_match.group(1),
                    type="class",
                    file_path=str(file_path),
                    start_line=i,
                    end_line=i,
                    language="javascript",
                ))

            # 匹配函数
            func_match = func_pattern.search(line)
            if func_match:
                name = func_match.group(1) or func_match.group(2) or func_match.group(3)
                if name:
                    entities.append(CodeEntity(
                        name=name,
                        type="function",
                        file_path=str(file_path),
                        start_line=i,
                        end_line=i,
                        language="javascript",
                    ))

        return entities


class GoParser(CodeParser):
    """Go 代码解析器."""

    def parse_file(self, file_path: Path) -> list[CodeEntity]:
        """解析 Go 文件."""
        entities = []
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        # 匹配函数：func Name() {
        func_pattern = re.compile(r"^func\s+(\w+)\s*\(")
        # 匹配结构体
        struct_pattern = re.compile(r"^type\s+(\w+)\s+struct")
        # 匹配接口
        interface_pattern = re.compile(r"^type\s+(\w+)\s+interface")

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("//"):
                continue

            # 匹配结构体
            struct_match = struct_pattern.match(stripped)
            if struct_match:
                entities.append(CodeEntity(
                    name=struct_match.group(1),
                    type="struct",
                    file_path=str(file_path),
                    start_line=i,
                    end_line=i,
                    language="go",
                ))
                continue

            # 匹配接口
            interface_match = interface_pattern.match(stripped)
            if interface_match:
                entities.append(CodeEntity(
                    name=interface_match.group(1),
                    type="interface",
                    file_path=str(file_path),
                    start_line=i,
                    end_line=i,
                    language="go",
                ))
                continue

            # 匹配函数
            func_match = func_pattern.match(stripped)
            if func_match:
                entities.append(CodeEntity(
                    name=func_match.group(1),
                    type="function",
                    file_path=str(file_path),
                    start_line=i,
                    end_line=i,
                    language="go",
                ))

        return entities


def get_parser(file_path: Path) -> CodeParser | None:
    """根据文件扩展名获取对应的解析器."""
    ext = file_path.suffix.lower()
    lang = CodeParser.LANGUAGE_EXTENSIONS.get(ext)

    if lang == "python":
        return PythonParser(file_path.parent)
    elif lang in ("javascript", "typescript"):
        return JavaScriptParser(file_path.parent)
    elif lang == "go":
        return GoParser(file_path.parent)

    return None


def parse_codebase(root_path: str | Path) -> list[CodeEntity]:
    """解析整个代码库."""
    root = Path(root_path)
    all_entities = []

    parser_config = {
        ".py": PythonParser,
        ".js": JavaScriptParser,
        ".ts": JavaScriptParser,
        ".go": GoParser,
    }

    for ext, parser_cls in parser_config.items():
        parser = parser_cls(root)
        for file_path in parser.scan([ext]):
            p = parser_cls(file_path.parent)
            entities = p.parse_file(file_path)
            all_entities.extend(entities)

    return all_entities
