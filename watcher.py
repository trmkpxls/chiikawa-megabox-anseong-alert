import os
import requests

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

URL = "https://www.megabox.co.kr/on/oh/ohc/Brch/schedulePage.do"

DATE = "20261003"
THEATER_NO = "0020"
KEYWORDS = ["치이카와", "인어 섬"]


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
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.megabox.co.kr/booking"
    }

    response = requests.post(
        URL,
        data=params,
        headers=headers,
        timeout=20
    )

    response.raise_for_status()
    result = response.json()

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

    print("전체 상영:", len(schedules))
    print("치이카와 발견:", len(found))

    if found:
        message = (
            "🚨 메가박스 상영 오픈!\n\n"
            "🏢 안성스타필드\n"
            "📅 2026-10-03\n\n"
            + "\n\n".join(found)
        )

        send_message(message)


if __name__ == "__main__":
    main()
