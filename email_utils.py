# -*- coding: utf-8 -*-
import imaplib, email, logging, pytz, re, json, anthropic
from datetime import datetime, timedelta
from email.header import decode_header
from email.utils import parseaddr, parsedate_to_datetime
from config import *
from feishu_utils import send_feishu_msg, search_package_in_bitable

def _decode(raw):
    if not raw: return ""
    return "".join(p.decode(e or "utf-8", errors="ignore") if isinstance(p, bytes) else str(p) for p, e in decode_header(raw))

def _body(msg):
    try:
        for part in (msg.walk() if msg.is_multipart() else [msg]):
            ct = part.get_content_type()
            if ct not in ("text/plain", "text/html"): continue
            if "attachment" in str(part.get("Content-Disposition", "")): continue
            raw = part.get_payload(decode=True)
            if not raw: continue
            text = raw.decode(part.get_content_charset() or "utf-8", errors="ignore")
            if ct == "text/html":
                text = re.sub(r"<[^>]+>", "", text.replace("<br>", "\n").replace("<br/>", "\n"))
            text = text.strip().replace("\r\n", "\n").replace("\r", "\n")
            return (text[:1000] + "\n...") if len(text) > 1000 else text
    except: pass
    return "无法解析邮件正文"

def _extract_pkg(subject, body):
    try:
        r = anthropic.Anthropic(api_key=CLAUDE_API_KEY).messages.create(
            model="claude-sonnet-4-6", max_tokens=128,
            messages=[{"role": "user", "content": f"从邮件提取Google Play包名，只返回JSON，没有则null。\n主题：{subject}\n正文：{body[:3000]}"}]
        )
        return json.loads(re.sub(r"^```(?:json)?\s*|\s*```$", "", r.content[0].text.strip())).get("google_package_name")
    except:
        return None

def check_unread_emails():
    logging.info("🔄 开始检查邮件...")
    try:
        conn = imaplib.IMAP4_SSL(IMAP_SERVER, 993)
        conn.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
        logging.info("✅ 邮箱登录成功")
    except Exception as e:
        logging.error(f"❌ 邮箱连接失败: {e}"); return

    imap_date = (datetime.now(pytz.UTC) - timedelta(hours=48)).strftime("%d-%b-%Y").replace(" 0", " ").strip()

    try:
        for folder in SEARCH_FOLDERS:
            conn.select(f'"{folder}"', readonly=False)
            _, ids = conn.search(None, f"UNSEEN SINCE {imap_date}")
            unread = ids[0].split() if ids[0] else []
            logging.info(f"📂 [{folder}] 未读 {len(unread)} 封")

            for mid in unread:
                try:
                    _, data = conn.fetch(mid, "(RFC822)")
                    if not data: continue
                    msg = email.message_from_bytes(data[0][1])

                    sender = _decode(msg.get("From", ""))
                    if not any(s in sender.lower() for s in TARGET_SENDERS.get(folder, [])):
                        continue

                    subject = _decode(msg.get("Subject", "")).replace("\n", "").strip()
                    tag, color = next(((f"【{t}】", c) for k, (t, c) in KEYWORD_RULES if k in subject), ("", ""))
                    if not tag: continue

                    logging.info(f"✨ 命中: {subject[:40]}")

                    recipient = _decode(msg.get("To", ""))
                    try:
                        receive_time = parsedate_to_datetime(msg.get("Date", "")).astimezone(pytz.timezone("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        receive_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    body = _body(msg)

                    if folder == "google":
                        pkg = _extract_pkg(subject, body)
                        logging.info(f"📦 包名: {pkg or '无'}")
                        if pkg and search_package_in_bitable(pkg):
                            logging.info(f"✅ 匹配成功: {pkg}")
                        else:
                            logging.info("📤 直接转发")

                    send_feishu_msg(tag, subject, sender, recipient, receive_time, color, body)
                    conn.store(mid, '+FLAGS', '\\Seen')

                except Exception as e:
                    logging.error(f"❌ 处理邮件 {mid} 失败: {e}")

    finally:
        try: conn.logout()
        except: pass
        # 删除"本轮检查完成"日志