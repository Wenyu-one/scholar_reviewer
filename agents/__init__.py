"""
agents 包
包含所有 Agent 模块：
- orchestrator: 主协调器
- literature_collector: Phase 1 文献采集
- paper_parser: Phase 2 论文解析
- analyzer: Phase 3 综合分析
- review_generator: Phase 4 综述生成
- quality_reviewer: Phase 5 质量审查
"""

__all__ = [
    "ScholarReviewerOrchestrator",
    "LiteratureCollectorAgent",
    "PaperParserAgent",
    "AnalysisAgent",
    "ReviewGeneratorAgent",
    "QualityReviewerAgent",
]
