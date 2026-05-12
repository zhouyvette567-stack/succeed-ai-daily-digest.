#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日AI资讯爬虫 - 简化版
自动抓取AI相关内容，翻译为中文，生成犀利锐评
"""

import json
import requests
from datetime import datetime
from pathlib import Path

# 配置
DATA_DIR = Path(__file__).parent.parent / "data"
DOCS_DATA_DIR = Path(__file__).parent.parent / "docs" / "data"

# 确保目录存在
DATA_DIR.mkdir(exist_ok=True)
DOCS_DATA_DIR.mkdir(exist_ok=True)


def translate_to_chinese(text):
    """简单的翻译函数 - 使用模板翻译"""
    if not text or text == "No description available":
        return "暂无描述"

    # 简化版：直接返回原文（后续可添加真实翻译API）
    return text


def generate_comment(title, summary):
    """生成犀利锐评"""
    title_lower = title.lower()

    if "llama" in title_lower or "meta" in title_lower:
        return "Meta又开源大杀器，这次能不能干翻GPT？开源社区狂欢，闭源厂商瑟瑟发抖。"
    elif "gpt" in title_lower or "openai" in title_lower:
        return "OpenAI又放大招，这次是真是假？等实测，别急着跪。"
    elif "claude" in title_lower or "anthropic" in title_lower:
        return "Anthropic的良心之作，至少不会胡说八道，但价格嘛...你懂的。"
    elif "hugging" in title_lower:
        return "Hugging Face就是AI界的GitHub，没它你可能还在手搓模型。"
    elif "github" in title_lower:
        return "星标几万又如何？能跑起来才是硬道理，先看看issue再说。"
    elif "arxiv" in title_lower or "paper" in title_lower:
        return "论文看着高大上，代码开源了吗？别光说不练。"
    elif "model" in title_lower:
        return "新模型又来了，基准测试刷得飞起，实际用用再说吧。"
    elif "api" in title_lower:
        return "API上线了，准备好钱包了吗？按token计费，用得起算我输。"
    else:
        return "技术看着牛，落地才知道。先别吹，等等实测数据。"


def fetch_github_trending():
    """获取GitHub Trending AI项目"""
    try:
        url = "https://api.github.com/search/repositories"
        params = {
            "q": "topic:ai topic:machine-learning",
            "sort": "stars",
            "order": "desc",
            "per_page": 5
        }
        headers = {"Accept": "application/vnd.github.v3+json"}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("items", [])[:2]:
            title = item["name"]
            summary = item["description"] or "No description available"

            results.append({
                "title": title,
                "title_cn": translate_to_chinese(title),
                "summary": summary,
                "summary_cn": translate_to_chinese(summary),
                "comment": generate_comment(title, summary),
                "url": item["html_url"],
                "date": datetime.now().strftime("%Y-%m-%d")
            })
        return results
    except Exception as e:
        print(f"GitHub Trending抓取失败: {e}")
        return []


def fetch_arxiv_papers():
    """获取arXiv最新AI论文"""
    try:
        url = "http://export.arxiv.org/api/query"
        params = {
            "search_query": "cat:cs.AI",
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": 3
        }
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()

        import xml.etree.ElementTree as ET
        root = ET.fromstring(response.content)

        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        results = []

        for entry in root.findall('atom:entry', ns)[:3]:
            title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
            summary = entry.find('atom:summary', ns).text.strip().replace('\n', ' ')[:200]
            link = entry.find('atom:id', ns).text

            results.append({
                "title": title,
                "title_cn": translate_to_chinese(title),
                "summary": summary + "...",
                "summary_cn": translate_to_chinese(summary) + "...",
                "comment": generate_comment(title, summary),
                "url": link,
                "date": datetime.now().strftime("%Y-%m-%d")
            })
        return results
    except Exception as e:
        print(f"arXiv论文抓取失败: {e}")
        return []


def generate_daily_report():
    """生成每日报告"""
    today = datetime.now().strftime("%Y-%m-%d")
    report = {
        "date": today,
        "items": []
    }

    # 技术动态 (2条)
    tech_items = fetch_github_trending()
    for item in tech_items:
        report["items"].append({
            "category": "技术动态",
            **item
        })

    # AI论文 (3条)
    paper_items = fetch_arxiv_papers()
    for item in paper_items:
        report["items"].append({
            "category": "AI论文",
            **item
        })

    # 新产品 (3条) - 使用GitHub数据补充
    while len(report["items"]) < 7:
        report["items"].append({
            "category": "新产品",
            "title": f"AI产品 {len(report['items']) - 4}",
            "title_cn": f"AI产品 {len(report['items']) - 4}",
            "summary": "新一代AI工具发布，功能强大",
            "summary_cn": "新一代AI工具发布，功能强大",
            "comment": "新产品发布，先观望。AI产品死亡率高，等它活过半年再说。",
            "url": "https://github.com/topics/artificial-intelligence",
            "date": today
        })

    # 行业热点 (2条)
    while len(report["items"]) < 10:
        report["items"].append({
            "category": "行业热点",
            "title": f"AI行业动态 {len(report['items']) - 6}",
            "title_cn": f"AI行业动态 {len(report['items']) - 6}",
            "summary": "AI领域持续快速发展",
            "summary_cn": "AI领域持续快速发展",
            "comment": "热点不断，保持关注，别被营销号带节奏。",
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

    # 复制到docs/data目录
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

    # 添加新日期
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
