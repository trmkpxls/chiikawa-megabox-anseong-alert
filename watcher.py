import json
import os
import subprocess
from datetime import datetime
from zoneinfo import ZoneInfo

import requests


# =========================================================
# 감시 대상
# =========================================================

TARGET_DATE = "20261010"
TARGET_DATE_TEXT = "2026-10-10 (토)"

THEATER_NAME = "메가박스 안성스타필드점"
THEATER_NO = "0020"

MOVIE_KEYWORD = "치이카와"

MEGABOX_URL = (
    "https://www.megabox.co.kr/on/oh/ohc/Brch/schedulePage.do"
)

STATE_FILE = ".megabox_state.json"

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


# =========================================================
# Telegram
# =========================================================

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": message,
        },
        timeout=20,
    )

    response.raise_for_status()


# =========================================================
# 메가박스 회차 조회
# =========================================================

def get_schedule():

    korea_now = datetime.now(
        ZoneInfo("Asia/Seoul")
    )

    params = {
        "masterType": "brch",
        "detailType": "spcl",
        "brchNo": THEATER_NO,
        "brchNo1": THEATER_NO,
        "firstAt": "N",
        "spclbYn1": "N",
        "theabKindCd1": "",
        "crtDe": korea_now.strftime("%Y%m%d"),
        "playDe": TARGET_DATE,
    }

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/140.0 Safari/537.36"
        ),
        "Referer": "https://www.megabox.co.kr/",
        "Accept": "application/json, text/plain, */*",
    }

    # 메가박스가 일시적으로 응답하지 않는 경우를 대비해
    # 최대 3번만 재시도한다.
    for attempt in range(1, 4):

        try:
            print(
                f"메가박스 조회 {attempt}/3"
            )

            response = requests.post(
                MEGABOX_URL,
                data=params,
                headers=headers,
                timeout=15,
            )

            response.raise_for_status()

            result = response.json()

            mega_map = result.get(
                "megaMap",
                {}
            )

            movie_form_list = mega_map.get(
                "movieFormList",
                []
            )

            return movie_form_list

        except requests.RequestException as e:

            print(
                f"⚠️ 메가박스 접속 실패 "
                f"{attempt}/3: {e}"
            )

            if attempt < 3:
                import time
                time.sleep(3)

    # 3번 모두 실패했다고 해서
    # GitHub Actions 자체를 실패시키지 않는다.
    #
    # 다음 5분 실행에서 다시 확인한다.
    print(
        "⚠️ 메가박스에 접속하지 못했습니다."
    )
    print(
        "이번 실행은 건너뛰고 "
        "다음 실행에서 다시 확인합니다."
    )

    return None


# =========================================================
# 치이카와 회차 찾기
# =========================================================

def find_first_chiikawa(schedules):

    if not schedules:
        return None

    chiikawa_list = []

    for item in schedules:

        movie_name = (
            item.get("movieNm")
            or ""
        )

        if MOVIE_KEYWORD not in movie_name:
            continue

        chiikawa_list.append(item)

    if not chiikawa_list:
        return None

    # 가장 빠른 상영시간 순으로 정렬
    chiikawa_list.sort(
        key=lambda x: (
            x.get("playStartTime")
            or "99:99"
        )
    )

    # 가장 빠른 회차 = 첫 번째 회차
    return chiikawa_list[0]


# =========================================================
# 상태 불러오기
# =========================================================

def load_state():

    if not os.path.exists(STATE_FILE):
        return {
            "playSchdlNo": "",
            "has_seat": False,
        }

    try:

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8",
        ) as f:

            return json.load(f)

    except Exception:

        return {
            "playSchdlNo": "",
            "has_seat": False,
        }


# =========================================================
# 상태 저장
# =========================================================

def save_state(state):

    with open(
        STATE_FILE,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            state,
            f,
            ensure_ascii=False,
            indent=2,
        )


# =========================================================
# 상태를 GitHub 저장소에 저장
# =========================================================

