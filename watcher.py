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

# 영화 검색어
KEYWORDS = ["치이카와", "인어 섬"]


# =========================
# 극장 번호
# =========================

# 메가박스 안성스타필드
ANSEONG_THEATER_NO = "0020"

# 메가박스 수원AK플라자(수원역)
SUWON_THEATER_NO = "0052"


# =========================
# 수원AK 목표 회차
# =========================

SUWON_TARGET_TIME = "07:40"


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
def get_schedule(theater_no):

    params = {
        "masterType": "brch",
        "detailType": "spcl",
        "brchNo": theater_no,
        "brchNo1": theater_no,
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
            print(f"메가박스 {theater_no} 조회 {attempt}/3")

            response = requests.post(
                URL,
                data=params,
                headers=headers,
                timeout=20
            )

            response.raise_for_status()

            print(f"메가박스 {theater_no} 응답 성공")

            return response.json()

        except requests.exceptions.RequestException as e:

            print(f"메가박스 접속 실패: {e}")

            if attempt < 3:
                print("10초 후 다시 시도합니다...")
                time.sleep(10)

            else:
                print("3회 모두 실패했습니다.")

    return None


# =========================
# 안성스타필드 확인
# =========================
def check_ansung():

    result = get_schedule(ANSEONG_THEATER_NO)

    if result is None:
        print("안성스타필드 조회 실패")
        return

    mega_map = result.get("megaMap", {})
    schedules = mega_map.get("movieFormList", [])

    found = []

    for item in schedules:

        movie_name = item.get("movieNm", "")

        # 치이카와 영화가 아니면 제외
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

    print(f"안성 전체 상영: {len(schedules)}")
    print(f"안성 치이카와 발견: {len(found)}")

    if found:

        message = (
            "🚨 메가박스 치이카와 상영 발견!\n\n"
            "🏢 안성스타필드\n"
            "📅 2026-10-03\n\n"
            + "\n\n".join(found)
        )

        send_message(message)

        print("안성 Telegram 알림 전송 완료")


# =========================
# 수원AK플라자 확인
# =========================
def check_suwon():

    result = get_schedule(SUWON_THEATER_NO)

    if result is None:
        print("수원AK플라자 조회 실패")
        return

    mega_map = result.get("megaMap", {})
    schedules = mega_map.get("movieFormList", [])

    found = []

    for item in schedules:

        movie_name = item.get("movieNm", "")

        # 치이카와 영화가 아니면 제외
        if not any(keyword in movie_name for keyword in KEYWORDS):
            continue

        start = item.get("playStartTime", "")

        # 07:40 회차가 아니면 제외
        if start != SUWON_TARGET_TIME:
            continue

        # 실제 메가박스 응답에서 상영관 이름
        room = item.get("theabExpoNm", "")

        room_text = str(room).replace(" ", "").upper()

        print(
            f"수원 후보: 영화={movie_name}, "
            f"시간={start}, "
            f"상영관={room}"
        )

        # COMFORT + 2관인지 확인
        if "2관" not in room_text:
            continue

        if "COMFORT" not in room_text and "컴포트" not in room_text:
            continue

        remain = item.get("restSeatCnt", "")
        total = item.get("totSeatCnt", "")

        # 잔여 좌석 확인
        try:
            remain_count = int(remain)

            if remain_count <= 0:
                print(
                    "수원AK 07:40 COMFORT 2관 - "
                    f"현재 매진 ({remain}/{total})"
                )
                continue

        except (ValueError, TypeError):

            print(
                f"수원AK 잔여좌석 숫자 확인 불가: {remain}"
            )

            continue

        # 조건을 모두 만족
        found.append(
            f"🎬 {movie_name}\n"
            f"🛋️ {room}\n"
            f"🕐 {start} ~ {item.get('playEndTime', '')}\n"
            f"💺 좌석: {remain}/{total}"
        )

    print(f"수원AK 전체 상영: {len(schedules)}")
    print(f"수원AK 목표 회차 발견: {len(found)}")

    if found:

        message = (
            "🚨🚨 메가박스 좌석 발생! 🚨🚨\n\n"
            "🏢 수원AK플라자(수원역)\n"
            "🎬 극장판 치이카와: 인어 섬의 비밀\n"
            "🛋️ COMFORT 2관\n"
            "📅 2026-10-03\n"
            "🕐 07:40 회차\n\n"
            + "\n\n".join(found)
        )

        send_message(message)

        print("수원AK Telegram 알림 전송 완료")


# =========================
# 메인
# =========================
def main():

    print("========== 메가박스 감시 시작 ==========")

    # 안성스타필드
    check_ansung()

    # 수원AK플라자
    check_suwon()

    print("========== 메가박스 감시 종료 ==========")


# =========================
# 실행
# =========================
if __name__ == "__main__":
    main()
