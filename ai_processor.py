import requests
import logging
from config import BACKEND_URL

def ai_extract_and_push(email_content):
    """
    AI 字段提取预设函数
    """
    # 1. 这里未来接入 AI (如 DeepSeek)
    # 模拟提取到的字段：App名称、违规类型、原始正文摘要
    extracted_data = {
        "app_name": "通过 AI 提取的 App 名称",
        "issue_type": "Policy Violation",
        "detail": email_content[:200]
    }
    
    logging.info(f"🧠 AI 提取完成: {extracted_data['app_name']}")

    # 2. 推送到指定后台
    if BACKEND_URL:
        try:
            # 实际部署时取消下面注释
            # requests.post(BACKEND_URL, json=extracted_data, timeout=10)
            logging.info("🚀 数据已同步至指定后台")
        except Exception as e:
            logging.error(f"❌ 后台同步失败: {e}")
            
    return extracted_data