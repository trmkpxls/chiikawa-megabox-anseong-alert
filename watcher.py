import os
import time
import requests

# =========================
# Telegram
# =========================
TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


# =========================
# Megabox
# =========================
URL = "https://www.megabox.co.kr/on/oh/ohc/Brch/schedulePage.do"

DATE = "20261003"
THEATER_NO = "0020"

KEYWORDS = ["치이카와", "인어 섬"]


# =========================
# Telegram 메시지 전송
# =========================
def send_message(text):
    telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    response = requests.post(
        telegram_url,
        data={
            "chat_id": CHAT_ID,
            "text": text
        },
        timeout=20
    )

    response.raise_for_status()


# =========================
# 메가박스 조회
# =========================
def get_schedule():

    params = {
        "masterType": "brch",
        "detailType": "spcl",
        "brchNo": THEATER_NO,
        "brchNo1": THEATER_NO,
        "firstAt": "N",
        "spclbYn1": "N",
        "theabKindCd1": "",
        "crtDe": "20260930",
        "playDe": DATE
    }

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/140.0.0.0 Safari/537.36"
        ),
        "Referer": "https://www.megabox.co.kr/"
    }

    # 메가박스 접속 실패 시 최대 3회 재시도
    for attempt in range(1, 4):

        try:
            print(f"메가박스 조회 {attempt}/3")

            response = requests.post(
                URL,
                data=params,
                headers=headers,
                timeout=10
            )

            response.raise_for_status()

            print("메가박스 응답 성공")

            return response.json()

        except requests.exceptions.RequestException as e:

            print(f"메가박스 접속 실패: {e}")

            if attempt < 3:
                print("5초 후 다시 시도합니다...")
                time.sleep(5)
            else:
                print("3회 모두 실패했습니다.")

    return None


# =========================
# 안성스타필드 확인
# =========================
def check_ansung():

    result = get_schedule()

    if result is None:
        print("메가박스 조회 실패")
        return

    mega_map = result.get("megaMap", {})
    schedules = mega_map.get("movieFormList", [])

    found = []

    for item in schedules:

        movie_name = item.get("movieNm", "")

        # 치이카와 영화만 확인
        if not any(keyword in movie_name for keyword in KEYWORDS):
            continue

        start = item.get("playStartTime", "")
        end = item.get("playEndTime", "")

        remain = item.get("restSeatCnt", "")
        total = item.get("totSeatCnt", "")

        found.append(
            f"🎬 {movie_name}\n"
            f"🕐 {start} ~ {end}\n"
            f"💺 좌석: {remain}/{total}"
        )

    print(f"전체 상영: {len(schedules)}")
    print(f"치이카와 발견: {len(found)}")

    # 치이카와 상영이 발견되면 Telegram 알림
    if found:

        message = (
            "🚨 메가박스 치이카와 상영 발견!\n\n"
            "🏢 안성스타필드\n"
            "📅 2026-10-03\n\n"
            + "\n\n".join(found)
        )

        send_message(message)

        print("Telegram 알림 전송 완료")


# =========================
# 메인
# =========================
def main():

    print("========== 메가박스 감시 시작 ==========")

    check_ansung()

    print("========== 메가박스 감시 종료 ==========")


if __name__ == "__main__":
    main()
