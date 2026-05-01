"""
Phase 5: 质量审查 Agent
检查引用完整性、逻辑连贯性、事实准确性。
"""

import re
from typing import Dict, Any, List


class QualityReviewerAgent:
    """质量审查 Agent：对生成的综述进行多维度审查"""

    PROMPT_REVIEW = """你是一位学术质量审查专家。请对以下综述草稿进行质量审查，重点检查：

1. **引用完整性**：文中是否有引用标注（[Author, Year] 或 [1] 格式）？文末参考文献列表是否完整？
2. **逻辑连贯性**：各章节之间是否有清晰的过渡？论证是否充分？
3. **事实准确性**：实验数据、年份、指标是否在文中保持一致？

## 综述草稿
{review_text}

## 论文列表（用于核对引用）
{papers_list}

请输出审查报告，格式如下：

### 引用完整性
- 评分：/10
- 问题：[列出具体问题]

### 逻辑连贯性
- 评分：/10
- 问题：[列出具体问题]

### 事实准确性
- 评分：/10
- 问题：[列出具体问题]

### 修改建议
[按优先级列出具体修改建议]
"""

    def __init__(self):
        pass

    def review(self,
               review_text: str,
               papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        对综述草稿进行质量审查
        返回：{"report": str, "scores": dict, "suggestions": list}
        """
        print("  🔎 正在进行质量审查...")

        # 规则检查（快速）
        rule_report = self._rule_based_review(review_text, papers)

        # LLM 检查（深度）
        llm_report = self._llm_review(review_text, papers)

        # 合并报告
        full_report = self._merge_reports(rule_report, llm_report)

        print("  ✅ 质量审查完成")
        return full_report

    def _rule_based_review(self,
                            review_text: str,
                            papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """基于规则进行基础检查（降级模式也可用）"""
        report_lines = []

        # 检查1：是否有引用标注
        citations = re.findall(r"\[([^\]]+)\]", review_text)
        citation_count = len(citations)
        report_lines.append(f"文中引用标注数量：{citation_count}")
        if citation_count < len(papers) * 0.5:
            report_lines.append("⚠️ 引用标注数量偏少（少于论文数量的一半）")

        # 检查2：是否有参考文献列表
        has_references = "reference" in review_text.lower() or "参考文献" in review_text
        report_lines.append(f"是否包含参考文献列表：{'是' if has_references else '否 ⚠️'}")

        # 检查3：各章节是否存在
        sections = ["introduction", "related work", "method", "result", "discussion", "conclusion"]
        found_sections = []
        for sec in sections:
            if sec in review_text.lower():
                found_sections.append(sec)
        report_lines.append(f"检测到的章节：{', '.join(found_sections) if found_sections else '未检测到标准章节结构 ⚠️'}")

        # 检查4：字数估算
        char_count = len(review_text)
        report_lines.append(f"估算字数：~{char_count} 字（中文字符）")

        return {
            "rule_check": "\n".join(report_lines),
            "citation_count": citation_count,
            "has_references": has_references,
            "sections_found": found_sections,
            "char_count": char_count,
        }

    def _llm_review(self,
                     review_text: str,
                     papers: List[Dict[str, Any]]) -> str:
        """使用 LLM 进行深度质量审查"""
        from utils.llm_utils import call_llm

        # 构造论文列表（简要）
        papers_list = "\n".join([
            f"- {p.get('title', '')} ({p.get('published', '')[:4]})"
            for p in papers[:30]
        ])

        # 截取综述文本（避免超长）
        text_for_review = review_text[:8000]
        if len(review_text) > 8000:
            text_for_review += "\n\n[内容过长已截断，以上为综述前半部分]"

        prompt = self.PROMPT_REVIEW.format(
            review_text=text_for_review,
            papers_list=papers_list,
        )

        try:
            result = call_llm(prompt, temperature=0.2, max_tokens=3000)
            if "降级" in result:
                return "(LLM审查降级，仅规则检查结果可用）"
            return result
        except Exception as e:
            print(f"  ⚠️ LLM审查失败：{e}")
            return "(LLM审查失败，仅规则检查结果可用）"

    def _merge_reports(self,
                       rule_report: Dict[str, Any],
                       llm_report: str) -> Dict[str, Any]:
        """合并规则检查和LLM审查结果"""
        full_report = f"""# 质量审查报告

## 基础检查结果（自动）
{rule_report['rule_check']}

## 深度审查结果（AI辅助）
{llm_report}

## 综合评分
- 引用完整性：{"✅ 通过" if rule_report['citation_count'] > 5 else "⚠️ 需改进"}
- 结构完整性：{"✅ 通过" if len(rule_report['sections_found']) >= 4 else "⚠️ 章节不完整"}
- 参考文献：{"✅ 通过" if rule_report['has_references'] else "⚠️ 缺少参考文献列表"}
"""
        return {
            "report": full_report,
            "rule_report": rule_report,
            "llm_report": llm_report,
        }

    def save_report(self, report_data: Dict[str, Any], output_path: str):
        """保存审查报告到文件"""
        import os
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report_data["report"])
        print(f"  💾 审查报告已保存：{output_path}")
