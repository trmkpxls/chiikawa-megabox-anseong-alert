import os
import requests

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

URL = "https://www.megabox.co.kr/on/oh/ohb/SimpleBooking/selectBokdList.do"

def send_message(text):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": text},
        timeout=20,
    )

def main():
    # Telegram 연결 테스트
    send_message("🧪 메가박스 봇 테스트\nTelegram 연결이 정상입니다.")

if __name__ == "__main__":
    main()
