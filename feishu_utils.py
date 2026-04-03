      
# -*- coding: utf-8 -*-
import requests, json, time, logging
from config import *

_token, _token_exp, _bitable_cache, _cache_time = "", 0, {}, 0

def _token_headers():
    global _token, _token_exp
    if not _token or time.time() >= _token_exp - 60:
        r = requests.post(
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal/",
            json={"app_id": APP_ID, "app_secret": APP_SECRET}, timeout=10
        ).json()
        if r.get("code") == 0:
            _token, _token_exp = r["tenant_access_token"], time.time() + r["expire"]
    return {"Authorization": f"Bearer {_token}", "Content-Type": "application/json"}

def _get_bitable():
    global _bitable_cache, _cache_time
    if time.time() - _cache_time < BITABLE_CACHE_DURATION and _bitable_cache:
        return _bitable_cache
    result, page_token = {}, ""
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BITABLE_APP_TOKEN}/tables/{BITABLE_TABLE_ID}/records"
    while True:
        data = requests.get(url, headers=_token_headers(), params={"page_size": 100, **({"page_token": page_token} if page_token else {})}, timeout=15).json()
        if data.get("code") != 0: break
        for r in data["data"]["items"]:
            f = r.get("fields", {})
            email_str = f.get(BITABLE_EMAIL_COL, "").strip().lower()
            if not email_str: continue
            val = (f.get(BITABLE_PROJECT_COL, "").strip(), f.get(BITABLE_VPS_COL, "").strip())
            for e in ([email_str] + [x.strip() for x in email_str.split(",") if x.strip()] if "," in email_str else [email_str]):
                result[e] = val
        if not data["data"].get("has_more"): break
        page_token = data["data"]["page_token"]
    _bitable_cache, _cache_time = result, time.time()
    return result

def search_package_in_bitable(package_name):
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BITABLE_APP_TOKEN}/tables/{BITABLE_TABLE_ID}/records"
    page_token = ""
    while True:
        data = requests.get(url, headers=_token_headers(), params={"page_size": 100, **({"page_token": page_token} if page_token else {})}, timeout=15).json()
        if data.get("code") != 0: return False
        if any(r["fields"].get("google_package_name", "").strip() == package_name for r in data["data"]["items"]): return True
        if not data["data"].get("has_more"): return False
        page_token = data["data"]["page_token"]

def get_project_info(recipient):
    import email.utils
    pure = email.utils.parseaddr(recipient)[1].strip().lower()
    m = _get_bitable()
    return m.get(pure) or next((v for k, v in m.items() if "," in k and pure in [x.strip() for x in k.split(",")]), ("", ""))

def send_feishu_msg(subject_tag, raw_subject, sender, recipient, receive_time, card_color, email_body):
    project_code, vps_info = get_project_info(recipient)
    card = {
        "config": {"wide_screen_mode": True},
        "header": {"title": {"content": subject_tag.strip("【】") or "邮件通知", "tag": "plain_text"}, "template": card_color},
        "elements": [
            {"tag": "div", "text": {"content": f"**项目代码：** {project_code or '未匹配'}", "tag": "lark_md"}},
            {"tag": "div", "text": {"content": f"**提审机器：** {vps_info or '未匹配'}", "tag": "lark_md"}},
            {"tag": "div", "text": {"content": f"**收件人：** {recipient}", "tag": "lark_md"}},
            {"tag": "div", "text": {"content": f"**发件人：** {sender}", "tag": "lark_md"}},
            {"tag": "div", "text": {"content": f"**收件时间：** {receive_time}", "tag": "lark_md"}},
            {"tag": "div", "text": {"content": f"**邮件主题：** {raw_subject}", "tag": "lark_md"}},
            {"tag": "collapsible_panel", "expanded": False,
             "header": {"title": {"tag": "markdown", "content": "**邮件正文 (点击展开)**"}, "icon": {"tag": "standard_icon", "token": "down-small-ccm_outlined", "size": "16px 16px"}},
             "elements": [{"tag": "markdown", "content": email_body.replace("\n", " \n")}]}
        ]
    }
    results = []
    for chat_id in filter(None, [CHAT_ID, CHAT_ID_2]):
        r = requests.post(
            "https://open.feishu.cn/open-apis/im/v1/messages",
            params={"receive_id_type": "chat_id"},
            headers=_token_headers(),
            json={"receive_id": chat_id, "msg_type": "interactive", "content": json.dumps(card, ensure_ascii=False)},
            timeout=10
        ).json()
        results.append(r.get("code") == 0)
    return all(results)

def send_error_alert(error_msg):
    card = {
        "header": {"title": {"content": "⚠️ 程序运行异常告警", "tag": "plain_text"}, "template": "red"},
        "elements": [{"tag": "div", "text": {"content": f"错误详情：\n{error_msg[:500]}", "tag": "plain_text"}}]
    }
    try:
        requests.post(
            "https://open.feishu.cn/open-apis/im/v1/messages",
            params={"receive_id_type": "chat_id"},
            headers=_token_headers(),
            json={"receive_id": CHAT_ID, "msg_type": "interactive", "content": json.dumps(card, ensure_ascii=False)},
            timeout=10
        )
    except: pass

    