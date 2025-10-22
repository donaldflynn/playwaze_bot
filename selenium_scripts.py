from selenium import webdriver
import time
from data.credentials import username, password

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from urllib.parse import urlparse, parse_qs
from selenium.common.exceptions import TimeoutException


from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)

HUB_URL = 'http://firefox:4444/wd/hub'

_TITLE_RE = re.compile(
    r'^(?P<dow>[A-Za-z]{3})\s+(?P<day>\d{1,2})/(?P<month>\d{1,2})\s+'
    r'(?P<start>\d{3,4})-(?P<end>\d{3,4})'
)

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

def _parse_title_start_dt(title: str) -> datetime:
    """
    Parse titles like: 'Fri 24/10 1230-1400, 4 courts (Acer)'
    """
    m = _TITLE_RE.search(title.strip())
    if not m:
        raise ValueError(f"Could not parse start time from title: {title!r}")

    day = int(m.group("day"))
    month = int(m.group("month"))
    start = m.group("start").zfill(4)  # e.g. '930' -> '0930'
    hour = int(start[:2])
    minute = int(start[2:])
    year = datetime.now().year

    return datetime(year, month, day, hour, minute)

def _get_session_id_and_time_from_string(driver, session_string: str, timeout=5):
    driver.get("https://www.playwaze.com/oxford-university-badminton-club/e5vt8osgi3erh/Community-Details")
    frag = _xpath_literal(session_string)
    xpath = (
        f'//a[contains(@class,"marketplace-result") and @data-type="PhysicalActivity"]'
        f'[.//div[contains(@class,"marketplace-result-details-title")]/div[1]'
        f'[contains(normalize-space(.), {frag})]]'
    )

    try:
        els = WebDriverWait(driver, timeout).until(lambda d: d.find_elements(By.XPATH, xpath))
    except TimeoutException:
        raise ValueError("Unable to find matching sessions")
        

    # Single match → return (session_id, start_dt)
    if len(els) == 1:
        title_el = els[0].find_element(By.CSS_SELECTOR, ".marketplace-result-details-title > div:nth-child(1)")
        title = title_el.text.strip()
        session_id = _extract_id(els[0])
        start_dt = _parse_title_start_dt(title)
        return session_id, start_dt

    # Multiple matches → return list of (title, session_id, start_dt)
    out = []
    for el in els:
        title_el = el.find_element(By.CSS_SELECTOR, ".marketplace-result-details-title > div:nth-child(1)")
        title = title_el.text.strip()
        session_id = _extract_id(el)
        start_dt = _parse_title_start_dt(title)
        out.append((title, session_id, start_dt))
    return out
        
def get_session_id_and_date(session_string: str, use_chrome=False):
    logger.info("Getting session ID and date for session string: %s", session_string)
    with FirefoxDriver() if not use_chrome else webdriver.Chrome() as driver:
        _playwaze_login(driver)
        session_id, start_datetime = _get_session_id_and_time_from_string(driver, session_string)
        if session_id is None or (isinstance(session_id, list) and len(session_id) != 1):
            raise ValueError(f"Could not uniquely identify session for string: {session_string!r}")
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

        delay = booking_time - datetime.now()
        if delay.total_seconds() > 0:
            logger.info("Waiting for booking time: %s seconds", delay.total_seconds())
            time.sleep(delay.total_seconds())

        logger.info("Clicking 'Complete' booking button")

        for i in (1, 2):
            wait.until(EC.element_to_be_clickable((By.ID, "session-book"))).click()
            logger.info("Booking flow submitted (attempt %d/2)", i)
            try:
                WebDriverWait(driver, 5).until(EC.presence_of_element_located((
                            By.XPATH,
                            "//div[contains(@class,'form-page-content')]"
                            "//div[contains(@class,'booking-header')][contains(translate(normalize-space(.),"
                            " 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'success')]"
                        )))

                logger.info("Success detected")
                break
            except TimeoutException:
                if i == 2:
                    raise TimeoutException("No success after 2 attempts")
                time.sleep(5)