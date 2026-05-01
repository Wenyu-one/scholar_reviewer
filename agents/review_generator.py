"""
Phase 4: 综述生成 Agent
基于综合分析结果，生成完整综述草稿。
"""

import json
from typing import Dict, Any, List
from utils.llm_utils import call_llm, format_citation


class ReviewGeneratorAgent:
    """综述生成 Agent"""

    PROMPT_GENERATE_REVIEW = """你是一位资深学术写作专家。请根据以下信息，撰写一篇完整的文献综述。

## 综述主题
{topic}

## 论文列表（含结构化信息）
{papers_json}

## 综合分析结果
趋势分析：
{trend_analysis}

研究空白：
{research_gaps}

## 要求
1. 综述结构：
   - Title（标题）
   - Abstract（摘要，150-250字）
   - 1. Introduction（引言）
   - 2. Related Work（相关工作，按主题/时间分组）
   - 3. Methodology Comparison（方法对比，可引用对比表）
   - 4. Results Analysis（实验结果分析）
   - 5. Discussion（讨论：研究空白、局限性）
   - 6. Future Directions（未来方向）
   - 7. Conclusion（结论）
   - References（参考文献列表，使用 {citation_style} 格式）

2. 写作要求：
   - 使用学术性中文写作
   - 每段附引用标注，如 [Author, Year] 或 [1]
   - 参考文献列表完整，包含所有引用的论文
   - 总字数控制在 3000-6000 字

请直接输出完整综述（Markdown 格式），不要输出其他内容。
"""

    PROMPT_GENERATE_OUTLINE = """你是一位学术写作专家。请根据以下论文列表，生成一篇文献综述的详细大纲。

综述主题：{topic}
论文数量：{n_papers} 篇

论文列表（标题 + 年份）：
{papers_list}

请输出详细大纲，包含每个章节的子标题和关键点。
"""

    def __init__(self, citation_style: str = "ieee", language: str = "zh"):
        self.citation_style = citation_style
        self.language = language

    def generate_review(self,
                        topic: str,
                        papers: List[Dict[str, Any]],
                        analysis_result: Dict[str, Any]) -> str:
        """
        生成完整综述
        返回：Markdown 格式的综述全文
        """
        print(f"  📝 正在生成综述草稿（基于 {len(papers)} 篇论文）...")

        # 构造输入（只取必要字段，控制长度）
        papers_input = []
        for p in papers[:50]:  # 最多使用50篇，避免超长
            structured = p.get("structured", {})
            papers_input.append({
                "title": p.get("title", ""),
                "year": p.get("published", "")[:4] if p.get("published") else "",
                "authors": p.get("authors", [])[:3],
                "methodology": structured.get("methodology", "")[:200],
                "key_results": structured.get("key_results", "")[:150],
                "contribution": structured.get("contribution", "")[:150],
            })

        papers_json = json.dumps(papers_input, ensure_ascii=False, indent=2)

        prompt = self.PROMPT_GENERATE_REVIEW.format(
            topic=topic,
            papers_json=papers_json[:10000],  # 控制长度
            trend_analysis=analysis_result.get("trend_analysis", ""),
            research_gaps="\n".join(analysis_result.get("research_gaps", [])),
            citation_style=self.citation_style,
        )

        result = call_llm(prompt, temperature=0.4, max_tokens=8000)

        if not result or "降级" in result:
            return self._generate_review_rule_based(topic, papers, analysis_result)

        print(f"  ✅ 综述草稿生成完成")
        return result

    def generate_outline(self, topic: str, papers: List[Dict[str, Any]]) -> str:
        """生成综述大纲（快速预览结构）"""
        print(f"  📋 正在生成综述大纲...")

        papers_list = "\n".join([
            f"- {p.get('title', '')} ({p.get('published', '')[:4]})"
            for p in papers[:30]
        ])

        prompt = self.PROMPT_GENERATE_OUTLINE.format(
            topic=topic,
            n_papers=len(papers),
            papers_list=papers_list,
        )

        result = call_llm(prompt, temperature=0.3, max_tokens=2048)
        return result

    def generate_reference_list(self, papers: List[Dict[str, Any]]) -> str:
        """生成参考文献列表（指定格式）"""
        print(f"  📋 正在生成参考文献列表（{self.citation_style} 格式）...")

        refs = []
        for i, p in enumerate(papers, 1):
            ref = format_citation(p, style=self.citation_style)
            refs.append(f"[{i}] {ref}" if self.citation_style == "ieee" else ref)

        return "\n\n".join(refs)

    def _generate_review_rule_based(self, topic: str,
                                   papers: List[Dict[str, Any]],
                                   analysis_result: Dict[str, Any]) -> str:
        """降级模式：基于规则生成综述框架"""
        lines = []
        lines.append(f"# {topic}")
        lines.append("")
        lines.append("## Abstract")
        lines.append("")
        lines.append(f"（降级模式：请在 config.py 中配置 LLM_API_KEY 以生成智能摘要。）")
        lines.append(f"本综述围绕「{topic}」主题，分析了 {len(papers)} 篇相关文献。")
        lines.append("")

        lines.append("## 1. Introduction")
        lines.append("")
        lines.append("（降级模式：请配置 LLM API 以生成引言）")
        lines.append("")

        lines.append("## 2. Related Work")
        lines.append("")
        for i, p in enumerate(papers[:15], 1):
            title = p.get("title", "")
            year = p.get("published", "")[:4] if p.get("published") else "年份不详"
            lines.append(f"{i}. **{title}** ({year})")
            abstract = p.get("abstract", "")[:200]
            lines.append(f"   - {abstract}...")
            lines.append("")

        lines.append("## 3. Methodology Comparison")
        lines.append("")
        lines.append("（降级模式：请配置 LLM API 以生成方法对比）")
        lines.append("")
        lines.append("## 4. Results Analysis")
        lines.append("")
        lines.append("（降级模式：请配置 LLM API 以生成结果分析）")
        lines.append("")
        lines.append("## 5. Discussion")
        lines.append("")
        lines.append("（降级模式：请配置 LLM API 以生成讨论）")
        lines.append("")
        lines.append("## 6. Future Directions")
        lines.append("")
        lines.append("（降级模式：请配置 LLM API 以生成未来方向）")
        lines.append("")
        lines.append("## 7. Conclusion")
        lines.append("")
        lines.append("（降级模式：请配置 LLM API 以生成结论）")
        lines.append("")
        lines.append("## References")
        lines.append("")
        lines.append(self.generate_reference_list(papers))

        return "\n".join(lines)
