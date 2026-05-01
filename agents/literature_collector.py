"""
Phase 1: 文献采集 Agent
对接 arXiv API，批量检索相关文献，输出结构化文献列表。
MVP：先实现 arXiv，后续加入 PubMed。
"""

import arxiv
import os
import json
from typing import List, Dict, Any, Optional


class LiteratureCollectorAgent:
    """文献采集 Agent：从学术数据库检索论文"""

    def __init__(self, max_results: int = 50, download_dir: str = "papers"):
        self.max_results = max_results
        self.download_dir = download_dir
        os.makedirs(download_dir, exist_ok=True)

    def collect_arxiv(self,
                      query: str,
                      max_results: Optional[int] = None,
                      sort_by: str = "relevance") -> List[Dict[str, Any]]:
        """
        从 arXiv 检索论文

        :param query: 搜索关键词（如 "large language model"）
        :param max_results: 最大结果数（默认使用 self.max_results）
        :param sort_by: 排序方式（"relevance" / "submittedDate" / "lastUpdatedDate"）
        :return: 结构化论文列表
        """
        max_results = max_results or self.max_results

        # 排序映射
        sort_map = {
            "relevance": arxiv.SortCriterion.Relevance,
            "submittedDate": arxiv.SortCriterion.SubmittedDate,
            "lastUpdatedDate": arxiv.SortCriterion.LastUpdatedDate,
        }
        sort_criterion = sort_map.get(sort_by, arxiv.SortCriterion.Relevance)

        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=sort_criterion,
        )

        results = []
        print(f"  🔍 正在从 arXiv 检索：{query}")
        for result in search.results():
            paper = self._parse_arxiv_result(result)
            results.append(paper)
            print(f"    ✓ {paper['id']}: {paper['title'][:60]}...")

        print(f"  ✅ arXiv 检索完成，共 {len(results)} 篇论文")
        return results

    def _parse_arxiv_result(self, result) -> Dict[str, Any]:
        """解析单篇 arXiv 论文结果为结构化字典"""
        return {
            "id": result.entry_id.split("/abs/")[-1],
            "title": result.title,
            "authors": [str(a) for a in result.authors],
            "abstract": result.summary,
            "published": str(result.published.date()) if result.published else "",
            "updated": str(result.updated.date()) if result.updated else "",
            "categories": result.categories,
            "pdf_url": result.pdf_url,
            "url": result.entry_id,
            "source": "arxiv",
        }

    def collect_pubmed(self,
                      query: str,
                      max_results: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        从 PubMed 检索论文（使用 Entrez API，无需 API Key）
        MVP 版本：基础实现，后续增强
        """
        max_results = max_results or self.max_results
        print(f"  🔍 正在从 PubMed 检索：{query}")

        try:
            import requests
            from bs4 import BeautifulSoup

            # 第一步：搜索获取 ID 列表
            search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            search_params = {
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "xml",
            }
            resp = requests.get(search_url, params=search_params, timeout=15)
            soup = BeautifulSoup(resp.content, "xml")
            id_list = [id_tag.text for id_tag in soup.find_all("Id")]

            if not id_list:
                print("  ⚠️  PubMed 未检索到结果")
                return []

            # 第二步：获取详细信息
            fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
            fetch_params = {
                "db": "pubmed",
                "id": ",".join(id_list),
                "retmode": "xml",
            }
            resp = requests.get(fetch_url, params=fetch_params, timeout=30)
            soup = BeautifulSoup(resp.content, "xml")

            results = []
            for article in soup.find_all("PubmedArticle"):
                paper = self._parse_pubmed_article(article)
                if paper:
                    results.append(paper)
                    print(f"    ✓ PMID:{paper['id']}: {paper['title'][:60]}...")

            print(f"  ✅ PubMed 检索完成，共 {len(results)} 篇论文")
            return results

        except ImportError:
            print("  ⚠️  未安装 beautifulsoup4，跳过 PubMed 检索")
            print("      请运行：pip install beautifulsoup4")
            return []
        except Exception as e:
            print(f"  ⚠️  PubMed 检索失败：{e}")
            return []

    def _parse_pubmed_article(self, article) -> Optional[Dict[str, Any]]:
        """解析单篇 PubMed 论文"""
        try:
            # 提取 PMID
            pmid_tag = article.find("PMID")
            pmid = pmid_tag.text if pmid_tag else ""

            # 提取标题
            title_tag = article.find("ArticleTitle")
            title = title_tag.text if title_tag else "Unknown Title"

            # 提取作者
            authors = []
            for author_tag in article.find_all("Author")[:10]:
                lastname = author_tag.find("LastName")
                forename = author_tag.find("ForeName")
                if lastname:
                    name = lastname.text
                    if forename:
                        name = forename.text + " " + name
                    authors.append(name)

            # 提取摘要
            abstract_parts = article.find_all("AbstractText")
            abstract = " ".join([p.text for p in abstract_parts]) if abstract_parts else ""

            # 提取发表日期
            pub_date = article.find("PubDate")
            year = ""
            if pub_date:
                year_tag = pub_date.find("Year")
                if year_tag:
                    year = year_tag.text

            return {
                "id": pmid,
                "title": title,
                "authors": authors,
                "abstract": abstract,
                "published": year,
                "updated": "",
                "categories": [],
                "pdf_url": "",
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "source": "pubmed",
            }
        except Exception as e:
            print(f"    ⚠️  解析 PubMed 论文失败：{e}")
            return None

    def filter_by_similarity(self,
                            papers: List[Dict[str, Any]],
                            query: str,
                            threshold: float = 0.3) -> List[Dict[str, Any]]:
        """
        基于摘要相似度过滤低相关度论文（使用简单关键词匹配，MVP版本）
        后续可升级为 embedding 相似度。
        """
        print(f"  🔧  正在过滤低相关度论文（阈值：{threshold}）...")

        # 简单关键词匹配评分
        query_words = set(query.lower().split())

        filtered = []
        for paper in papers:
            abstract = paper.get("abstract", "").lower()
            title = paper.get("title", "").lower()

            # 计算关键词命中率
            hit_count = sum(1 for w in query_words if w in abstract or w in title)
            score = hit_count / max(len(query_words), 1)

            paper["_relevance_score"] = round(score, 3)
            if score >= threshold:
                filtered.append(paper)

        print(f"  ✅ 过滤完成：{len(papers)} → {len(filtered)} 篇（去除 {len(papers) - len(filtered)} 篇低相关度论文）")
        return filtered

    def save_results(self, papers: List[Dict[str, Any]], output_path: str):
        """保存检索结果到 JSON 文件"""
        import os
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(papers, f, ensure_ascii=False, indent=2)
        print(f"  💾 检索结果已保存：{output_path}（{len(papers)} 篇）")
