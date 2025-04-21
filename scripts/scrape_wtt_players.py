import time
import csv
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def scrape_players_by_gender(driver, scroll_pause=1.0):
    """
    Scrolls through the players list on the current page until no more rows load,
    then extracts and returns the uppercase names from the 2nd column.
    """
    last_count = 0
    while True:
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        if len(rows) == last_count:
            break
        last_count = len(rows)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause)

    names = []
    for tr in rows:
        try:
            name = tr.find_element(By.CSS_SELECTOR, "td:nth-child(2)").text.strip()
            if name:
                names.append(name.upper())
        except NoSuchElementException:
            continue
    return names

def scrape_players_list(csv_path="./data/player_list.csv"):
    """
    Scrapes the WTT players list for both genders by loading
    "?gender=M" and "?gender=F" pages, scrolling fully, and
    writing a deduplicated sorted CSV of names.
    """
    # Setup headless Chrome with webdriver-manager
    service = Service(ChromeDriverManager().install())
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=service, options=options)

    all_names = set()

    for gender in ("M", "F"):
        url = f"https://worldtabletennis.com/playerslist?gender={gender}"
        driver.get(url)
        time.sleep(1.5)

        # Accept cookies on first load
        if gender == "M":
            try:
                btn = driver.find_element(By.CSS_SELECTOR, "#onetrust-accept-btn-handler")
                btn.click()
                time.sleep(0.5)
            except NoSuchElementException:
                pass

        names = scrape_players_by_gender(driver)
        print(f"→ scraped {len(names)} players for gender={gender}")
        all_names.update(names)

    driver.quit()

    # Write out CSV of all names
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for n in sorted(all_names):
            writer.writerow([n])

    print(f"Wrote {len(all_names)} players → {csv_path}")


if __name__ == "__main__":
    scrape_players_list()
