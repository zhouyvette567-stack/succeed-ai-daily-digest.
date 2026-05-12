#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日AI资讯爬虫
自动抓取AI相关内容并生成JSON格式的日报
"""

import json
import os
from datetime import datetime, timedelta
import requests
from pathlib import Path

# 配置
DATA_DIR = Path(__file__).parent.parent / "data"
DOCS_DATA_DIR = Path(__file__).parent.parent / "docs" / "data"

# 确保目录存在
DATA_DIR.mkdir(exist_ok=True)
DOCS_DATA_DIR.mkdir(exist_ok=True)


def fetch_github_trending():
    """获取GitHub Trending AI项目"""
    try:
        # 使用GitHub API获取AI相关trending repos
        url = "https://api.github.com/search/repositories"
        params = {
            "q": "topic:ai topic:machine-learning sort:stars-desc",
            "sort": "stars",
            "order": "desc",
            "per_page": 10
        }
        headers = {"Accept": "application/vnd.github.v3+json"}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("items", [])[:5]:
            results.append({
                "title": item["name"],
                "summary": item["description"] or "No description available",
                "url": item["html_url"],
                "stars": item["stargazers_count"]
            })
        return results
    except Exception as e:
        print(f"GitHub Trending抓取失败: {e}")
        return []


def fetch_arxiv_papers():
    """获取arXiv最新AI论文"""
    try:
        # 使用arXiv API
        url = "http://export.arxiv.org/api/query"
        params = {
            "search_query": "cat:cs.AI OR cat:cs.LG OR cat:cs.CV",
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": 10
        }
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()

        # 简单解析XML
        import xml.etree.ElementTree as ET
        root = ET.fromstring(response.content)

        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        results = []

        for entry in root.findall('atom:entry', ns)[:5]:
            title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
            summary = entry.find('atom:summary', ns).text.strip().replace('\n', ' ')[:200]
            link = entry.find('atom:id', ns).text
            published = entry.find('atom:published', ns).text[:10]

            results.append({
                "title": title,
                "summary": summary + "...",
                "url": link,
                "published": published
            })
        return results
    except Exception as e:
        print(f"arXiv论文抓取失败: {e}")
        return []


def fetch_huggingface_models():
    """获取Hugging Face热门模型"""
    try:
        url = "https://huggingface.co/api/models"
        params = {
            "sort": "downloads",
            "direction": "-1",
            "limit": 10
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data[:5]:
            results.append({
                "title": item.get("modelId", "Unknown Model"),
                "summary": f"作者: {item.get('author', 'Unknown')}, 下载量: {item.get('downloads', 0)}",
                "url": f"https://huggingface.co/{item.get('modelId', '')}",
                "downloads": item.get("downloads", 0)
            })
        return results
    except Exception as e:
        print(f"Hugging Face模型抓取失败: {e}")
        return []


def generate_daily_report():
    """生成每日报告"""
    today = datetime.now().strftime("%Y-%m-%d")
    report = {
        "date": today,
        "items": []
    }

    # 技术动态 (2条) - 来自GitHub Trending
    tech_items = fetch_github_trending()
    for item in tech_items[:2]:
        report["items"].append({
            "category": "技术动态",
            "title": item["title"],
            "summary": item["summary"],
            "url": item["url"],
            "date": today
        })

    # AI论文 (3条) - 来自arXiv
    paper_items = fetch_arxiv_papers()
    for item in paper_items[:3]:
        report["items"].append({
            "category": "AI论文",
            "title": item["title"],
            "summary": item["summary"],
            "url": item["url"],
            "date": item.get("published", today)
        })

    # 新产品 (3条) - 混合来源
    hf_items = fetch_huggingface_models()
    # 使用HuggingFace数据作为新产品来源
    for item in hf_items[:3]:
        report["items"].append({
            "category": "新产品",
            "title": item["title"],
            "summary": item["summary"],
            "url": item["url"],
            "date": today
        })

    # 行业热点 (2条) - 使用GitHub Trending补充
    remaining_tech = tech_items[2:4] if len(tech_items) > 2 else tech_items[:2]
    for item in remaining_tech[:2]:
        report["items"].append({
            "category": "行业热点",
            "title": item["title"],
            "summary": item["summary"],
            "url": item["url"],
            "date": today
        })

    # 如果条目不足10条，用备用数据补充
    while len(report["items"]) < 10:
        report["items"].append({
            "category": "行业热点",
            "title": f"AI行业动态 {len(report['items']) + 1}",
            "summary": "今日AI领域持续快速发展，多项新技术和产品值得关注。",
            "url": "https://github.com/topics/artificial-intelligence",
            "date": today
        })

    return report


def save_report(report):
    """保存报告到JSON文件"""
    date_str = report["date"]
    filename = f"{date_str}.json"

    # 保存到data目录
    data_path = DATA_DIR / filename
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # 复制到docs/data目录（用于GitHub Pages）
    docs_path = DOCS_DATA_DIR / filename
    with open(docs_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # 更新latest.json
    latest_path = DOCS_DATA_DIR / "latest.json"
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # 更新索引文件
    update_index(date_str)

    print(f"报告已保存: {data_path}")
    return data_path


def update_index(current_date):
    """更新报告索引"""
    index_path = DOCS_DATA_DIR / "index.json"

    # 读取现有索引
    if index_path.exists():
        with open(index_path, "r", encoding="utf-8") as f:
            index = json.load(f)
    else:
        index = {"dates": []}

    # 添加新日期（如果不存在）
    if current_date not in index["dates"]:
        index["dates"].insert(0, current_date)
        index["dates"].sort(reverse=True)

    # 保存索引
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"索引已更新: {index_path}")


def main():
    """主函数"""
    print("开始生成每日AI资讯报告...")
    report = generate_daily_report()
    save_report(report)
    print("报告生成完成！")


if __name__ == "__main__":
    main()
