"""
ScholarReviewer AI - 配置文件
用户可根据自己的情况修改以下配置
"""

import os

# ============
# LLM 配置（核心）
# ============

# 支持多种LLM后端，取消注释你使用的那个

# OpenAI / OpenAI兼容API（推荐）
LLM_CONFIG = {
    "provider": "openai",  # openai / anthropic / qwen / custom
    "model": "gpt-4o",
    "api_key": os.getenv("OPENAI_API_KEY", ""),
    "base_url": None,  # 如需使用代理API，填写base_url，如 "https://api.proxy.com/v1"
    "temperature": 0.3,
    "max_tokens": 4096,
}

# 通义千问（阿里云）
# LLM_CONFIG = {
#     "provider": "qwen",
#     "model": "qwen-max",
#     "api_key": os.getenv("DASHSCOPE_API_KEY", ""),
#     "temperature": 0.3,
# }

# DeepSeek
# LLM_CONFIG = {
#     "provider": "openai",  # DeepSeek兼容OpenAI格式
#     "model": "deepseek-chat",
#     "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
#     "base_url": "https://api.deepseek.com/v1",
#     "temperature": 0.3,
# }

# ============
# 文献采集配置
# ============

LITERATURE_CONFIG = {
    "arxiv_max_results": 50,       # arXiv单次最大检索数
    "pubmed_max_results": 50,      # PubMed单次最大检索数
    "similarity_threshold": 0.3,  # 相似度阈值（低于此值视为不相关，过滤掉）
    "download_dir": "papers",      # PDF下载目录（相对于项目根目录）
}

# ============
# 论文解析配置
# ============

PARSER_CONFIG = {
    "use_full_text": False,    # True=解析全文，False=仅解析摘要（更快）
    "max_full_text_len": 8000,  # 全文解析时最大字符数（避免超长）
}

# ============
# 综述生成配置
# ============

REVIEW_CONFIG = {
    "default_language": "zh",   # zh=中文，en=英文
    "citation_style": "ieee",    # ieee / apa / bibtex / mla
    "max_papers_for_review": 80,  # 参与综述生成的最大论文数
}

# ============
# 输出配置
# ============

OUTPUT_CONFIG = {
    "output_dir": "output",       # 输出目录
    "review_filename": "review.md",
    "comparison_table": "comparison_table.csv",
    "reference_file": "references.bib",
    "report_file": "quality_report.md",
}
