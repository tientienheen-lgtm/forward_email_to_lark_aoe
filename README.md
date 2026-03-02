# 📬 Google Play 邮件监控 → 飞书通知系统

自动监控新浪邮箱中来自 Google Play 的开发者邮件，使用 DeepSeek AI 提取应用包名，与飞书多维表格中的包名库匹配，匹配成功则发送飞书群消息通知。

---

## 🔄 工作流程

```
新浪邮箱（每60秒检查）
    ↓ 过滤指定发件人 + 关键词匹配
DeepSeek AI 提取包名
    ↓
飞书多维表格包名库搜索
    ↓ 匹配成功
发送飞书群卡片通知
```

---

## 📁 项目结构

```
├── main.py            # 主程序入口，7*24 小时循环运行
├── email_utils.py     # 邮箱连接、邮件读取与过滤
├── ai_processor.py    # DeepSeek 提取包名 + 飞书表格匹配
├── feishu_utils.py    # 飞书 Token、消息发送、多维表格操作
├── config.py          # 所有配置项
├── .env               # 环境变量（不提交到 git）
├── .env.example       # 环境变量模板
└── requirements.txt   # 依赖列表
```

---

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/your-repo/forward_email_to_lark_aoe.git
cd forward_email_to_lark_aoe
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制模板并填写真实值：

```bash
cp .env.example .env
```

用编辑器打开 `.env`，按下方说明逐项填写。

### 4. 运行

```bash
python main.py
```

---

## ⚙️ 环境变量说明

| 变量名 | 说明 | 获取方式 |
|--------|------|---------|
| `EMAIL_ACCOUNT` | 新浪邮箱账号 | 你的邮箱地址 |
| `EMAIL_PASSWORD` | 新浪邮箱 IMAP 授权码 | 邮箱设置 → 客户端授权码 |
| `APP_ID` | 飞书应用 ID | 飞书开放平台 → 应用 → 凭证与基础信息 |
| `APP_SECRET` | 飞书应用密钥 | 同上 |
| `CHAT_ID` | 飞书目标群 ID | 右键群聊 → 复制链接，末段即为 ID |
| `BITABLE_APP_TOKEN` | 项目映射表格 Token | 多维表格链接中 `/base/` 后面的字符串 |
| `BITABLE_TABLE_ID` | 项目映射表格 ID | 多维表格链接中 `?table=` 后面的字符串 |
| `BITABLE_EMAIL_COL` | 邮箱列名 | 多维表格中对应列的列头名称 |
| `BITABLE_PROJECT_COL` | 项目代码列名 | 多维表格中对应列的列头名称 |
| `BITABLE_VPS_COL` | 提审机器列名 | 多维表格中对应列的列头名称 |
| `DEEPSEEK_API_KEY` | DeepSeek API Key | [platform.deepseek.com](https://platform.deepseek.com) 注册后获取 |

---

## 📦 包名匹配表格配置

包名库表格信息已硬编码在 `config.py` 中：

```python
BITABLE_PKG_APP_TOKEN = "WJlfbzhcHatoWWs2bO1cctoKnQc"
BITABLE_PKG_TABLE_ID  = "tblgIfOupxB4TrCP"
BITABLE_PKG_COL       = "包名"
```

如需更换表格，直接修改这三项即可。

---

## 📋 requirements.txt

```
python-dotenv
requests
pytz
openai
```

安装命令：

```bash
pip install -r requirements.txt
```

---

## 🔍 匹配逻辑说明

1. 每 60 秒检查一次邮箱未读邮件
2. 只处理来自以下发件人的邮件：
   - Google：`no-reply-googleplay-developer@google.com`
   - Apple：`no_reply@email.apple.com`
3. 邮件主题必须命中关键词规则才继续处理
4. DeepSeek AI 读取邮件正文，提取 Google Play 包名
5. 用提取到的包名在飞书多维表格的「包名」列中搜索
6. 有匹配结果 → 发送飞书卡片通知；无匹配 → 静默跳过，标记已读

---

## ❓ 常见问题

**Q：新浪邮箱登录失败？**  
A：`EMAIL_PASSWORD` 填的是 IMAP 授权码，不是登录密码。前往新浪邮箱 → 设置 → 客户端授权码 开启并获取。

**Q：DeepSeek 提取不到包名？**  
A：检查邮件正文是否被截断（目前限制 3000 字符），或包名格式不符合反向域名规则。

**Q：飞书消息发送失败？**  
A：确认飞书应用已开通「发送消息」权限，且机器人已加入目标群聊。

**Q：如何后台持续运行？**  
```bash
nohup python main.py > email_monitor.log 2>&1 &
```
