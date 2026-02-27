# -*- coding: utf-8 -*-
"""所有敏感配置独立存放"""

# ========== 邮箱配置 ==========
IMAP_SERVER = "imap.sina.com"
EMAIL_ACCOUNT = "aoe_google@sina.com"
EMAIL_PASSWORD = "433fbd3c1420e184"  # 授权码

# ========== 飞书配置 ==========
APP_ID = "cli_a873200afb1f100c"
APP_SECRET = "pPBzh1uYJWzvnGZIP1Jzztwnkeb7pgYk"
CHAT_ID = "oc_04de837b1e7ec3f4fcfccd049c1bc1ab"  # 接收消息/异常的群ID 需要修改，预留多个群聊接口
#CHAT_ID ="oc_4eb24b6eacc039345f84bd798b5c2e09" #账号组ID

# ========== 飞书多维表格配置 ==========
BITABLE_APP_TOKEN = "WJlfbzhcHatoWWs2bO1cctoKnQc"
BITABLE_TABLE_ID = "tbl0IzjjavVzIOpq"
BITABLE_EMAIL_COL = "开发者邮箱"
BITABLE_PROJECT_COL = "总表对照项目"
BITABLE_VPS_COL = "虚拟机/风控编号"

# ========== 业务配置 ==========
CHECK_INTERVAL = 60  # 检查间隔（秒）
BITABLE_CACHE_DURATION = 1800  # 表格缓存时间（秒）

# 监控文件夹&目标发件人
SEARCH_FOLDERS = ["apple", "google"]
TARGET_SENDERS = {
    "apple": ["no_reply@email.apple.com"],
    "google": ["no-reply-googleplay-developer@google.com"],
    #"globalrating": ["noreply@globalratings.com"]  
}

# 关键词规则
KEYWORD_RULES = [
    # 苹果邮件关键词规则 - 只要包含 "issue" 即可触发
    ("There's an issue with your", ("苹果应用拒审", "orange")),
    
    # 原有的苹果规则（如果需要可以保留，"issue" 会覆盖大部分拒审情况）
    ("Welcome to the App Store", ("苹果应用首次上线", "green")),          
    ("submission is complete.", ("苹果应用审核通过", "blue")),          
    ("You have a message from App Review about ", ("苹果审核回复", "orange")),               
    
    # 谷歌邮件关键词规则
    ("IARC Live Rating Notice:", ("谷歌应用首次上线", "green")),
    ("Notification from Google Play about ", ("谷歌开发者通知", "red")),
    ("Action Required: Your app is not compliant with Google Play Policies", ("需要采取措施：应用不符合政策", "yellow")),
    ("建议采取行动", ("需要采取措施：应用不符合政策", "yellow")),
]