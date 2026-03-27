# -*- coding: utf-8 -*-
"""包名提取模块：使用 Claude 从 Google 开发者邮件中提取包名，并在飞书多维表格中匹配"""
import logging
import json
import anthropic
from config import CLAUDE_API_KEY
from feishu_utils import search_package_in_bitable

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

EXTRACT_PROMPT = """你是一个专门分析 Google Play 开发者邮件的助手。
请从以下邮件内容中提取 Google Play 包名，仅返回 JSON，不要有任何其他文字或 markdown 代码块。

包名格式为反向域名，如 com.example.app，可能出现在括号内：
- 英文邮件："your app, App Name (com.example.app), we found..."
- 中文邮件："您的应用"App Name"(com.example.app) 时"
- 中文全角括号："审核您的应用"App Name"（com.example.app）时"

需要提取的字段（没有则为 null）：
- google_package_name

仅返回 JSON，示例：
{"google_package_name": "com.example.app"}

邮件主题：{subject}

邮件正文：
{body}
"""


def extract_package_name(subject: str, body: str) -> str | None:
    """调用 Claude 从邮件中提取 Google Play 包名。"""
    try:
        prompt = EXTRACT_PROMPT.format(subject=subject, body=body[:3000])
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=128,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw.strip())
        package_name = result.get("google_package_name")
        if package_name:
            logging.info(f"🤖 Claude 提取到包名: {package_name}")
        else:
            logging.info("ℹ️ Claude 未提取到包名")
        return package_name
    except Exception as e:
        logging.error(f"❌ Claude 提取异常: {e}")
        return None


def process_email_for_matching(subject: str, body: str) -> bool:
    """
    对外统一入口：Claude 提取包名 → 飞书多维表格搜索匹配。
    匹配成功返回 True，否则返回 False。
    """
    package_name = extract_package_name(subject, body)
    if not package_name:
        return False
    return search_package_in_bitable(package_name)