# ScholarReviewer AI

**学术文献综述智能体** — 基于 Multi-Agent 架构的自动化文献综述生成系统。

输入一个研究主题，系统自动完成：**文献采集 → 论文解析 → 综合分析 → 综述生成 → 质量审查**，输出完整的综述文档和多种分析报告。

---

## 功能特性

| 特性 | 说明 |
|------|------|
| **多源检索** | 支持 arXiv + PubMed 双数据库，自动去重合并 |
| **全文解析** | 可选 PyMuPDF 深度解析 PDF 内容 |
| **多LLM后端** | OpenAI / 通义千问 / DeepSeek / 降级模式 |
| **多引用格式** | IEEE / APA / BibTeX / MLA |
| **质量审查** | 自动检查逻辑自洽性、数据完整性、引用准确性 |
| **多种输出** | 综述 Markdown、对比表格、趋势分析、参考文献 |

---

## 安装

```bash
git clone https://github.com/Wenyu-one/scholar_reviewer.git
cd scholar_reviewer
pip install -r requirements.txt
```

---

## 快速开始

### 命令行模式

```bash
# 基础用法
python main.py --topic "large language model" --max-papers 30

# 指定引用格式和全文解析
python main.py --topic "retrieval augmented generation" --citation-style bibtex --use-full-text

# 仅检索 arXiv
python main.py --topic "transformer attention" --arxiv-only --max-papers 50
```

### 交互模式

```bash
python main.py --interactive
```

---

## 配置

编辑 `config.py` 中的 `LLM_CONFIG`：

```python
# OpenAI
LLM_CONFIG = {
    "provider": "openai",
    "model": "gpt-4o",
    "api_key": "your-key-here",
}

# 通义千问（阿里云）
LLM_CONFIG = {
    "provider": "qwen",
    "model": "qwen-max",
    "api_key": "your-key-here",
}

# DeepSeek
LLM_CONFIG = {
    "provider": "openai",
    "model": "deepseek-chat",
    "api_key": "your-key-here",
    "base_url": "https://api.deepseek.com/v1",
}
```

> 无 API Key 时，系统自动降级为规则提取模式，仍可生成基础内容。

---

## 输出文件

运行后在 `output/` 目录下生成：

| 文件 | 说明 |
|------|------|
| `review.md` | 完整综述草稿（Markdown格式） |
| `quality_report.md` | 质量审查报告 |
| `method_comparison_table.md` | 方法对比表 |
| `result_comparison_table.md` | 实验结果对比表 |
| `trend_analysis.md` | 研究趋势分析 |
| `papers.json` | 所有论文元数据（JSON） |
| `references.txt` | 参考文献列表 |

---

## 系统架构

```
┌─────────────────────────────────────────────┐
│           ScholarReviewerOrchestrator        │
│              （主协调器）                      │
├─────────────────────────────────────────────┤
│                                             │
│  Phase 1 ──→ Phase 2 ──→ Phase 3           │
│  文献采集      论文解析      综合分析        │
│                                             │
│  Phase 4 ──→ Phase 5                       │
│  综述生成      质量审查                      │
│                                             │
└─────────────────────────────────────────────┘
```

- **Phase 1**：arXiv API + PubMed E-utilities 并行检索
- **Phase 2**：PyMuPDF 解析 PDF，提取摘要/方法/结果
- **Phase 3**：LLM 跨论文综合分析，识别关系和趋势
- **Phase 4**：按模板生成综述，批量生成引用格式
- **Phase 5**：质量审查，输出改进建议

---

## 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--topic`, `-t` | 综述主题（关键词） | 必填 |
| `--max-papers`, `-m` | 最大检索论文数 | 50 |
| `--citation-style`, `-c` | 引用格式 | ieee |
| `--use-full-text` | 启用全文解析 | 否（仅摘要） |
| `--output-dir`, `-o` | 输出目录 | output |
| `--interactive`, `-i` | 交互模式 | 否 |
| `--arxiv-only` | 仅使用 arXiv | 否 |

---

## 项目结构

```
scholar_reviewer/
├── main.py                      # 主入口
├── config.py                    # 配置文件
├── requirements.txt              # 依赖列表
├── agents/
│   ├── orchestrator.py         # 主协调器
│   ├── literature_collector.py  # 文献采集
│   ├── paper_parser.py         # 论文解析
│   ├── analyzer.py             # 综合分析
│   ├── review_generator.py      # 综述生成
│   └── quality_reviewer.py      # 质量审查
├── utils/
│   └── llm_utils.py             # LLM 调用封装
└── templates/
    └── review_template.md       # 综述模板
```

---

## 环境要求

- Python 3.10+
- 网络访问 arXiv / PubMed（需代理或国际网络）

---

## License

MIT License