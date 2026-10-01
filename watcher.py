import os
import requests

# =========================
# 감시 대상
# =========================

DATE = "20261003"
THEATER_NO = "0020"

MOVIE_KEYWORD = "치이카와"
SCREEN_KEYWORD = "2관"
START_TIME = "10:10"

# 현재 예매할 수 없는 장애인석
DISABLED_SEAT_COUNT = 2

URL = "https://www.megabox.co.kr/on/oh/ohc/Brch/schedulePage.do"

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


# =========================
# Telegram
# =========================

def send_message(message):
    telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    response = requests.post(
        telegram_url,
        data={
            "chat_id": CHAT_ID,
            "text": message,
        },
        timeout=20,
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
        "crtDe": "20261001",
        "playDe": DATE,
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.megabox.co.kr/",
    }

    response = requests.post(
        URL,
        data=params,
        headers=headers,
        timeout=20,
    )

    response.raise_for_status()

    result = response.json()

    mega_map = result.get("megaMap", {})

    return mega_map.get("movieFormList", [])


# =========================
# 메인
# =========================

def main():

    schedules = get_schedule()

    target = None

    for item in schedules:

        movie_name = item.get("movieNm", "")

        screen_name = item.get("theabExpoNm", "")

        start_time = item.get("playStartTime", "")

        # 영화 확인
        if MOVIE_KEYWORD not in movie_name:
            continue

        # 2관 확인
        if SCREEN_KEYWORD not in screen_name:
            continue

        # 10:10 회차 확인
        if start_time != START_TIME:
            continue

        target = item
        break

    if target is None:

        print("❌ 목표 회차를 찾지 못했습니다.")

        print("전체 회차:", len(schedules))

        return

    movie_name = target.get("movieNm", "")
    screen_name = target.get("theabExpoNm", "")
    start_time = target.get("playStartTime", "")
    end_time = target.get("playEndTime", "")

    rest_seat = int(target.get("restSeatCnt", 0))
    total_seat = int(target.get("totSeatCnt", 0))

    # 장애인석 2개를 제외한 일반석 계산
    normal_seat = max(
        0,
        rest_seat - DISABLED_SEAT_COUNT
    )

    print("🎬 목표 회차 발견")
    print("영화:", movie_name)
    print("관:", screen_name)
    print("시간:", start_time, "~", end_time)
    print("메가박스 잔여좌석:", rest_seat)
    print("일반석 추정 잔여:", normal_seat)
    print("전체 좌석:", total_seat)

    # =========================
    # 일반석이 생긴 경우만 알림
    # =========================

    if normal_seat >= 1:

        message = (
            "🚨 치이카와 좌석 오픈!\n\n"
            "🎬 극장판 치이카와: 인어 섬의 비밀\n"
            "📍 메가박스 안성스타필드\n"
            "📅 2026-10-03 (토)\n"
            f"🎥 {screen_name}\n"
            f"⏰ {start_time} ~ {end_time}\n"
            f"💺 일반석 약 {normal_seat}석 가능\n\n"
            "👉 취소표가 발생했습니다!"
        )

        send_message(message)

        print("🚨 일반석 좌석 발생 → Telegram 알림 전송 완료")

    else:

        print("⛔ 일반석 없음 → 알림 안 보냄")


if __name__ == "__main__":
    main()
