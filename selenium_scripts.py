from selenium import webdriver
import time
from data.credentials import username, password

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from urllib.parse import urlparse, parse_qs

from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)

HUB_URL = 'http://firefox:4444/wd/hub'

def _xpath_literal(s: str) -> str:
    if "'" not in s:
        return f"'{s}'"
    if '"' not in s:
        return f'"{s}"'
    parts = s.split("'")
    return "concat(" + ", \"'\", ".join("'" + p + "'" for p in parts) + ")"

def _extract_id(a):
    data_id = a.get_attribute("data-id")
    if data_id:
        return data_id.split("/")[-1]
    href = a.get_attribute("href") or ""
    event_id = parse_qs(urlparse(href).query).get("eventId", [None])[0]
    return event_id.split("/")[-1] if event_id else None

class FirefoxDriver:
    def __init__(self):
        logger.info("Initializing FirefoxDriver with Remote WebDriver at %s", HUB_URL)
        # Initialize Firefox options
        options = Options()
        options.add_argument('--headless')  # Optional: run Firefox in headless mode
        options.add_argument('--no-sandbox')  # Optional: required for certain environments
        options.add_argument('--disable-dev-shm-usage')  # Optional: to prevent out-of-memory errors in Docker

        logger.debug("Firefox options set: headless, no-sandbox, disable-dev-shm-usage")
        self.driver = webdriver.Remote(command_executor=HUB_URL, options=options)
        logger.info("Remote WebDriver session started: %s", getattr(self.driver, "session_id", "unknown"))

    def __enter__(self):
        logger.debug("Entering FirefoxDriver context manager")
        return self.driver

    def __exit__(self, type, value, tb):
        logger.info("Exiting FirefoxDriver context manager. Quitting driver.")
        driver = self.driver.quit()
        logger.debug("Driver.quit() invoked")

def _playwaze_login(driver):
    logger.info("Navigating to Playwaze login page")
    # Go to login page
    driver.get("https://www.playwaze.com/Login")

    logger.debug("Waiting for username input visibility")
    username_box = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "UserName"))
    )
    logger.debug("Username input visible. Sending credentials (username only, password redacted).")
    username_box = driver.find_element("id", "UserName")
    username_box.send_keys(username)
    password_box = driver.find_element("id", "Password")
    password_box.send_keys(password)

    continue_button = driver.find_element("class name", "PointerClass")
    logger.info("Submitting login form")
    continue_button.click()

def _get_session_id_from_string(driver, session_string: str, timeout=5):
    driver.get("https://www.playwaze.com/oxford-university-badminton-club/e5vt8osgi3erh/Community-Details")
    frag = _xpath_literal(session_string)
    xpath = (
        f'//a[contains(@class,"marketplace-result") and @data-type="PhysicalActivity"]'
        f'[.//div[contains(@class,"marketplace-result-details-title")]/div[1]'
        f'[contains(normalize-space(.), {frag})]]'
    )
    els = WebDriverWait(driver, timeout).until(
        lambda d: d.find_elements(By.XPATH, xpath)
    )
    if len(els) == 1:
        return _extract_id(els[0])
    if not els:
        raise ValueError("No title contained the fragment")
    return [
        (
            els[i].find_element(By.CSS_SELECTOR, ".marketplace-result-details-title > div:nth-child(1)")
            .text.strip(),
            _extract_id(els[i])
        )
        for i in range(len(els))
    ]

def _fetch_session_start_time(driver, session_id: str, timeout = 15):
    logger.info("Fetching start time for session string: %s", session_id)
    driver.get(f"https://www.playwaze.com/discover/result?item=PhysicalEvents/{session_id}")
    logger.debug("Locating time container div")

    el = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((
            By.XPATH,
            '//div[contains(@class,"session-details")]//div[contains(@class,"session-detail")][1]/div[2]'
        ))
    )
    text = el.text.strip()
    # Find the "Friday, October 24, 12:30" part
    m = re.search(r'([A-Za-z]+,\s+[A-Za-z]+\s+\d{1,2},\s+\d{1,2}:\d{2})', text)
    if not m:
        raise ValueError(f"Could not parse start time from: {text!r}")

    start_str = m.group(1)
    year = datetime.now().year
    dt = datetime.strptime(f"{start_str} {year}", "%A, %B %d, %H:%M %Y")
    return dt
        
def get_session_id_and_date(session_string: str, use_chrome=False):
    logger.info("Getting session ID and date for session string: %s", session_string)
    with FirefoxDriver() if not use_chrome else webdriver.Chrome() as driver:
        _playwaze_login(driver)
        session_id = _get_session_id_from_string(driver, session_string)
        if session_id is None or (isinstance(session_id, list) and len(session_id) != 1):
            raise ValueError(f"Could not uniquely identify session for string: {session_string!r}")
        start_datetime = _fetch_session_start_time(driver, session_id)
        return session_id, start_datetime


def book_session(session_id: str, booking_time: float, use_chrome = False):
    logger.info("Starting booking flow. session_string='%s', booking_time=%s", session_id, booking_time)
    with FirefoxDriver() if not use_chrome else webdriver.Chrome() as driver:
        _playwaze_login(driver)
        wait = WebDriverWait(driver, 15)

        driver.get(f"https://playwaze.com/Book?p=PhysicalEvents/{session_id}")

        logger.info("Waiting for and clicking 'Continue' (dependant-booking) button")
        continue_button = wait.until(EC.element_to_be_clickable((By.ID, "dependant-booking")))
        continue_button.click()

        logger.info("Selecting account for provided username")
        account_div = wait.until(EC.element_to_be_clickable((By.XPATH, f"//div[@class='select-account' and @accusername='{username}']")))
        account_div.click()

        logger.info("Clicking 'Complete' booking button")
        complete_button = wait.until(EC.element_to_be_clickable((By.ID, "session-book")))
        complete_button.click()
        logger.info("Booking flow submitted")

if __name__ == "__main__":
    print(get_session_id_and_date("Fri 24/10 1230", use_chrome=True))
    # book_session("84034-B", 1740657600.0, use_chrome=True)
