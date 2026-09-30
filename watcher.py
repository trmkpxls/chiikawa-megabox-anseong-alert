import os
import requests

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

DATE = "20261003"
THEATER = "안성스타필드"
THEATER_NO = "0020"
MOVIE_KEYWORD = "치이카와"

URL = "https://www.megabox.co.kr/on/oh/ohb/SimpleBooking/selectBokdList.do"


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": message
    })


def check_megabox():
    data = {
        "arrMovieNo": "",
        "playDe": DATE,
        "brchNoListCnt": "1",
        "brchNo1": THEATER_NO,
        "areaCd1": "",
        "spclbYn1": "N",
        "theabKindCd1": "",
        "sellChnlCd": "ONLINE"
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.megabox.co.kr/booking"
    }

    response = requests.post(URL, data=data, headers=headers, timeout=20)
    response.raise_for_status()

    result = response.json()

    found = []

    for area in result.get("areaBrchList", []):
        for movie in area.get("movieList", []):
            movie_name = movie.get("movieNm", "")

            if MOVIE_KEYWORD not in movie_name:
                continue

            for schedule in movie.get("movieFormList", []):
                start = schedule.get("playStartTime", "")
                end = schedule.get("playEndTime", "")
                remain = schedule.get("restSeatCnt", "")

                found.append(
                    f"{movie_name}\n"
                    f"시간: {start} ~ {end}\n"
                    f"잔여좌석: {remain}"
                )

    return found


if __name__ == "__main__":
    if not TELEGRAM_TOKEN or not CHAT_ID:
        raise RuntimeError("Telegram Secret이 없습니다.")

    schedules = check_megabox()

    if schedules:
        message = (
            "🎬 메가박스 상영 오픈!\n\n"
            f"🏢 {THEATER}\n"
            f"📅 2026-10-03\n\n"
            + "\n\n".join(schedules)
        )

        send_telegram(message)
        print(message)

    else:
        print("아직 상영시간표가 없습니다.")
