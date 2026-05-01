"""
Phase 2: 论文解析 Agent
从 PDF 或摘要中提取结构化信息（研究问题、方法、结果、局限等）。
支持降级模式：若无 LLM API，则使用规则提取。
"""

import json
import re
from typing import Dict, Any, List, Optional

from utils.llm_utils import call_llm, chunk_text


class PaperParserAgent:
    """论文解析 Agent：提取单篇论文的结构化信息"""

    PROMPT_EXTRACT = """你是一位学术论文分析专家。请仔细阅读以下论文摘要/全文，提取以下结构化信息，输出为纯 JSON（不要输出```json```包裹）：

{{
  "research_question": "论文试图解决的核心研究问题（1-2句话）",
  "methodology": "论文提出的方法/模型/算法（详细描述）",
  "dataset": "使用的数据集名称，如未知则填'未说明'",
  "key_results": "主要实验结果（包含关键指标和数值）",
  "limitations": "论文作者提到的局限性或你自己分析出的不足",
  "future_work": "未来工作方向",
  "contribution": "论文的主要贡献（1-2句话）",
  "keywords": ["关键词1", "关键词2", "关键词3"]
}}

论文内容如下：

{content}

只输出JSON，不要输出其他内容。
"""

    def __init__(self, use_full_text: bool = False, max_full_text_len: int = 8000):
        self.use_full_text = use_full_text
        self.max_full_text_len = max_full_text_len

    def parse_paper(self, paper_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析单篇论文，返回增强后的 paper_info（新增 structured 字段）
        """
        abstract = paper_info.get("abstract", "")
        title = paper_info.get("title", "")

        print(f"    🔧  解析论文：{title[:50]}...")

        # 优先使用 LLM 提取
        content_for_llm = abstract  # MVP：先用摘要
        if self.use_full_text and paper_info.get("pdf_path"):
            content_for_llm = self._read_pdf_text(paper_info["pdf_path"])

        if content_for_llm.strip():
            structured = self._extract_with_llm(title, content_for_llm)
        else:
            structured = self._extract_with_rules(title, abstract)

        # 合并到 paper_info
        paper_info["structured"] = structured
        return paper_info

    def parse_papers_batch(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量解析论文"""
        results = []
        total = len(papers)
        for i, paper in enumerate(papers, 1):
            print(f"  🔧  解析进度：{i}/{total}")
            results.append(self.parse_paper(paper))
        return results

    def _extract_with_llm(self, title: str, content: str) -> Dict[str, Any]:
        """使用 LLM 提取结构化信息"""
        # 内容过长时分块处理（取前 max_full_text_len 字符）
        if len(content) > self.max_full_text_len:
            content = content[:self.max_full_text_len] + "\n[内容过长，已截断，请基于以上内容分析]"

        prompt = self.PROMPT_EXTRACT.format(content=content)
        system_prompt = "你是一位学术论文分析专家，擅长从论文摘要/全文中提取结构化信息。请严格输出JSON格式。"

        try:
            response = call_llm(prompt, system_prompt=system_prompt, max_tokens=2048)
            # 尝试解析 JSON
            response = response.strip()
            if response.startswith("```"):
                # 去除 ```json ... ``` 包裹
                response = re.sub(r"^```[a-z]*\n?", "", response)
                response = re.sub(r"\n?```$", "", response)
            data = json.loads(response)
            return data
        except json.JSONDecodeError:
            print(f"    ⚠️  LLM 返回格式异常，使用规则提取")
            return self._extract_with_rules(title, content[:500])
        except Exception as e:
            print(f"    ⚠️  LLM 调用失败：{e}，使用规则提取")
            return self._extract_with_rules(title, content[:500])

    def _extract_with_rules(self, title: str, abstract: str) -> Dict[str, Any]:
        """降级模式：使用规则提取（关键词匹配）"""
        text = (title + " " + abstract).lower()

        # 简单规则提取
        research_question = abstract[:200] + "..." if len(abstract) > 200 else abstract
        methodology = "（规则提取）" + self._extract_method_keywords(text)
        dataset = self._extract_dataset_keywords(text)
        key_results = "（请配置LLM API以自动提取实验结果）"
        limitations = "（请配置LLM API以自动提取局限性）"
        future_work = "（请配置LLM API以自动提取未来方向）"
        contribution = "（请配置LLM API以自动提取贡献）"
        keywords = self._extract_keywords(text)

        return {
            "research_question": research_question,
            "methodology": methodology,
            "dataset": dataset,
            "key_results": key_results,
            "limitations": limitations,
            "future_work": future_work,
            "contribution": contribution,
            "keywords": keywords,
            "_extraction_method": "rule-based",
        }

    def _read_pdf_text(self, pdf_path: str) -> str:
        """读取 PDF 文件前 N 页的文本内容"""
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc[:8]:  # 只读前8页（摘要+引言通常够用）
                text += page.get_text()
            return text
        except ImportError:
            print("    ⚠️  未安装 PyMuPDF（pip install PyMuPDF），跳过全文解析")
            return ""
        except Exception as e:
            print(f"    ⚠️  读取 PDF 失败：{e}")
            return ""

    def _extract_method_keywords(self, text: str) -> str:
        """从文本中提取方法相关关键词"""
        method_keywords = ["method", "approach", "model", "algorithm", "framework",
                         "propose", "novel", "network", "transformer", "lstm", "cnn"]
        found = [kw for kw in method_keywords if kw in text]
        return "疑似方法关键词：" + ", ".join(found[:5]) if found else "未识别"

    def _extract_dataset_keywords(self, text: str) -> str:
        """从文本中提取数据集名称"""
        dataset_pattern = r"\b([A-Z]{2,}\d*)\b"  # 简单匹配大写字母组成的数据集名
        matches = re.findall(dataset_pattern, text)
        known_datasets = ["ImageNet", "COCO", "SQuAD", "GLUE", "SuperGLUE",
                         "MNIST", "CIFAR", "PASCAL", "ADE20K"]
        for ds in known_datasets:
            if ds.lower() in text:
                return ds
        return "未说明（规则提取未识别）"

    def _extract_keywords(self, text: str) -> List[str]:
        """简单提取高频词作为关键词"""
        stop_words = {"the", "a", "an", "and", "or", "in", "on", "at", "to", "for",
                      "of", "with", "by", "is", "are", "was", "were", "be", "been"}
        words = re.findall(r"\b[a-z]{4,}\b", text)
        filtered = [w for w in words if w not in stop_words]
        # 返回出现次数最多的5个词
        from collections import Counter
        return [w for w, _ in Counter(filtered).most_common(5)]
