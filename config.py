import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ========== 邮箱配置 ==========
IMAP_SERVER = "imap.sina.com"
EMAIL_ACCOUNT = os.getenv("EMAIL_ACCOUNT")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# ========== 飞书基础配置 ==========
APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")
CHAT_ID = os.getenv("CHAT_ID")

# ========== 飞书多维表格配置 ==========
BITABLE_APP_TOKEN = os.getenv("BITABLE_APP_TOKEN")
BITABLE_TABLE_ID = os.getenv("BITABLE_TABLE_ID")
BITABLE_EMAIL_COL = os.getenv("BITABLE_EMAIL_COL")
BITABLE_PROJECT_COL = os.getenv("BITABLE_PROJECT_COL")
BITABLE_VPS_COL = os.getenv("BITABLE_VPS_COL")

# ========== 业务逻辑配置 ==========
CHECK_INTERVAL = 60
BITABLE_CACHE_DURATION = 1800
BACKEND_URL = os.getenv("BACKEND_URL") # 预设后台接口

# 监控设置
SEARCH_FOLDERS = ["apple", "google"]
TARGET_SENDERS = {
    "apple": ["no_reply@email.apple.com"],
    "google": ["no-reply-googleplay-developer@google.com"],
}

# 关键词规则
KEYWORD_RULES = [
    ("There's an issue with your", ("苹果应用拒审", "orange")),
    ("Welcome to the App Store", ("苹果应用首次上线", "green")),          
    ("submission is complete.", ("苹果应用审核通过", "blue")),          
    ("You have a message from App Review about ", ("苹果审核回复", "orange")),               
    ("IARC Live Rating Notice:", ("谷歌应用首次上线", "green")),
    ("Notification from Google Play about ", ("谷歌开发者通知", "red")),
    ("Action Required: Your app is not compliant with Google Play Policies", ("需要采取措施：应用不符合政策", "yellow")),
    ("建议采取行动", ("需要采取措施：应用不符合政策", "yellow")),
]