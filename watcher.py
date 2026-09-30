import os
import requests

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

URL = "https://www.megabox.co.kr/on/oh/ohb/SimpleBooking/selectBokdList.do"

DATE = "20261003"
THEATER_NO = "0020"
KEYWORD = "치이카와"


def send_message(text):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": text
        },
        timeout=20
    )


def main():
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

    response = requests.post(
        URL,
        data=data,
        headers=headers,
        timeout=20
    )

    response.raise_for_status()
    result = response.json()

    found = []

    for area in result.get("areaBrchList", []):
        for movie in area.get("movieList", []):

            movie_name = movie.get("movieNm", "")

            if KEYWORD not in movie_name:
                continue

            for schedule in movie.get("movieFormList", []):
                start = schedule.get("playStartTime", "")
                end = schedule.get("playEndTime", "")
                remain = schedule.get("restSeatCnt", "")

                found.append(
                    f"🎬 {movie_name}\n"
                    f"🕐 {start} ~ {end}\n"
                    f"💺 잔여좌석: {remain}"
                )

    if found:
        message = (
            "🚨 메가박스 상영 오픈!\n\n"
            "🏢 안성스타필드\n"
            "📅 2026-10-03\n\n"
            + "\n\n".join(found)
        )

        send_message(message)

    print("발견된 상영:", len(found))
    print("응답 종류:", type(result))
print("응답 키:", list(result.keys()))


if __name__ == "__main__":
    main()
