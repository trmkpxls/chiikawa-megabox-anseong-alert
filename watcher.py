import json
import os
import subprocess

import requests


# =========================================================
# 감시 대상
# =========================================================

DATE = "20261010"
DATE_TEXT = "2026-10-10 (토)"

THEATER = "메가박스 안성스타필드점"
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

def get_schedules():
    params = {
        "masterType": "brch",
        "detailType": "spcl",
        "brchNo": THEATER_NO,
        "brchNo1": THEATER_NO,
        "firstAt": "N",
        "spclbYn1": "N",
        "theabKindCd1": "",
        "crtDe": "20261002",
        "playDe": DATE,
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.megabox.co.kr/",
    }

    response = requests.post(
        MEGABOX_URL,
        data=params,
        headers=headers,
        timeout=20,
    )

    response.raise_for_status()

    result = response.json()

    mega_map = result.get("megaMap", {})

    return mega_map.get("movieFormList", [])


# =========================================================
# 치이카와 회차만 골라내기
# =========================================================

def get_chiikawa_schedules(schedules):
    result = []

    for item in schedules:
        movie_name = (
            item.get("movieNm")
            or item.get("rpstMovieNm")
            or ""
        )

        if MOVIE_KEYWORD not in movie_name:
            continue

        result.append(item)

    # 가장 빠른 시간 순으로 정렬
    result.sort(
        key=lambda x: x.get("playStartTime", "")
    )

    return result


# =========================================================
# 상태 파일
#
# GitHub Actions는 매번 새 컴퓨터에서 실행되기 때문에
# 이전 실행 상태를 파일로 저장하고 GitHub에 commit한다.
# =========================================================

def load_state():
    if not os.path.exists(STATE_FILE):
        return {
            "playSchdlNo": "",
            "has_seat": False,
        }

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "playSchdlNo": "",
            "has_seat": False,
        }


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
# 변경된 상태를 GitHub 저장소에 저장
# =========================================================

