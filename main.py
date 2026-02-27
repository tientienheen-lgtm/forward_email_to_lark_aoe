"""主程序（7*24运行+异常自动告警）"""
import time
import logging
import sys
from email_utils import check_unread_emails
from feishu_utils import send_error_alert
from config import CHECK_INTERVAL

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("email_monitor.log", encoding='utf-8') # 确保日志写入文件
    ]
)

def main():
    logging.info("🚀 邮箱监控系统启动（7*24小时运行模式）")
    while True:
        try:
            check_unread_emails()
        except Exception as e:
            error_msg = f"程序运行异常：{str(e)}\n异常详情：{logging.Formatter().formatException(sys.exc_info())}"
            logging.error(error_msg)
            send_error_alert(error_msg)
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()  