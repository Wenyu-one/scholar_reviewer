"""
Phase 3: 综合分析 Agent
对所有论文的结构化信息进行横向对比分析，
生成方法对比表、实验结果对比表和趋势分析。
"""

import json
from typing import Dict, Any, List
from utils.llm_utils import call_llm


class AnalysisAgent:
    """综合分析 Agent：横向对比多论文，识别趋势和研究空白"""

    PROMPT_COMPARE_METHODS = """你是一位学术评审专家。请根据以下论文列表的结构化信息，
生成一份「方法对比表」，以 Markdown 表格形式输出。

对比维度包括：论文标题、提出的方法、核心创新点、使用的编码器/解码器、训练策略。

论文列表（JSON）：
{papers_json}

请直接输出 Markdown 表格，不要输出其他内容。
"""

    PROMPT_COMPARE_RESULTS = """你是一位学术评审专家。请根据以下论文列表的结构化信息，
生成一份「实验结果对比表」，以 Markdown 表格形式输出。

对比维度包括：论文标题、使用的数据集、主要指标名称、指标数值、相比基线的提升。

论文列表（JSON）：
{papers_json}

请直接输出 Markdown 表格，不要输出其他内容。
如果某篇论文没有实验结果，则对应单元格填"未报告"。
"""

    PROMPT_TREND_ANALYSIS = """你是一位学术综述专家。请根据以下论文列表的结构化信息，
分析该领域的研究趋势，输出 300-500 字的分析文字。

分析维度：
1. 方法论的演进脉络（从早期方法到最新方法的演进路径）
2. 当前的研究热点
3. 尚未解决的研究空白（research gap）
4. 未来可能的研究方向

论文列表（JSON）：
{papers_json}

请用学术性中文输出（如使用英文请保持英文）。
"""

    def __init__(self):
        pass

    def analyze(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        对论文列表进行综合对比分析
        返回：{
            "method_comparison_table": str,  # Markdown 表格
            "result_comparison_table": str,  # Markdown 表格
            "trend_analysis": str,            # 趋势分析文字
            "research_gaps": List[str],       # 研究空白列表
        }
        """
        print(f"  📊 正在综合分析 {len(papers)} 篇论文...")

        # 构造输入 JSON（只取关键字段，避免超长）
        papers_input = []
        for p in papers:
            structured = p.get("structured", {})
            papers_input.append({
                "title": p.get("title", ""),
                "year": p.get("published", "")[:4] if p.get("published") else "",
                "methodology": structured.get("methodology", "")[:300],
                "dataset": structured.get("dataset", ""),
                "key_results": structured.get("key_results", "")[:200],
                "limitations": structured.get("limitations", ""),
                "future_work": structured.get("future_work", ""),
                "keywords": structured.get("keywords", []),
            })

        papers_json = json.dumps(papers_input, ensure_ascii=False, indent=2)

        # 用 LLM 生成对比表和趋势分析
        method_table = self._generate_method_table(papers_json, len(papers))
        result_table = self._generate_result_table(papers_json, len(papers))
        trend_analysis = self._generate_trend_analysis(papers_json, len(papers))

        # 提取研究空白（从趋势分析中自动提取或单独调用 LLM）
        research_gaps = self._extract_research_gaps(papers_json)

        print(f"  ✅ 综合分析完成")

        return {
            "method_comparison_table": method_table,
            "result_comparison_table": result_table,
            "trend_analysis": trend_analysis,
            "research_gaps": research_gaps,
            "papers_analyzed": len(papers),
        }

    def _generate_method_table(self, papers_json: str, n_papers: int) -> str:
        """生成方法对比表"""
        print(f"    🔧  生成方法对比表（{n_papers} 篇）...")
        prompt = self.PROMPT_COMPARE_METHODS.format(papers_json=papers_json[:6000]))
        result = call_llm(prompt, temperature=0.2, max_tokens=2048)
        if not result or "降级" in result:
            return self._rule_based_method_table(papers_json)
        return result

    def _generate_result_table(self, papers_json: str, n_papers: int) -> str:
        """生成实验结果对比表"""
        print(f"    🔧  生成实验结果对比表（{n_papers} 篇）...")
        prompt = self.PROMPT_COMPARE_RESULTS.format(papers_json=papers_json[:6000]))
        result = call_llm(prompt, temperature=0.2, max_tokens=2048)
        if not result or "降级" in result:
            return self._rule_based_result_table(papers_json)
        return result

    def _generate_trend_analysis(self, papers_json: str, n_papers: int) -> str:
        """生成研究趋势分析"""
        print(f"    🔧  生成研究趋势分析（{n_papers} 篇）...")
        prompt = self.PROMPT_TREND_ANALYSIS.format(papers_json=papers_json[:8000]))
        result = call_llm(prompt, temperature=0.3, max_tokens=1500)
        if not result or "降级" in result:
            return self._rule_based_trend_analysis(papers_json)
        return result

    def _extract_research_gaps(self, papers_json: str) -> List[str]:
        """从论文的 limitations 字段中提取研究空白"""
        try:
            data = json.loads(papers_json)
            gaps = []
            for p in data:
                lim = p.get("limitations", "")
                if lim and lim not in ("（请配置LLM API以自动提取局限性）", ""):
                    # 简单拆分：按句号或分号
                    parts = [s.strip() for s in lim.replace("；", ";").split(";")]
                    gaps.extend([p for p in parts if len(p) > 10])
            return gaps[:10] if gaps else ["（请配置LLM API以自动识别研究空白）"]
        except Exception:
            return ["（规则提取失败，请配置LLM API）"]

    # ========== 降级规则 ==========

    def _rule_based_method_table(self, papers_json: str) -> str:
        """基于规则生成方法对比表（降级模式）"""
        try:
            data = json.loads(papers_json)
        except Exception:
            return "| 论文标题 | 方法 | 创新点 |\n|---|---|---|\n| （降级模式，请配置LLM API）| - | - |"

        lines = ["| 论文标题 | 方法（规则提取） | 数据集 |", "|---|---|---|"]
        for p in data[:20]:  # 最多显示20行
            title = p.get("title", "")[:40] + "..." if len(p.get("title", "")) > 40 else p.get("title", "")
            method = p.get("methodology", "")[:50]
            dataset = p.get("dataset", "未说明")
            lines.append(f"| {title} | {method} | {dataset} |")
        return "\n".join(lines)

    def _rule_based_result_table(self, papers_json: str) -> str:
        """基于规则生成实验结果对比表（降级模式）"""
        try:
            data = json.loads(papers_json)
        except Exception:
            return "| 论文标题 | 数据集 | 主要指标 | 指标值 |\n|---|---|---|---|\n| （降级模式）| - | - | - |"

        lines = ["| 论文标题 | 数据集 | 主要指标（规则提取） |", "|---|---|---|"]
        for p in data[:20]:
            title = p.get("title", "")[:40] + "..." if len(p.get("title", "")) > 40 else p.get("title", "")
            dataset = p.get("dataset", "未说明")
            results = p.get("key_results", "")[:60]
            lines.append(f"| {title} | {dataset} | {results} |")
        return "\n".join(lines)

    def _rule_based_trend_analysis(self, papers_json: str) -> str:
        """基于规则生成趋势分析（降级模式）"""
        try:
            data = json.loads(papers_json)
            years = [p.get("year", "") for p in data if p.get("year", "").isdigit()]
            if years:
                year_dist = {}
                for y in years:
                    year_dist[y] = year_dist.get(y, 0) + 1
                top_year = max(year_dist, key=year_dist.get)
                return (
                    f"（降级模式趋势分析）\n\n"
                    f"分析范围内的论文发表年份分布：{year_dist}。\n"
                    f"发表量最高的年份是 {top_year} 年（{year_dist[top_year]} 篇）。\n"
                    f"请配置 LLM API 以获取更深入的趋势分析。"
                )
        except Exception:
            pass
        return "（降级模式）请配置 LLM_API_KEY 以启用智能趋势分析。"
