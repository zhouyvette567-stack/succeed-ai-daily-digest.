#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日AI资讯爬虫 - 升级版
自动抓取AI相关内容，翻译为中文，生成犀利锐评，并生成JSON格式的日报
"""

import json
import os
import requests
from datetime import datetime
from pathlib import Path

# 配置
DATA_DIR = Path(__file__).parent.parent / "data"
DOCS_DATA_DIR = Path(__file__).parent.parent / "docs" / "data"

# 确保目录存在
DATA_DIR.mkdir(exist_ok=True)
DOCS_DATA_DIR.mkdir(exist_ok=True)


def translate_to_chinese(text, max_retries=3):
    """
    使用免费翻译API将文本翻译为中文
    优先使用MyMemory Translation API（免费，无需密钥）
    """
    if not text or text == "No description available":
        return "暂无描述"

    # 清理文本
    text = text.strip()
    if len(text) < 5:
        return text

    # 尝试使用MyMemory Translation API（免费，每天5000字符）
    try:
        url = "https://api.mymemory.translated.net/get"
        params = {
            "q": text[:500],  # 限制长度
            "langpair": "en|zh-CN"
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("responseStatus") == 200:
            translated = data.get("responseData", {}).get("translatedText", "")
            if translated and translated != text:
                return translated
    except Exception as e:
        print(f"翻译失败（MyMemory）: {e}")

    # 备用方案：使用Google Translate免费接口（无需密钥）
    try:
        # Google Translate的免费接口
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": "en",
            "tl": "zh-CN",
            "dt": "t",
            "q": text[:500]
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        result = response.json()

        # 解析Google Translate返回的结果
        translated = ""
        for item in result[0]:
            if item and item[0]:
                translated += item[0]

        if translated:
            return translated
    except Exception as e:
        print(f"翻译失败（Google）: {e}")

    # 如果都失败，返回原文
    return text


def generate_comment(title, description):
    """
    生成犀利锐评 - 使用模板+关键词匹配（完全免费，无需API密钥）
    后续可升级为LLM API（需要密钥）
    """
    # 关键词匹配锐评模板
    comment_templates = {
        "llama": "Meta又开源大杀器，这次能不能干翻GPT？开源社区狂欢，闭源厂商瑟瑟发抖。",
        "gpt": "OpenAI又放大招，这次是真是假？等实测，别急着跪。",
        "claude": "Anthropic的良心之作，至少不会胡说八道，但价格嘛...你懂的。",
        "hugging": "Hugging Face就是AI界的GitHub，没它你可能还在手搓模型。",
        "github": "星标几万又如何？能跑起来才是硬道理，先看看issue再说。",
        "arxiv": "论文看着高大上，代码开源了吗？别光说不练。",
        "model": "新模型又来了，基准测试刷得飞起，实际用用再说吧。",
        "api": "API上线了，准备好钱包了吗？按token计费，用得起算我输。",
        "vision": "多模态是趋势，但别指望它真的'看懂'了，能分清猫狗就算成功。",
        "agent": "AI Agent喊了这么久，有几个真正好用的？先解决幻觉问题吧。",
        "chip": "芯片战打得火热，可你买到货了吗？涨价倒是挺快。",
        "regulation": "监管来了，好事！至少能管管那些夸大宣传的，让行业清醒清醒。",
        "default_tech": "技术看着牛，落地才知道。先别吹，等等实测数据。",
        "default_paper": "论文值不值，看代码和实验复现。光看摘要都是纸上谈兵。",
        "default_product": "新产品发布，先观望。AI产品死亡率高，等它活过半年再说。",
        "default_hot": "热点蹭得飞起，实际价值几何？让子弹飞一会儿。"
    }

    title_lower = title.lower()
    desc_lower = description.lower()

    # 关键词匹配
    for keyword, comment in comment_templates.items():
        if keyword in title_lower or keyword in desc_lower:
            return comment

    # 根据分类返回默认锐评
    if "llama" in title_lower or "gpt" in title_lower or "claude" in title_lower:
        return comment_templates["default_tech"]
    elif "arxiv" in title_lower or "paper" in title_lower or "research" in title_lower:
        return comment_templates["default_paper"]
    elif "model" in title_lower or "hugging" in title_lower:
        return comment_templates["default_product"]
    else:
        return comment_templates["default_hot"]


def fetch_github_trending():
    """获取GitHub Trending AI项目"""
    try:
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
            title = item["name"]
            summary = item["description"] or "No description available"

            # 翻译
            title_cn = translate_to_chinese(title)
            summary_cn = translate_to_chinese(summary)

            # 生成锐评
            comment = generate_comment(title, summary)

            results.append({
                "title": title,
                "title_cn": title_cn,
                "summary": summary,
                "summary_cn": summary_cn,
                "comment": comment,
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
        url = "http://export.arxiv.org/api/query"
        params = {
            "search_query": "cat:cs.AI OR cat:cs.LG OR cat:cs.CV",
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": 10
        }
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()

        import xml.etree.ElementTree as ET
        root = ET.fromstring(response.content)

        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        results = []

        for entry in root.findall('atom:entry', ns)[:5]:
            title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
            summary = entry.find('atom:summary', ns).text.strip().replace('\n', ' ')[:300]
            link = entry.find('atom:id', ns).text
            published = entry.find('atom:published', ns).text[:10]

            # 翻译
            title_cn = translate_to_chinese(title)
            summary_cn = translate_to_chinese(summary)

            # 生成锐评
            comment = generate_comment(title, summary)

            results.append({
                "title": title,
                "title_cn": title_cn,
                "summary": summary + "...",
                "summary_cn": summary_cn + "...",
                "comment": comment,
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
            title = item.get("modelId", "Unknown Model")
            summary = f"作者: {item.get('author', 'Unknown')}, 下载量: {item.get('downloads', 0)}"

            # 翻译
            title_cn = translate_to_chinese(title)
            summary_cn = translate_to_chinese(summary)

            # 生成锐评
            comment = generate_comment(title, summary)

            results.append({
                "title": title,
                "title_cn": title_cn,
                "summary": summary,
                "summary_cn": summary_cn,
                "comment": comment,
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
            "title_cn": item["title_cn"],
            "summary": item["summary"],
            "summary_cn": item["summary_cn"],
            "comment": item["comment"],
            "url": item["url"],
            "date": today
        })

    # AI论文 (3条) - 来自arXiv
    paper_items = fetch_arxiv_papers()
    for item in paper_items[:3]:
        report["items"].append({
            "category": "AI论文",
            "title": item["title"],
            "title_cn": item["title_cn"],
            "summary": item["summary"],
            "summary_cn": item["summary_cn"],
            "comment": item["comment"],
            "url": item["url"],
            "date": item.get("published", today)
        })

    # 新产品 (3条) - 来自Hugging Face
    hf_items = fetch_huggingface_models()
    for item in hf_items[:3]:
        report["items"].append({
            "category": "新产品",
            "title": item["title"],
            "title_cn": item["title_cn"],
            "summary": item["summary"],
            "summary_cn": item["summary_cn"],
            "comment": item["comment"],
            "url": item["url"],
            "date": today
        })

    # 行业热点 (2条) - 使用GitHub Trending补充
    remaining_tech = tech_items[2:4] if len(tech_items) > 2 else tech_items[:2]
    for item in remaining_tech[:2]:
        report["items"].append({
            "category": "行业热点",
            "title": item["title"],
            "title_cn": item["title_cn"],
            "summary": item["summary"],
            "summary_cn": item["summary_cn"],
            "comment": item["comment"],
            "url": item["url"],
            "date": today
        })

    # 如果条目不足10条，用备用数据补充
    while len(report["items"]) < 10:
        report["items"].append({
            "category": "行业热点",
            "title": f"AI行业动态 {len(report['items']) + 1}",
            "title_cn": f"AI行业动态 {len(report['items']) + 1}",
            "summary": "今日AI领域持续快速发展，多项新技术和产品值得关注。",
            "summary_cn": "今日AI领域持续快速发展，多项新技术和产品值得关注。",
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
    print("开始生成每日AI资讯报告（中文翻译+锐评版）...")
    report = generate_daily_report()
    save_report(report)
    print("报告生成完成！")


if __name__ == "__main__":
    main()
