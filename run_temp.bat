@echo off
chcp 65001 >nul

set PYTHON=C:\Users\aoemo\AppData\Local\Programs\Python\Python311\python.exe
set SCRIPT=C:\Users\aoemo\Desktop\邮件转发\main.py

schtasks /create /tn "邮件转发监控" /tr "\"%PYTHON%\" \"%SCRIPT%\"" /sc onlogon /rl highest /f

echo ✅ 开机自启动已设置完成
echo 任务名称: 邮件转发监控
echo 脚本路径: %SCRIPT%
pause