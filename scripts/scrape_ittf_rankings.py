import csv
import os
import time
import requests

# -----------------------------------------------
# WTT player name scraper using official API
# Supports "GetRankingIndividuals" and "GetRankingPairs" endpoints.
# -----------------------------------------------

# Base endpoints
INDIV_ENDPOINT = (
    "https://wttcmsapigateway-new.azure-api.net/"
    "internalttu/RankingsCurrentWeek/CurrentWeek/GetRankingIndividuals"
)
PAIRS_ENDPOINT = (
    "https://wttcmsapigateway-new.azure-api.net/"
    "internalttu/RankingsCurrentWeek/CurrentWeek/GetRankingPairs"
)

EVENTS = {
    # Senior events
    "MS": "MEN'S SINGLES",
    "WS": "WOMEN'S SINGLES",
    "MD": "MEN'S DOUBLES",
    "WD": "WOMEN'S DOUBLES",
    "XD": "MIXED DOUBLES",
    "MDI": "MEN'S DOUBLES INDIVIDUAL",
    "WDI": "WOMEN'S DOUBLES INDIVIDUAL",
    "XDI": "MIXED DOUBLES INDIVIDUAL",
    # Youth events
    "BS": "BOYS' SINGLES",
    "GS": "GIRLS' SINGLES",
    "BD": "BOYS' DOUBLES",
    "GD": "GIRLS' DOUBLES",
    "BDI": "BOYS' DOUBLES INDIVIDUAL",
    "GDI": "GIRLS' DOUBLES INDIVIDUAL",
}

# Age categories: Senior and Youth
CATEGORIES = ["SEN", "YOU"] 

# Pagination: 100 players per page
PAGE_SIZE = 100

# Request headers
API_KEY = os.getenv("API_KEY")
SEC_API_KEY = os.getenv("SEC_API_KEY")

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://worldtabletennis.com",
    "Referer": "https://worldtabletennis.com/",
    "apikey": API_KEY,
    "secapimkey": SEC_API_KEY,
}


def fetch_all_player_names(csv_path="./data/player_list.csv"):
    """
    Fetch every playerName from the WTT API by:
      - looping CategoryCode in [SEN, YOU]
      - looping all EVENTS keys
      - paging StartRank to EndRank in PAGE_SIZE increments
    Uses:
      - GetRankingIndividuals for MS, WS, MDI, WDI, XDI, BS, GS, BDI, GDI
      - GetRankingPairs for MD, WD, XD, BD, GD
    Writes deduplicated uppercase names to CSV.
    """
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    session = requests.Session()
    session.headers.update(HEADERS)
    seen = set()

    # Determine which events use pairs endpoint
    PAIRS_EVENTS = {"MD", "WD", "XD", "BD", "GD"}

    for cat in CATEGORIES:
        for sub_event in EVENTS.keys():
            start = 1
            while True:
                end_rank = start + PAGE_SIZE - 1
                # choose the endpoint
                if sub_event in PAIRS_EVENTS:
                    url = PAIRS_ENDPOINT
                else:
                    url = INDIV_ENDPOINT

                params = {
                    "CategoryCode": cat,
                    "SubEventCode": sub_event,
                    "StartRank": start,
                    "EndRank": end_rank
                }
                try:
                    resp = session.get(url, params=params, timeout=10)
                    resp.raise_for_status()
                    data = resp.json().get("Result", [])
                except Exception:
                    break

                if not data:
                    break

                for rec in data:
                    if sub_event in PAIRS_EVENTS:
                        p1 = rec.get("Player1Name") or rec.get("Player1")
                        p2 = rec.get("Player2Name") or rec.get("Player2")
                        for nm in (p1, p2):
                            if nm:
                                seen.add(nm.strip().upper())
                    else:
                        name = rec.get("PlayerName", "").strip().upper()
                        if name:
                            seen.add(name)

                start += PAGE_SIZE
                time.sleep(0.1)

    # write the results
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["player_name"])
        for name in sorted(seen):
            writer.writerow([name])

    print(f"Wrote {len(seen)} unique player names → {csv_path}")


if __name__ == "__main__":
    fetch_all_player_names()