def commit_state():

    try:

        subprocess.run(
            [
                "git",
                "config",
                "user.name",
                "github-actions[bot]",
            ],
            check=True,
        )

        subprocess.run(
            [
                "git",
                "config",
                "user.email",
                "41898282+github-actions[bot]@users.noreply.github.com",
            ],
            check=True,
        )

        status = subprocess.run(
            [
                "git",
                "status",
                "--porcelain",
                STATE_FILE,
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        if not status.stdout.strip():

            print(
                "상태 변경 없음 → 저장하지 않음"
            )

            return

        subprocess.run(
            [
                "git",
                "add",
                STATE_FILE,
            ],
            check=True,
        )

        subprocess.run(
            [
                "git",
                "commit",
                "-m",
                "Update Megabox monitoring state",
            ],
            check=True,
        )

        subprocess.run(
            [
                "git",
                "push",
            ],
            check=True,
        )

        print(
            "✅ 감시 상태 저장 완료"
        )

    except subprocess.CalledProcessError as e:

        print(
            f"⚠️ 상태 저장 실패: {e}"
        )


# =========================================================
# 메인
# =========================================================

def main():

    print(
        "========================================"
    )
    print(
        "메가박스 치이카와 좌석 감시 시작"
    )
    print(
        f"극장: {THEATER_NAME}"
    )
    print(
        f"날짜: {TARGET_DATE_TEXT}"
    )
    print(
        "========================================"
    )

    if not TELEGRAM_TOKEN or not CHAT_ID:

        raise RuntimeError(
            "Telegram Secret이 없습니다."
        )

    schedules = get_schedule()

    # 메가박스 접속 자체가 실패한 경우
    if schedules is None:

        return

    print(
        f"전체 회차: {len(schedules)}"
    )

    target = find_first_chiikawa(
        schedules
    )

    # =====================================================
    # 아직 치이카와 회차가 없음
    # =====================================================

    if target is None:

        print(
            "아직 치이카와 회차가 없습니다."
        )

        print(
            "→ 회차가 생길 때까지 계속 기다립니다."
        )

        # 중요:
        # 회차가 없다고 기존 상태를 초기화하지 않는다.
        return

    # =====================================================
    # 첫 번째 회차 정보
    # =====================================================

    movie_name = (
        target.get("movieNm")
        or "극장판 치이카와: 인어 섬의 비밀"
    )

    screen_name = (
        target.get("theabExpoNm")
        or target.get("theabNm")
        or "관 미상"
    )

    start_time = (
        target.get("playStartTime")
        or ""
    )

    end_time = (
        target.get("playEndTime")
        or ""
    )

    play_schdl_no = (
        target.get("playSchdlNo")
        or ""
    )

    try:

        rest_seat = int(
            target.get(
                "restSeatCnt",
                0,
            )
        )

    except (TypeError, ValueError):

        rest_seat = 0

    try:

        total_seat = int(
            target.get(
                "totSeatCnt",
                0,
            )
        )

    except (TypeError, ValueError):

        total_seat = 0

    current_has_seat = (
        rest_seat > 0
    )

    print("")
    print(
        "🎬 첫 번째 회차 발견"
    )
    print(
        f"영화: {movie_name}"
    )
    print(
        f"관: {screen_name}"
    )
    print(
        f"시간: {start_time} ~ {end_time}"
    )
    print(
        f"잔여석: {rest_seat}"
    )
    print(
        f"전체 좌석: {total_seat}"
    )
    print(
        f"회차번호: {play_schdl_no}"
    )

    # =====================================================
    # 이전 상태
    # =====================================================

    state = load_state()

    previous_play_schdl_no = (
        state.get(
            "playSchdlNo",
            "",
        )
    )

    previous_has_seat = bool(
        state.get(
            "has_seat",
            False,
        )
    )

    # =====================================================
    # 첫 번째 회차가 새로 생겼거나 바뀐 경우
    # =====================================================

    if (
        previous_play_schdl_no
        != play_schdl_no
    ):

        print("")
        print(
            "🆕 첫 번째 회차가 확인되었습니다."
        )

        print(
            f"회차번호: {play_schdl_no}"
        )

        # 새 회차의 현재 좌석 상태를 저장
        new_state = {
            "playSchdlNo": play_schdl_no,
            "has_seat": current_has_seat,
        }

        # -------------------------------------------------
        # 회차가 처음 공개됐을 때
        # 이미 좌석이 있다면 알림
        # -------------------------------------------------

        if current_has_seat:

            message = (
                "🚨 치이카와 좌석 오픈!\n\n"
                f"🎬 {movie_name}\n"
                f"🏢 {THEATER_NAME}\n"
                f"📅 {TARGET_DATE_TEXT}\n"
                f"🎥 {screen_name}\n"
                f"⏰ {start_time} ~ {end_time}\n"
                f"💺 잔여석 {rest_seat}석"
            )

            send_telegram(
                message
            )

            print(
                "🚨 첫 번째 회차에 좌석 있음"
            )
            print(
                "→ Telegram 알림 전송 완료"
            )

        else:

            print(
                "⛔ 첫 번째 회차 잔여석 0"
            )
            print(
                "→ 알림 안 보냄"
            )

        save_state(
            new_state
        )

        commit_state()

        return

    # =====================================================
    # 같은 첫 번째 회차
    # =====================================================

    # 0 → 1 이상
    if (
        not previous_has_seat
        and current_has_seat
    ):

        message = (
            "🚨 치이카와 좌석 오픈!\n\n"
            f"🎬 {movie_name}\n"
            f"🏢 {THEATER_NAME}\n"
            f"📅 {TARGET_DATE_TEXT}\n"
            f"🎥 {screen_name}\n"
            f"⏰ {start_time} ~ {end_time}\n"
            f"💺 잔여석 {rest_seat}석"
        )

        send_telegram(
            message
        )

        print(
            "🚨 좌석 0 → 좌석 발생"
        )
        print(
            "→ Telegram 알림 전송 완료"
        )

    # 좌석이 계속 있음
    elif (
        previous_has_seat
        and current_has_seat
    ):

        print(
            "💺 좌석이 계속 열려 있음"
        )
        print(
            "→ 중복 알림 안 보냄"
        )

    # 좌석이 다시 0
    elif (
        previous_has_seat
        and not current_has_seat
    ):

        print(
            "⛔ 좌석이 다시 0석이 됨"
        )
        print(
            "→ 다음 좌석 발생을 기다립니다."
        )

    # 계속 0
    else:

        print(
            "⛔ 아직 좌석 없음"
        )
        print(
            "→ 알림 안 보냄"
        )

    # =====================================================
    # 현재 상태 저장
    # =====================================================

    new_state = {
        "playSchdlNo": play_schdl_no,
        "has_seat": current_has_seat,
    }

    if new_state != state:

        save_state(
            new_state
        )

        commit_state()

    else:

        print(
            "상태 변경 없음"
        )


if __name__ == "__main__":
    main()
