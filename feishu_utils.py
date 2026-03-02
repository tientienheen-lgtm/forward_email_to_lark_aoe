# -*- coding: utf-8 -*-
"""飞书相关工具封装"""
import requests
import json
import time
import logging
from config import *

_TENANT_ACCESS_TOKEN = ""
_TOKEN_EXPIRE_TIME = 0
_EMAIL_PROGRAM_MAP_CACHE = {}
_LAST_BITABLE_READ_TIME = 0


def get_feishu_token():
    global _TENANT_ACCESS_TOKEN, _TOKEN_EXPIRE_TIME
    current_time = time.time()

    if _TENANT_ACCESS_TOKEN and current_time < _TOKEN_EXPIRE_TIME - 60:
        return _TENANT_ACCESS_TOKEN

    try:
        logging.debug("⚙️ 刷新飞书 Token...")
        resp = requests.post(
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal/",
            headers={"Content-Type": "application/json"},
            json={"app_id": APP_ID, "app_secret": APP_SECRET},
            timeout=10
        )
        result = resp.json()
        if result.get("code") == 0:
            _TENANT_ACCESS_TOKEN = result["tenant_access_token"]
            _TOKEN_EXPIRE_TIME = current_time + result["expire"]
            logging.info("✅ 飞书 Token 已更新")
            return _TENANT_ACCESS_TOKEN
    except Exception as e:
        logging.error(f"❌ 获取飞书 Token 失败: {e}")
    return None


def read_bitable_data():
    global _EMAIL_PROGRAM_MAP_CACHE, _LAST_BITABLE_READ_TIME
    current_time = time.time()

    if current_time - _LAST_BITABLE_READ_TIME < BITABLE_CACHE_DURATION and _EMAIL_PROGRAM_MAP_CACHE:
        return _EMAIL_PROGRAM_MAP_CACHE

    token = get_feishu_token()
    if not token:
        return _EMAIL_PROGRAM_MAP_CACHE

    logging.info("🔍 同步多维表格数据...")
    new_map = {}
    page_token = ""
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BITABLE_APP_TOKEN}/tables/{BITABLE_TABLE_ID}/records"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        while True:
            params = {"page_size": 100, "page_token": page_token} if page_token else {"page_size": 100}
            resp = requests.get(url, headers=headers, params=params, timeout=15)
            if resp.status_code != 200 or resp.json().get("code") != 0:
                break

            for record in resp.json()["data"]["items"]:
                fields = record.get("fields", {})
                email_str = fields.get(BITABLE_EMAIL_COL, "").strip().lower()
                project_code = fields.get(BITABLE_PROJECT_COL, "").strip()
                vps_info = fields.get(BITABLE_VPS_COL, "").strip()
                if not email_str:
                    continue
                new_map[email_str] = (project_code, vps_info)
                if ',' in email_str:
                    for e in [x.strip() for x in email_str.split(',') if x.strip()]:
                        new_map[e] = (project_code, vps_info)

            if not resp.json()["data"].get("has_more"):
                break
            page_token = resp.json()["data"]["page_token"]

        _EMAIL_PROGRAM_MAP_CACHE = new_map
        _LAST_BITABLE_READ_TIME = current_time
        logging.info(f"✅ 同步完成，共 {len(new_map)} 条记录")
    except Exception as e:
        logging.error(f"❌ 读取多维表格失败: {e}")
    return new_map


def get_project_info(recipient_email):
    import email.utils
    pure_email = email.utils.parseaddr(recipient_email)[1].strip().lower()
    email_map = read_bitable_data()
    if pure_email in email_map:
        return email_map[pure_email]
    for key in email_map:
        if ',' in key and pure_email in [x.strip() for x in key.split(',')]:
            return email_map[key]
    return ("", "")


