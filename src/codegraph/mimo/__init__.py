"""MiMo API 客户端 - 调用小米自研大模型."""

import os
from dataclasses import dataclass
from typing import Iterator
import requests


@dataclass
class MiMoMessage:
    """对话消息."""
    role: str  # system, user, assistant
    content: str


@dataclass
class MiMoResponse:
    """API 响应."""
    content: str
    usage: dict
    model: str


class MiMoClient:
    """MiMo API 客户端.

    API 文档: https://platform.xiaomimimo.com
    """

    BASE_URL = "https://api.xiaomimimo.com/v1"

    def __init__(self, api_key: str | None = None):
        """初始化客户端.

        Args:
            api_key: MiMo API Key。如果为 None，从环境变量 MIMO_API_KEY 读取。
        """
        self.api_key = api_key or os.environ.get("MIMO_API_KEY", "")
        if not self.api_key:
            raise ValueError("需要提供 MiMo API Key")

    def chat(
        self,
        messages: list[MiMoMessage],
        model: str = "MiMo-Text",
        stream: bool = False,
        **kwargs,
    ) -> MiMoResponse:
        """发送对话请求.

        Args:
            messages: 对话消息列表
            model: 模型名称，默认 MiMo-Text
            stream: 是否流式返回
            **kwargs: 其他参数如 temperature, max_tokens 等

        Returns:
            API 响应
        """
        url = f"{self.BASE_URL}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": stream,
            **kwargs,
        }

        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        data = response.json()
        return MiMoResponse(
            content=data["choices"][0]["message"]["content"],
            usage=data.get("usage", {}),
            model=data.get("model", model),
        )

    def stream_chat(
        self,
        messages: list[MiMoMessage],
        model: str = "MiMo-Text",
        **kwargs,
    ) -> Iterator[str]:
        """流式对话.

        Args:
            messages: 对话消息列表
            model: 模型名称
            **kwargs: 其他参数

        Yields:
            流式输出的文本片段
        """
        url = f"{self.BASE_URL}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
            **kwargs,
        }

        with requests.post(url, headers=headers, json=payload, stream=True, timeout=120) as resp:
            for line in resp.iter_lines():
                if line:
                    line = line.decode("utf-8")
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        import json
                        try:
                            obj = json.loads(data)
                            content = obj.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue


def explain_code_with_mimo(
    client: MiMoClient,
    code_snippet: str,
    language: str = "代码",
) -> str:
    """用 MiMo 解释代码.

    Args:
        client: MiMo 客户端
        code_snippet: 代码片段
        language: 编程语言

    Returns:
        代码的中文解释
    """
    messages = [
        MiMoMessage(
            role="system",
            content="你是一个专业的中文代码分析师，擅长解释代码的功能、业务逻辑和技术细节。",
        ),
        MiMoMessage(
            role="user",
            content=f"请解释以下{language}代码的功能和实现逻辑，用中文回答，简洁明了：\n\n```{language}\n{code_snippet}\n```",
        ),
    ]

    response = client.chat(messages)
    return response.content


def summarize_entities_with_mimo(
    client: MiMoClient,
    entities: list,
    codebase_summary: str = "",
) -> dict:
    """用 MiMo 总结代码实体列表，生成中文描述.

    Args:
        client: MiMo 客户端
        entities: 代码实体列表
        codebase_summary: 代码库整体描述

    Returns:
        每个实体的中文描述字典
    """
    if not entities:
        return {}

    # 构建实体描述
    entity_list = []
    for e in entities:
        entity_list.append(f"- {e.type}: {e.name} (文件: {e.file_path})")

    entities_text = "\n".join(entity_list[:50])  # 限制数量避免超出 token

    messages = [
        MiMoMessage(
            role="system",
            content="你是一个专业的中文代码分析师，根据代码实体列表，分析其整体架构和主要功能模块。",
        ),
        MiMoMessage(
            role="user",
            content=f"代码库整体描述：{codebase_summary or '未提供'}\n\n代码实体列表（前50个）：\n{entities_text}\n\n请给出：\n1. 这个代码库的主要功能模块\n2. 核心的数据流或业务流程\n3. 关键技术栈",
        ),
    ]

    response = client.chat(messages)
    return {"summary": response.content, "entities": entities_text}