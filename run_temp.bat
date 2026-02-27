@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

:: 设置唯一窗口标题
title 邮件监控系统_%RANDOM%

:: ==============================================
:: 配置区域
:: ==============================================
set REBOOT_TIME=01:00
set CHECK_INTERVAL=60
set PYTHON_SCRIPT=%~dp0main.py
set LOCK_FILE=%TEMP%\email_monitor_%~n0.lock
:: ==============================================

:: 检查是否已有实例在运行
if exist "%LOCK_FILE%" (
    echo [ERROR] 检测到程序已在运行！
    echo 锁文件: %LOCK_FILE%
    echo 如果确认没有其他实例，请删除该文件后重试
    pause
    exit /b 1
)

:: 创建锁文件
echo %date% %time% > "%LOCK_FILE%"

:: 注册退出时清理
set "CLEANUP_CMD=if exist "%LOCK_FILE%" del "%LOCK_FILE%" >nul 2>&1"
:: Ctrl+C 处理
if not defined CLEANUP_REGISTERED (
    set CLEANUP_REGISTERED=1
)

:MAIN_LOOP
cls
echo ===============================================
echo    📧 邮件监控系统运行中
echo ===============================================
echo 🕒 当前时间: %date% %time%
echo 🔄 定时重启: 每天 %REBOOT_TIME%
echo 📊 检查间隔: %CHECK_INTERVAL% 秒
echo 💡 按 Ctrl+C 可安全退出
echo ===============================================
echo.

:: 启动Python进程（后台模式）
echo [启动] 正在启动邮件监控进程...
start /B "" python.exe "%PYTHON_SCRIPT%"
if errorlevel 1 (
    echo [ERROR] Python启动失败！
    goto CLEANUP_EXIT
)

:: 等待2秒让Python完全启动
timeout /t 2 /nobreak >nul
echo [成功] 监控进程已启动

:MONITOR_LOOP
:: 每次循环显示一次状态
set "cur_time=%time:~0,5%"
set "cur_time=%cur_time: =0%"
echo [%date% %cur_time%] 监控中...

:: 1. 检查Python进程是否还在运行
tasklist /FI "IMAGENAME eq python.exe" /FI "STATUS eq running" 2>nul | find /I "python.exe" >nul
if errorlevel 1 (
    echo.
    echo [警告] 检测到Python进程已退出！
    echo [操作] 等待30秒后自动重启...
    timeout /t 30 /nobreak >nul
    goto MAIN_LOOP
)

:: 2. 检查是否到达定时重启时间
if "%cur_time%"=="%REBOOT_TIME%" (
    echo.
    echo ===============================================
    echo [定时重启] 已到达预定时间 %REBOOT_TIME%
    echo ===============================================
    goto RESTART_PROCESS
)

:: 3. 等待后继续监控
timeout /t %CHECK_INTERVAL% /nobreak >nul
goto MONITOR_LOOP

:RESTART_PROCESS
echo [1/4] 准备重启进程...

:: 温柔终止（给Python时间清理资源）
echo [2/4] 正在发送终止信号...
taskkill /FI "IMAGENAME eq python.exe" /T >nul 2>&1
timeout /t 5 /nobreak >nul

:: 强制清理残留进程
echo [3/4] 清理残留进程...
taskkill /FI "IMAGENAME eq python.exe" /F /T >nul 2>&1
timeout /t 3 /nobreak >nul

:: 确认清理完成
tasklist /FI "IMAGENAME eq python.exe" 2>nul | find /I "python.exe" >nul
if not errorlevel 1 (
    echo [警告] 仍有Python进程残留，强制清理...
    taskkill /IM python.exe /F /T >nul 2>&1
    timeout /t 2 /nobreak >nul
)

echo [4/4] 重启完成，3秒后恢复监控...
timeout /t 3 /nobreak >nul
goto MAIN_LOOP

:CLEANUP_EXIT
echo.
echo [退出] 正在清理资源...
:: 清理Python进程
taskkill /FI "IMAGENAME eq python.exe" /F /T >nul 2>&1
:: 删除锁文件
if exist "%LOCK_FILE%" del "%LOCK_FILE%" >nul 2>&1
echo [完成] 程序已安全退出
timeout /t 3 >nul
exit /b 0