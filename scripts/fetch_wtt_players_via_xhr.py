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
    Scroll the page until all rows load, then extract uppercase names
    from the second column of the players table.
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


def scrape_players_list(csv_path="./data/xhr_player_list.csv"):
    """
    Scrapes both Men and Women players from the WTT players list by
    toggling the radio inputs and scrolling. Writes deduplicated names
    to a CSV.
    """
    # Initialize headless Chrome via webdriver-manager
    service = Service(ChromeDriverManager().install())
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=service, options=options)

    all_names = set()

    # Load the Players List page
    driver.get("https://worldtabletennis.com/playerslist")
    time.sleep(2.0)

    # Accept cookies if the banner appears
    try:
        consent = driver.find_element(By.CSS_SELECTOR, "#onetrust-accept-btn-handler")
        consent.click()
        time.sleep(1.0)
    except NoSuchElementException:
        pass

    # Scrape Men (default)
    men_names = scrape_players_by_gender(driver)
    print(f"→ scraped {len(men_names)} players for Men")
    all_names.update(men_names)

    # Toggle to Women via actual input[type=radio]
    try:
        women_radio = driver.find_element(By.CSS_SELECTOR, "input[name='Gender Switch'][value='F']")
        driver.execute_script("arguments[0].click();", women_radio)
        time.sleep(2.0)
    except NoSuchElementException:
        print("❌ Could not find the Women radio input; skipping Women scraping.")

    # Scrape Women
    women_names = scrape_players_by_gender(driver)
    print(f"→ scraped {len(women_names)} players for Women")
    all_names.update(women_names)

    driver.quit()

    # Write out CSV of all unique names
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for name in sorted(all_names):
            writer.writerow([name])

    print(f"Wrote {len(all_names)} players → {csv_path}")

if __name__ == "__main__":
    scrape_players_list()
