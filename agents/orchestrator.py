"""
主协调 Agent（Orchestrator）
统一调度 Phase 1~5，管理全流程状态。
"""

import json
import os
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from agents.literature_collector import LiteratureCollectorAgent
from agents.paper_parser import PaperParserAgent
from agents.analyzer import AnalysisAgent
from agents.review_generator import ReviewGeneratorAgent
from agents.quality_reviewer import QualityReviewerAgent


class ScholarReviewerOrchestrator:
    """
    学术文献综述智能体 - 主协调器
    按顺序执行 5 个阶段，并管理中间状态。
    """

    def __init__(self,
                 topic: str,
                 max_papers: int = 50,
                 use_full_text: bool = False,
                 citation_style: str = "ieee",
                 output_dir: str = "output",
                 verbose: bool = True):
        self.topic = topic
        self.max_papers = max_papers
        self.use_full_text = use_full_text
        self.citation_style = citation_style
        self.output_dir = output_dir
        self.verbose = verbose

        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

        # 初始化各 Agent
        self.collector = LiteratureCollectorAgent(
            max_results=max_papers,
            download_dir=os.path.join(output_dir, "pdfs")
        )
        self.parser = PaperParserAgent(
            use_full_text=use_full_text,
            max_full_text_len=8000,
        )
        self.analyzer = AnalysisAgent()
        self.generator = ReviewGeneratorAgent(
            citation_style=citation_style,
            language="zh",
        )
        self.reviewer = QualityReviewerAgent()

        # 状态
        self.papers: List[Dict[str, Any]] = []
        self.parsed_papers: List[Dict[str, Any]] = []
        self.analysis_result: Dict[str, Any] = {}
        self.review_text: str = ""
        self.quality_report: Dict[str, Any] = {}

    def run(self) -> Dict[str, Any]:
        """执行完整流程（Phase 1 ~ Phase 5）"""
        start_time = time.time()
        print(f"\n{'='*60}")
        print(f"  ScholarReviewer AI  学术文献综述智能体")
        print(f"  主题：{self.topic}")
        print(f"  最大论文数：{self.max_papers}")
        print(f"{'='*60}\n")

        # Phase 1：文献采集
        self._phase1_collect()

        # Phase 2：论文解析
        self._phase2_parse()

        # Phase 3：综合分析
        self._phase3_analyze()

        # Phase 4：综述生成
        self._phase4_generate()

        # Phase 5：质量审查
        self._phase5_review()

        # 保存结果
        self._save_all_results()

        elapsed = round(time.time() - start_time, 1)
        print(f"\n{'='*60}")
        print(f"  ✅  全部完成！耗时 {elapsed} 秒")
        print(f"  输出目录：{os.path.abspath(self.output_dir)}")
        print(f"{'='*60}\n")

        return {
            "topic": self.topic,
            "n_papers": len(self.papers),
            "review_text": self.review_text,
            "output_dir": self.output_dir,
        }

    def _phase1_collect(self):
        print(f"\n{'─'*60}")
        print(f"  Phase 1：文献采集")
        print(f"{'─'*60}")
        t0 = time.time()

        # arXiv
        arxiv_papers = self.collector.collect_arxiv(
            query=self.topic,
            max_results=self.max_papers,
        )

        # PubMed（可选）
        pubmed_papers = []
        try:
            pubmed_papers = self.collector.collect_pubmed(
                query=self.topic,
                max_results=min(30, self.max_papers),
            )
        except Exception as e:
            print(f"  ⚠️  PubMed 检索失败：{e}（跳过）")

        # 合并去重
        all_papers = arxiv_papers + pubmed_papers
        seen_ids = set()
        deduped = []
        for p in all_papers:
            pid = p.get("id", p.get("title", ""))
            if pid not in seen_ids:
                seen_ids.add(pid)
                deduped.append(p)
        self.papers = deduped

        # 过滤低相关度
        self.papers = self.collector.filter_by_similarity(
            self.papers, query=self.topic, threshold=0.2
        )

        elapsed = round(time.time() - t0, 1)
        print(f"  ✅ Phase 1 完成：共采集 {len(self.papers)} 篇论文（耗时 {elapsed}s）")

    def _phase2_parse(self):
        print(f"\n{'─'*60}")
        print(f"  Phase 2：论文解析")
        print(f"{'─'*60}")
        t0 = time.time()

        self.parsed_papers = self.parser.parse_papers_batch(self.papers)

        elapsed = round(time.time() - t0, 1)
        print(f"  ✅ Phase 2 完成：{len(self.parsed_papers)} 篇论文已解析（耗时 {elapsed}s）")

    def _phase3_analyze(self):
        print(f"\n{'─'*60}")
        print(f"  Phase 3：综合分析")
        print(f"{'─'*60}")
        t0 = time.time()

        self.analysis_result = self.analyzer.analyze(self.parsed_papers)

        elapsed = round(time.time() - t0, 1)
        print(f"  ✅ Phase 3 完成：综合分析已生成（耗时 {elapsed}s）")

    def _phase4_generate(self):
        print(f"\n{'─'*60}")
        print(f"  Phase 4：综述生成")
        print(f"{'─'*60}")
        t0 = time.time()

        self.review_text = self.generator.generate_review(
            topic=self.topic,
            papers=self.parsed_papers,
            analysis_result=self.analysis_result,
        )

        elapsed = round(time.time() - t0, 1)
        print(f"  ✅ Phase 4 完成：综述草稿已生成（耗时 {elapsed}s）")

    def _phase5_review(self):
        print(f"\n{'─'*60}")
        print(f"  Phase 5：质量审查")
        print(f"{'─'*60}")
        t0 = time.time()

        self.quality_report = self.reviewer.review(
            review_text=self.review_text,
            papers=self.parsed_papers,
        )

        elapsed = round(time.time() - t0, 1)
        print(f"  ✅ Phase 5 完成：质量审查已生成（耗时 {elapsed}s）")

    def _save_all_results(self):
        """保存所有结果到输出目录"""
        print(f"\n  💾 正在保存结果...")

        # 1. 综述草稿
        review_path = os.path.join(self.output_dir, "review.md")
        with open(review_path, "w", encoding="utf-8") as f:
            f.write(self.review_text)
        print(f"    ✓ 综述草稿：{review_path}")

        # 2. 质量审查报告
        report_path = os.path.join(self.output_dir, "quality_report.md")
        self.reviewer.save_report(self.quality_report, report_path)
        print(f"    ✓ 审查报告：{report_path}")

        # 3. 方法对比表
        if self.analysis_result.get("method_comparison_table"):
            method_path = os.path.join(self.output_dir, "method_comparison_table.md")
            with open(method_path, "w", encoding="utf-8") as f:
                f.write(self.analysis_result["method_comparison_table"])
            print(f"    ✓ 方法对比表：{method_path}")

        # 4. 实验结果对比表
        if self.analysis_result.get("result_comparison_table"):
            result_path = os.path.join(self.output_dir, "result_comparison_table.md")
            with open(result_path, "w", encoding="utf-8") as f:
                f.write(self.analysis_result["result_comparison_table"])
            print(f"    ✓ 结果对比表：{result_path}")

        # 5. 趋势分析
        if self.analysis_result.get("trend_analysis"):
            trend_path = os.path.join(self.output_dir, "trend_analysis.md")
            with open(trend_path, "w", encoding="utf-8") as f:
                f.write(self.analysis_result["trend_analysis"])
            print(f"    ✓ 趋势分析：{trend_path}")

        # 6. 论文列表（JSON）
        papers_path = os.path.join(self.output_dir, "papers.json")
        with open(papers_path, "w", encoding="utf-8") as f:
            json.dump(self.parsed_papers, f, ensure_ascii=False, indent=2)
        print(f"    ✓ 论文列表：{papers_path}")

        # 7. 参考文献列表
        ref_path = os.path.join(self.output_dir, "references.txt")
        refs = self.generator.generate_reference_list(self.parsed_papers)
        with open(ref_path, "w", encoding="utf-8") as f:
            f.write(refs)
        print(f"    ✓ 参考文献：{ref_path}")
