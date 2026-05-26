"""简单的解析测试."""

from pathlib import Path
from codegraph.parser import PythonParser, JavaScriptParser, GoParser, parse_codebase

# 测试代码
test_code = """
def hello():
    '''Say hello.'''
    print("Hello, World!")

class User:
    def __init__(self, name):
        self.name = name

    def greet(self):
        return f"Hello, {self.name}!"

def main():
    user = User("CodeGraph")
    user.greet()
"""

# 创建测试文件
test_dir = Path(__file__).parent / "test_data"
test_dir.mkdir(exist_ok=True)

(test_dir / "test.py").write_text(test_code, encoding="utf-8")
(test_dir / "test.js").write_text("""
export function hello(name) {
    return `Hello, ${name}!`;
}

class Calculator {
    add(a, b) {
        return a + b;
    }
}
""", encoding="utf-8")


if __name__ == "__main__":
    print("Testing Python Parser:")
    parser = PythonParser(test_dir)
    for f in parser.scan([".py"]):
        entities = parser.parse_file(f)
        for e in entities:
            print(f"  [{e.type}] {e.name} @ {e.file_path}:{e.start_line}")
            for child in e.children:
                print(f"    └─ [{child.type}] {child.name}")

    print("\nTesting JavaScript Parser:")
    parser = JavaScriptParser(test_dir)
    for f in parser.scan([".js"]):
        entities = parser.parse_file(f)
        for e in entities:
            print(f"  [{e.type}] {e.name} @ {e.file_path}:{e.start_line}")

    print("\nTesting full codebase parse:")
    entities = parse_codebase(test_dir)
    print(f"Found {len(entities)} entities")