def commit_state():
    try:
        subprocess.run(
            ["git", "config", "user.name", "github-actions[bot]"],
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
            print("상태 변경 없음 → commit 하지 않음")
            return

        subprocess.run(
            ["git", "add", STATE_FILE],
            check=True,
        )

        subprocess.run(
            [
                "git",
                "commit",
                "-m",
                "Update Megabox seat monitoring state",
            ],
            check=True,
        )

        subprocess.run(
            ["git", "push"],
            check=True,
        )

        print("상태 저장 완료")

    except subprocess.CalledProcessError as e:
        print("⚠️ 상태 저장 중 오류:", e)


# =========================================================
# 메인 감시
# =========================================================

def main():

    if not TELEGRAM_TOKEN or not CHAT_ID:
        raise RuntimeError(
            "Telegram Secret이 없습니다."
        )

    print("========================================")
    print("메가박스 치이카와 좌석 감시 시작")
    print("극장:", THEATER)
    print("날짜:", DATE_TEXT)
    print("========================================")

    schedules = get_schedules()

    print("전체 회차:", len(schedules))

    chiikawa = get_chiikawa_schedules(schedules)

    print("치이카와 회차:", len(chiikawa))

    # -----------------------------------------------------
    # 아직 회차가 안 열림
    # -----------------------------------------------------

    if not chiikawa:
        print("아직 치이카와 회차가 없습니다.")
        print("→ 회차 오픈을 계속 기다립니다.")

        # 기존 상태를 일부러 건드리지 않는다.
        # 메가박스 API가 일시적으로 비어 있어도
        # 잘못된 상태 초기화를 방지한다.
        return

    # -----------------------------------------------------
    # 가장 빠른 첫 번째 회차 선택
    # -----------------------------------------------------

    target = chiikawa[0]

    movie_name = (
        target.get("movieNm")
        or target.get("rpstMovieNm")
        or "극장판 치이카와: 인어 섬의 비밀"
    )

    screen_name = (
        target.get("theabExpoNm")
        or target.get("theabNm")
        or "관 미상"
    )

    start_time = target.get(
        "playStartTime",
        "",
    )

    end_time = target.get(
        "playEndTime",
        "",
    )

    play_schdl_no = target.get(
        "playSchdlNo",
        "",
    )

    try:
        rest_seat = int(
            target.get("restSeatCnt", 0)
        )
    except (TypeError, ValueError):
        rest_seat = 0

    try:
        total_seat = int(
            target.get("totSeatCnt", 0)
        )
    except (TypeError, ValueError):
        total_seat = 0

    current_has_seat = rest_seat > 0

    print("")
    print("🎬 첫 번째 회차 발견")
    print("영화:", movie_name)
    print("관:", screen_name)
    print("시간:", start_time, "~", end_time)
    print("잔여석:", rest_seat)
    print("전체 좌석:", total_seat)
    print("회차번호:", play_schdl_no)

    # -----------------------------------------------------
    # 이전 상태
    # -----------------------------------------------------

    state = load_state()

    previous_play_schdl_no = state.get(
        "playSchdlNo",
        "",
    )

    previous_has_seat = bool(
        state.get(
            "has_seat",
            False,
        )
    )

    # -----------------------------------------------------
    # 첫 번째 회차가 바뀐 경우
    #
    # 예:
    # 처음에는 10:10이 첫 회차였는데
    # 나중에 09:30 회차가 추가됨
    #
    # → 새 첫 회차를 처음부터 감시
    # -----------------------------------------------------

    if previous_play_schdl_no != play_schdl_no:

        print("")
        print("🔄 첫 번째 회차가 새로 확인되었습니다.")
        print("이전 회차:", previous_play_schdl_no)
        print("현재 회차:", play_schdl_no)

        state = {
            "playSchdlNo": play_schdl_no,
            "has_seat": current_has_seat,
        }

        # 새 첫 회차가 이미 좌석이 있다면
        # 바로 알림한다.
        if current_has_seat:

            message = (
                "🚨 치이카와 좌석 오픈!\n\n"
                f"🎬 {movie_name}\n"
                f"🏢 {THEATER}\n"
                f"📅 {DATE_TEXT}\n"
                f"🎥 {screen_name}\n"
                f"⏰ {start_time} ~ {end_time}\n"
                f"💺 잔여석 {rest_seat}석\n\n"
                "👉 첫 번째 회차 좌석이 열렸습니다!"
            )

            send_telegram(message)

            print(
                "🚨 첫 번째 회차에 좌석 있음 "
                "→ Telegram 알림 전송 완료"
            )

        else:
            print(
                "⛔ 첫 번째 회차 잔여석 0 "
                "→ 알림 안 보냄"
            )

        save_state(state)
        commit_state()
        return

    # -----------------------------------------------------
    # 같은 첫 번째 회차
    #
    # 0 → 1 이상
    # 일 때만 알림
    # -----------------------------------------------------

    if not previous_has_seat and current_has_seat:

        message = (
            "🚨 치이카와 좌석 오픈!\n\n"
            f"🎬 {movie_name}\n"
            f"🏢 {THEATER}\n"
            f"📅 {DATE_TEXT}\n"
            f"🎥 {screen_name}\n"
            f"⏰ {start_time} ~ {end_time}\n"
            f"💺 잔여석 {rest_seat}석\n\n"
            "👉 첫 번째 회차 좌석이 열렸습니다!"
        )

        send_telegram(message)

        print(
            "🚨 좌석 0 → 좌석 발생 "
            "→ Telegram 알림 전송 완료"
        )

    elif previous_has_seat and current_has_seat:

        print(
            "💺 좌석이 계속 열려 있음 "
            "→ 중복 알림 안 보냄"
        )

    elif previous_has_seat and not current_has_seat:

        print(
            "⛔ 좌석이 다시 0석이 됨 "
            "→ 다음 좌석 발생을 기다림"
        )

    else:

        print(
            "⛔ 아직 좌석 없음 "
            "→ 알림 안 보냄"
        )

    # -----------------------------------------------------
    # 현재 상태 저장
    # -----------------------------------------------------

    new_state = {
        "playSchdlNo": play_schdl_no,
        "has_seat": current_has_seat,
    }

    if new_state != state:
        save_state(new_state)
        commit_state()
    else:
        print("상태 변경 없음")


if __name__ == "__main__":
    main()
