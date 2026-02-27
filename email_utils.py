# -*- coding: utf-8 -*-
"""邮箱相关工具封装（优化日志版）"""
import imaplib
import email
import logging
import pytz
import re
from datetime import datetime, timedelta
from email.header import decode_header
from email.utils import parseaddr
from config import *
from feishu_utils import send_feishu_msg

def decode_email_info(raw_str):
    if not raw_str: return ""
    decoded_parts = decode_header(raw_str)
    res = ""
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            res += part.decode(encoding or "utf-8", errors="ignore")
        else:
            res += str(part)
    return res

def parse_email_body(msg):
    body = ""
    try:
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type in ["text/plain", "text/html"] and "attachment" not in str(part.get("Content-Disposition", "")):
                    charset = part.get_content_charset() or "utf-8"
                    payload = part.get_payload(decode=True)
                    if payload:
                        decoded = payload.decode(charset, errors="ignore")
                        if content_type == "text/html":
                            decoded = re.sub(r'<[^>]+>', '', decoded.replace("<br>", "\n").replace("<br/>", "\n"))
                        body = decoded.strip()
                        if content_type == "text/plain": break
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                body = payload.decode(msg.get_content_charset() or "utf-8", errors="ignore").strip()
                if msg.get_content_type() == "text/html":
                    body = re.sub(r'<[^>]+>', '', body.replace("<br>", "\n").replace("<br/>", "\n"))
        
        body = body.replace("\r\n", "\n").replace("\r", "\n")
        return body[:1000] + "\n..." if len(body) > 1000 else body
    except:
        return "无法解析邮件正文"

def check_unread_emails():
    mail_conn = None
    try:
        logging.info(f"🌐 连接邮箱: {EMAIL_ACCOUNT}")
        mail_conn = imaplib.IMAP4_SSL(IMAP_SERVER, 993)
        
        try:
            mail_conn.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
            logging.info(f"✅ 登录成功")
        except imaplib.IMAP4.error as e:
            logging.error(f"❌ 登录失败: {e}")
            return
        
        past_48h = datetime.now(pytz.UTC) - timedelta(hours=48)
        imap_date = past_48h.strftime("%d-%b-%Y").replace(" 0", " ").strip()
        search_criteria = f"UNSEEN SINCE {imap_date}"
        
        total_processed = 0
        total_matched = 0
        total_sent = 0
        
        for folder in SEARCH_FOLDERS:
            try:
                mail_conn.select(f'"{folder}"', readonly=False)
                _, msg_ids = mail_conn.search(None, search_criteria)
                unread_ids = msg_ids[0].split() if msg_ids[0] else []
                
                if not unread_ids:
                    continue
                
                folder_matched = 0
                folder_sent = 0
                
                logging.info(f"📂 [{folder}] 发现 {len(unread_ids)} 封未读邮件")
                
                for msg_id in unread_ids:
                    _, msg_data = mail_conn.fetch(msg_id, "(RFC822)")
                    if not msg_data: continue
                    msg = email.message_from_bytes(msg_data[0][1])
                    
                    total_processed += 1
                    
                    # 发件人过滤（静默跳过，不记录日志）
                    sender = decode_email_info(msg.get("From", ""))
                    pure_sender = parseaddr(sender)[1].lower()
                    if pure_sender not in TARGET_SENDERS.get(folder, []):
                        continue
                    
                    # 主题匹配
                    raw_subject = msg.get("Subject", "")
                    decoded_subject = decode_email_info(raw_subject).replace("\n", "").strip()
                    
                    subject_tag, card_color = "", ""
                    for keyword, (tag, color) in KEYWORD_RULES:
                        if keyword in decoded_subject:
                            subject_tag, card_color = f"【{tag}】", color
                            break
                    
                    # 只有匹配到关键词才记录日志
                    if subject_tag:
                        folder_matched += 1
                        total_matched += 1
                        
                        # 简化日志：只显示关键信息
                        logging.info(f"✨ {subject_tag} {decoded_subject[:30]}...")
                        
                        recipient = decode_email_info(msg.get("To", ""))
                        try:
                            date_dt = email.utils.parsedate_to_datetime(msg.get("Date", ""))
                            receive_time = date_dt.astimezone(pytz.timezone("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S")
                        except:
                            receive_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        email_body = parse_email_body(msg)
                        if send_feishu_msg(subject_tag, decoded_subject, sender, recipient, receive_time, card_color, email_body):
                            mail_conn.store(msg_id, '+FLAGS', '\\Seen')
                            folder_sent += 1
                            total_sent += 1
                
                # 只有处理了邮件才输出汇总
                if folder_matched > 0:
                    logging.info(f"📊 [{folder}] 匹配 {folder_matched} 封，成功转发 {folder_sent} 封")
                    
            except Exception as folder_err:
                logging.error(f"❌ 处理文件夹 {folder} 时出错: {folder_err}")
        
        # 最终汇总（只在有匹配时显示）
        if total_matched > 0:
            logging.info(f"🎯 本次检查完成：处理 {total_processed} 封，匹配 {total_matched} 封，转发 {total_sent} 封")
        else:
            logging.info(f"✓ 本次检查完成：无需处理的邮件")
            
    except Exception as global_err:
        logging.error(f"❌ 邮件模块异常: {global_err}")
    finally:
        if mail_conn:
            try:
                mail_conn.logout()
            except: pass