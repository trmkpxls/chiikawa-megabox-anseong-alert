import os
import time
import requests

# =========================
# 설정
# =========================
DATE = "20261003"
THEATER_NO = "0020"
KEYWORDS = ["치이카와", "인어 섬"]

URL = "https://www.megabox.co.kr/on/oh/ohc/Brch/schedulePage.do"

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


# =========================
# Telegram 메시지 전송
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
        "crtDe": "20260930",
        "playDe": DATE,
    }

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/140.0.0.0 Safari/537.36"
        ),
        "Referer": "https://www.megabox.co.kr/",
    }

    # 메가박스 접속 실패 시 최대 3번 시도
    for attempt in range(1, 4):
        try:
            print(f"메가박스 조회 시도 {attempt}/3")

            response = requests.post(
                URL,
                data=params,
                headers=headers,
                timeout=20,
            )

            response.raise_for_status()

            print("메가박스 응답 성공")
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"메가박스 접속 실패: {e}")

            if attempt < 3:
                print("10초 후 다시 시도합니다...")
                time.sleep(10)
            else:
                print("3번 모두 실패했습니다.")
                return None


# =========================
# 메인
# =========================
def main():
    result = get_schedule()

    # 메가박스 접속이 3번 모두 실패한 경우
    if result is None:
        print("메가박스 조회 실패로 이번 실행을 종료합니다.")
        return

    mega_map = result.get("megaMap", {})
    schedules = mega_map.get("movieFormList", [])

    print(f"전체 상영: {len(schedules)}")

    found = []

    for movie in schedules:
        movie_name = movie.get("movieNm", "")

        if any(keyword in movie_name for keyword in KEYWORDS):
            found.append(movie)

    print(f"치이카와 발견: {len(found)}")

    # 치이카와 상영이 발견되었을 때만 Telegram 알림
    if found:
        message_lines = [
            "🎬 치이카와 상영 발견!",
            "",
            "📍 메가박스 안성스타필드",
            "📅 2026-10-03",
            "",
        ]

        for movie in found:
            movie_name = movie.get("movieNm", "영화명 없음")
            start_time = movie.get("playStartTime", "시간 없음")
            end_time = movie.get("playEndTime", "")

            message_lines.append(
                f"🎥 {movie_name}\n"
                f"⏰ {start_time} ~ {end_time}"
            )

        send_message("\n".join(message_lines))
        print("Telegram 알림 전송 완료")


if __name__ == "__main__":
    main()
