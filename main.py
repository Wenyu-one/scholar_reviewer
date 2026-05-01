#!/usr/bin/env python3
"""
ScholarReviewer AI - 学术文献综述智能体
主入口文件

使用方法：
  python main.py --topic "large language model" --max-papers 30
  python main.py --topic "transformer attention mechanism" --use-full-text
  python main.py --interactive  # 交互模式
"""

import argparse
import sys
import os

# 确保项目根目录在 sys.path 中
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def main():
    parser = argparse.ArgumentParser(
        description="ScholarReviewer AI - 学术文献综述智能体",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python main.py --topic "large language model" --max-papers 30
  python main.py --topic " retrieval augmented generation" --citation-style bibtex
  python main.py --interactive

输出文件位于 output/ 目录：
  - review.md              综述草稿（Markdown）
  - quality_report.md       质量审查报告
  - method_comparison_table.md  方法对比表
  - result_comparison_table.md  实验结果对比表
  - trend_analysis.md        趋势分析
  - papers.json             论文列表（JSON）
  - references.txt          参考文献列表
""",
    )

    parser.add_argument(
        "--topic", "-t",
        type=str,
        help="综述主题（关键词，如 'large language model'）",
    )
    parser.add_argument(
        "--max-papers", "-m",
        type=int,
        default=50,
        help="最大检索论文数（默认 50）",
    )
    parser.add_argument(
        "--use-full-text",
        action="store_true",
        help="启用全文解析（需要安装 PyMuPDF，且会显著变慢）",
    )
    parser.add_argument(
        "--citation-style", "-c",
        type=str,
        default="ieee",
        choices=["ieee", "apa", "bibtex", "mla"],
        help="引用格式（默认 ieee）",
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default="output",
        help="输出目录（默认 output/）",
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="交互模式：逐步确认每个阶段",
    )
    parser.add_argument(
        "--arxiv-only",
        action="store_true",
        help="仅使用 arXiv（跳过 PubMed）",
    )

    args = parser.parse_args()

    # 交互模式或直接运行
    if args.interactive:
        return run_interactive()

    if not args.topic:
        print("❌ 请提供综述主题！")
        print("\n使用 --help 查看帮助，或使用 --interactive 进入交互模式")
        return 1

    return run_pipeline(args)


def run_pipeline(args):
    """执行完整流程"""
    from agents.orchestrator import ScholarReviewerOrchestrator

    print("\n" + "=" * 60)
    print("  ScholarReviewer AI  学术文献综述智能体")
    print("=" * 60)

    # 检查 LLM 配置
    check_llm_config()

    orchestrator = ScholarReviewerOrchestrator(
        topic=args.topic,
        max_papers=args.max_papers,
        use_full_text=args.use_full_text,
        citation_style=args.citation_style,
        output_dir=args.output_dir,
    )

    try:
        result = orchestrator.run()
        print(f"\n📂 所有文件已保存至：{os.path.abspath(args.output_dir)}")
        print(f"   请打开 {args.output_dir}/review.md 查看综述草稿")
        return 0
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断，已保存当前进度")
        return 1
    except Exception as e:
        print(f"\n❌ 运行出错：{e}")
        import traceback
        traceback.print_exc()
        return 1


def run_interactive():
    """交互模式：逐步确认"""
    print("\n" + "=" * 60)
    print("  ScholarReviewer AI - 交互模式")
    print("=" * 60)

    topic = input("\n① 请输入综述主题（关键词）：").strip()
    if not topic:
        print("❌ 主题不能为空！")
        return 1

    max_papers_str = input("② 最大检索论文数（默认 50，回车跳过）：").strip()
    max_papers = 50
    if max_papers_str.isdigit():
        max_papers = int(max_papers_str)

    citation_style = input("③ 引用格式（ieee/apa/bibtex/mla，默认 ieee）：").strip()
    if citation_style not in ("ieee", "apa", "bibtex", "mla"):
        citation_style = "ieee"

    use_full_text = input("④ 是否启用全文解析（y/N，需要 PyMuPDF）：").strip().lower()
    use_full_text = use_full_text == "y"

    output_dir = input("⑤ 输出目录（默认 output，回车跳过）：").strip()
    if not output_dir:
        output_dir = "output"

    print(f"\n{'─' * 60}")
    print("  确认配置：")
    print(f"  主题：{topic}")
    print(f"  最大论文数：{max_papers}")
    print(f"  引用格式：{citation_style}")
    print(f"  全文解析：{'是' if use_full_text else '否（仅摘要）'}")
    print(f"  输出目录：{output_dir}")
    print(f"{'─' * 60}\n")

    confirm = input("确认开始？（y/N）：").strip().lower()
    if confirm != "y":
        print("已取消。")
        return 0

    # 执行
    from agents.orchestrator import ScholarReviewerOrchestrator

    check_llm_config()

    orchestrator = ScholarReviewerOrchestrator(
        topic=topic,
        max_papers=max_papers,
        use_full_text=use_full_text,
        citation_style=citation_style,
        output_dir=output_dir,
    )

    try:
        result = orchestrator.run()
        print(f"\n📂 所有文件已保存至：{os.path.abspath(output_dir)}")
        return 0
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        return 1
    except Exception as e:
        print(f"\n❌ 运行出错：{e}")
        import traceback
        traceback.print_exc()
        return 1


def check_llm_config():
    """检查 LLM 配置，给出提示"""
    try:
        from config import LLM_CONFIG
        provider = LLM_CONFIG.get("provider", "mock")
        api_key = LLM_CONFIG.get("api_key", "")

        if provider == "mock" or not api_key:
            print("\n⚠️  未配置 LLM API Key！")
            print("   当前为「降级模式」，仅使用规则生成基础内容。")
            print("   如需完整功能，请编辑 config.py 配置 LLM_CONFIG。\n")
        else:
            print(f"\n✅ LLM 已配置：{provider} / {LLM_CONFIG.get('model', '')}\n")
    except ImportError:
        print("\n⚠️  未找到 config.py，使用默认降级模式\n")


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
