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
KEYWORDS = ["치이카와", "인어 섬"]
# 안성스타필드
ANSEONG_THEATER_NO = "0020"
# 수원AK플라자(수원역)
SUWON_THEATER_NO = "0052"
# 수원AK에서 감시할 정확한 회차
SUWON_TARGET_TIME = "07:40"
SUWON_TARGET_ROOM = "컴포트 2관"
# =========================
# Telegram 전송
# =========================
def send_message(text):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": text
        },
        timeout=20
    )
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
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.megabox.co.kr/booking"
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
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"접속 실패: {e}")
            if attempt < 3:
                print("10초 후 재시도합니다...")
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
        return
    mega_map = result.get("megaMap", {})
    schedules = mega_map.get("movieFormList", [])
    found = []
    for item in schedules:
        movie_name = item.get("movieNm", "")
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
    print("안성 전체 상영:", len(schedules))
    print("안성 치이카와 발견:", len(found))
    if found:
        message = (
            "🚨 메가박스 상영 오픈!\n\n"
            "🏢 안성스타필드\n"
            "📅 2026-10-03\n\n"
            + "\n\n".join(found)
        )
        send_message(message)
# =========================
# 수원AK플라자 확인
# =========================
def check_suwon():
    result = get_schedule(SUWON_THEATER_NO)
    if result is None:
        return
    mega_map = result.get("megaMap", {})
    schedules = mega_map.get("movieFormList", [])
    found = []
    for item in schedules:
        movie_name = item.get("movieNm", "")
        # 치이카와가 아니면 제외
        if not any(keyword in movie_name for keyword in KEYWORDS):
            continue
        start = item.get("playStartTime", "")
        end = item.get("playEndTime", "")
        room = item.get("theabNm", "")
        # 07:40 회차만 확인
        if start != SUWON_TARGET_TIME:
            continue
        # COMFORT 2관만 확인
        if SUWON_TARGET_ROOM not in room:
            continue
        remain = item.get("restSeatCnt", "")
        total = item.get("totSeatCnt", "")
        # 좌석이 생겼을 때만 알림
        try:
            if int(remain) <= 0:
                print("수원AK 07:40 COMFORT 2관 - 아직 좌석 없음")
                continue
        except (ValueError, TypeError):
            pass
        found.append(
            f"🎬 {movie_name}\n"
            f"🛋️ {room}\n"
            f"🕐 {start} ~ {end}\n"
            f"💺 좌석: {remain}/{total}"
        )
    print("수원AK 전체 상영:", len(schedules))
    print("수원AK 목표 회차 발견:", len(found))
    if found:
        message = (
            "🚨 메가박스 좌석 발생!\n\n"
            "🏢 수원AK플라자(수원역)\n"
            "🛋️ COMFORT 2관\n"
            "📅 2026-10-03\n"
            "🕐 07:40 회차\n\n"
            + "\n\n".join(found)
        )
        send_message(message)
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
if __name__ == "__main__":
    main()