def send_feishu_msg(subject_tag, raw_subject, sender, recipient, receive_time, card_color, email_body):
    token = get_feishu_token()
    if not token:
        return False

    project_code, vps_info = get_project_info(recipient)
    card_title = subject_tag.strip("【】") if subject_tag else "邮件通知"

    card = {
        "config": {"wide_screen_mode": True},
        "header": {"title": {"content": card_title, "tag": "plain_text"}, "template": card_color},
        "elements": [
            {"tag": "div", "text": {"content": f"**项目代码：** {project_code or '未匹配'}", "tag": "lark_md"}},
            {"tag": "div", "text": {"content": f"**提审机器：** {vps_info or '未匹配'}", "tag": "lark_md"}},
            {"tag": "div", "text": {"content": f"**收件人：** {recipient}", "tag": "lark_md"}},
            {"tag": "div", "text": {"content": f"**发件人：** {sender}", "tag": "lark_md"}},
            {"tag": "div", "text": {"content": f"**收件时间：** {receive_time}", "tag": "lark_md"}},
            {"tag": "div", "text": {"content": f"**邮件主题：** {raw_subject}", "tag": "lark_md"}},
            {
                "tag": "collapsible_panel",
                "expanded": False,
                "header": {
                    "title": {"tag": "markdown", "content": "**邮件正文 (点击展开)**"},
                    "icon": {"tag": "standard_icon", "token": "down-small-ccm_outlined", "size": "16px 16px"}
                },
                "elements": [{"tag": "markdown", "content": email_body.replace("\n", "  \n")}]
            }
        ]
    }

    try:
        resp = requests.post(
            "https://open.feishu.cn/open-apis/im/v1/messages",
            params={"receive_id_type": "chat_id"},
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"receive_id": CHAT_ID, "msg_type": "interactive", "content": json.dumps(card, ensure_ascii=False)},
            timeout=10
        )
        if resp.json().get("code") == 0:
            logging.info("📤 已转发")
            return True
        else:
            logging.warning(f"⚠️ 飞书API返回错误: {resp.json()}")
    except Exception as e:
        logging.error(f"❌ 发送失败: {e}")
    return False


def search_package_in_bitable(package_name: str) -> bool:
    """
    在包名表格中搜索指定包名，类似 Ctrl+F 全文搜索。
    找到至少一条匹配记录返回 True，否则返回 False。
    """
    token = get_feishu_token()
    if not token:
        return False

    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BITABLE_PKG_APP_TOKEN}/tables/{BITABLE_PKG_TABLE_ID}/records/search"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = {
        "page_size": 1,
        "filter": {
            "conjunction": "and",
            "conditions": [
                {
                    "field_name": BITABLE_PKG_COL,
                    "operator": "contains",
                    "value": [package_name]
                }
            ]
        }
    }

    try:
        resp = requests.post(url, headers=headers, json=body, timeout=10)
        data = resp.json()
        if data.get("code") == 0:
            total = data.get("data", {}).get("total", 0)
            if total > 0:
                logging.info(f"✅ 包名匹配成功: {package_name}（共 {total} 条记录）")
                return True
            else:
                logging.info(f"ℹ️ 包名未匹配: {package_name}")
                return False
        else:
            logging.warning(f"⚠️ 多维表格搜索返回错误: {data}")
            return False
    except Exception as e:
        logging.error(f"❌ 包名搜索异常: {e}")
        return False


def send_error_alert(error_msg):
    token = get_feishu_token()
    if not token:
        return
    card = {
        "header": {"title": {"content": "⚠️ 程序运行异常告警", "tag": "plain_text"}, "template": "red"},
        "elements": [{"tag": "div", "text": {"content": f"错误详情：\n{error_msg[:500]}...", "tag": "plain_text"}}]
    }
    try:
        requests.post(
            "https://open.feishu.cn/open-apis/im/v1/messages",
            params={"receive_id_type": "chat_id"},
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"receive_id": CHAT_ID, "msg_type": "interactive", "content": json.dumps(card, ensure_ascii=False)},
            timeout=10
        )
    except:
        pass