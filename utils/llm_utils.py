"""
工具函数：LLM调用封装
支持多种LLM后端（OpenAI / 通义千问 / DeepSeek 等）
"""

import os
import json
import time
from typing import Optional, List, Dict, Any

# ============
# LLM 调用封装
# ============

def call_llm(
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 4096,
    retry: int = 3,
) -> str:
    """
    统一LLM调用入口。
    根据 config.LLM_CONFIG 选择后端。
    如果没有配置API Key，则使用内置的启发式规则生成（降级模式）。
    """
    # 尝试导入配置
    try:
        from config import LLM_CONFIG
    except ImportError:
        LLM_CONFIG = {
            "provider": "mock",
            "model": "mock",
            "api_key": "",
        }

    provider = LLM_CONFIG.get("provider", "mock")

    # 无API Key时降级到mock模式
    api_key = LLM_CONFIG.get("api_key", "")
    if not api_key and provider != "mock":
        print("  ⚠️  未检测到API Key，使用降级模式（基于规则生成）")
        return _mock_response(prompt)

    if provider == "openai":
        return _call_openai(prompt, system_prompt, temperature, max_tokens, retry)
    elif provider == "qwen":
        return _call_qwen(prompt, system_prompt, temperature, max_tokens, retry)
    else:
        # mock / 未知 provider
        return _mock_response(prompt)


def _call_openai(prompt: str, system_prompt: Optional[str],
                  temperature: float, max_tokens: int, retry: int) -> str:
    """调用 OpenAI 兼容 API"""
    try:
        from openai import OpenAI
        from config import LLM_CONFIG

        client = OpenAI(
            api_key=LLM_CONFIG["api_key"],
            base_url=LLM_CONFIG.get("base_url"),
        )

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        for attempt in range(retry):
            try:
                response = client.chat.completions.create(
                    model=LLM_CONFIG["model"],
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return response.choices[0].message.content
            except Exception as e:
                if attempt == retry - 1:
                    raise
                print(f"  ⚠️  API调用失败，重试 {attempt + 2}/{retry}... 错误: {e}")
                time.sleep(2 ** attempt)

        return ""
    except ImportError:
        print("  ⚠️  未安装 openai 包，使用降级模式")
        return _mock_response(prompt)
    except Exception as e:
        print(f"  ⚠️  LLM调用失败: {e}，使用降级模式")
        return _mock_response(prompt)


def _call_qwen(prompt: str, system_prompt: Optional[str],
                temperature: float, max_tokens: int, retry: int) -> str:
    """调用通义千问 API（Dashscope）"""
    try:
        import dashscope
        from dashscope import Generation
        from config import LLM_CONFIG

        dashscope.api_key = LLM_CONFIG["api_key"]

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        for attempt in range(retry):
            try:
                response = Generation.call(
                    model=LLM_CONFIG["model"],
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return response.output.text
            except Exception as e:
                if attempt == retry - 1:
                    raise
                print(f"  ⚠️  API调用失败，重试 {attempt + 2}/{retry}... 错误: {e}")
                time.sleep(2 ** attempt)

        return ""
    except ImportError:
        print("  ⚠️  未安装 dashscope 包，使用降级模式")
        return _mock_response(prompt)
    except Exception as e:
        print(f"  ⚠️  LLM调用失败: {e}，使用降级模式")
        return _mock_response(prompt)


def _mock_response(prompt: str) -> str:
    """
    降级模式：当没有API Key时，返回基于规则的提示性内容。
    实际部署时，请配置有效的LLM API。
    """
    # 简单的关键词匹配，生成有意义的默认回复
    if "摘要" in prompt or "abstract" in prompt.lower():
        return "(LLM降级模式) 请在 config.py 中配置 LLM_API_KEY 以启用智能摘要提取。"
    if "方法" in prompt or "method" in prompt.lower():
        return "(LLM降级模式) 请在 config.py 中配置 LLM_API_KEY 以启用智能方法提取。"
    if "对比" in prompt or "compare" in prompt.lower():
        return "(LLM降级模式) 请在 config.py 中配置 LLM_API_KEY 以启用智能对比分析。"
    if "综述" in prompt or "review" in prompt.lower():
        return "(LLM降级模式) 请在 config.py 中配置 LLM_API_KEY 以启用智能综述生成。"

    return "(LLM降级模式) 请在 config.py 中配置 LLM_API_KEY 以获得完整功能。当前为基于规则的降级输出。"


# ============
# 文本处理工具
# ============

def chunk_text(text: str, max_len: int = 4000) -> List[str]:
    """将长文本按段落分块，每块不超过 max_len 字符"""
    paragraphs = text.split("\n\n")
    chunks = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 2 <= max_len:
            current = current + "\n\n" + para if current else para
        else:
            if current:
                chunks.append(current)
            current = para
    if current:
        chunks.append(current)
    return chunks


def format_citation(paper_info: Dict[str, Any], style: str = "ieee") -> str:
    """格式化单篇论文的引用"""
    title = paper_info.get("title", "Unknown Title")
    authors = paper_info.get("authors", [])
    year = paper_info.get("published", "Unknown")[:4] if paper_info.get("published") else "Unknown"
    url = paper_info.get("url", "")

    author_str = ", ".join(authors[:3]) + (" et al." if len(authors) > 3 else "") if authors else "Unknown Author"

    if style == "ieee":
        return f"[{author_str}, {year}] {title}. [Online]. Available: {url}"
    elif style == "apa":
        return f"{author_str} ({year}). {title}. Retrieved from {url}"
    elif style == "bibtex":
        # 生成 BibTeX 条目
        key = f"{authors[0].split()[-1].lower()}{year}" if authors else "unknown"
        return f"""@article{{{key},
  title={{{title}}},
  author={{{', '.join(authors)}}},
  year={{{year}}},
  url={{{url}}}
}}"""
    else:
        return f"{author_str}. {title}. {year}."


# ============
# 文件工具
# ============

def ensure_dir(path: str):
    """确保目录存在"""
    import os
    os.makedirs(path, exist_ok=True)


def save_json(data: Any, filepath: str):
    """保存为 JSON 文件"""
    import os
    ensure_dir(os.path.dirname(filepath) or ".")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(filepath: str) -> Any:
    """读取 JSON 文件"""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)
