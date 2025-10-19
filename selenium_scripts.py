from selenium import webdriver
import time
from data.credentials import username, password

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException

from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)

HUB_URL = 'http://firefox:4444/wd/hub'

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

def _go_to_session_from_string(driver, session_string):
    logger.info("Opening community details page to locate session: %s", session_string)
    # Go to sessions
    driver.get("https://www.playwaze.com/oxford-university-badminton-club/e5vt8osgi3erh/Community-Details")

    # Filter to clubnight only
    logger.debug("Clicking marketplace activity filter")
    marketplace_div = driver.find_element(By.XPATH, "//div[@class='marketplace-filter-type' and @data-type='activity']")
    marketplace_div.click()

    logger.info("Searching for matching session card")
    _look_for_and_click_matching_session(driver, session_string)

def _look_for_and_click_matching_session(driver, session_string):
    logger.info("Looking for session matching: %s", session_string)
    # The page may take a while to load. Look for up to NUM_ATTEMPTS seconds before giving up.
    NUM_ATTEMPTS = 10
    for i in range(NUM_ATTEMPTS):
        try:
            logger.debug("Attempt %d/%d: locating session title elements", i + 1, NUM_ATTEMPTS)
            sessions = driver.find_elements(By.CLASS_NAME, "marketplace-result-details-title")
            texts = [s.text for s in sessions]
            logger.debug("Found %d session elements: %s", len(sessions), texts)
            matching_elements = [s for s in sessions if session_string in s.text]
            logger.debug("Matching elements count: %d", len(matching_elements))
            if len(matching_elements) != 1:
                time.sleep(1)
                continue
            logger.info("Clicking matched session: %s", matching_elements[0].text)
            matching_elements[0].click()
            return
        except Exception as e:
            logger.debug("Error while scanning sessions on attempt %d: %s", i + 1, e, exc_info=True)
            pass
    try:
        # Will fail because matching_elements may be undefined if every try raised before assignment
        logger.error("Failed to find single matching session for '%s'.", session_string)
        raise ValueError(f"Expected single session matching {session_string}. Found {[e.text for e in matching_elements]}")
    except NameError:
        logger.error("Failed to find single matching session for '%s' (no elements captured).", session_string)
        raise ValueError(f"Expected single session matching {session_string}. Found []")

def fetch_session_start_time(session_string: str):
    logger.info("Fetching start time for session string: %s", session_string)
    with FirefoxDriver() as driver:
        _playwaze_login(driver)
        _go_to_session_from_string(driver, session_string)
        logger.debug("Locating time container div")
        time_div = driver.find_element(By.XPATH, "//i[@class='far fa-calendar-alt']/ancestor::div")
        # Get the text inside the div
        time_text = time_div.text
        logger.info("Raw time text: %s", time_text)

        # Extract the date and start time using regular expressions
        date_match = re.search(r"(\d{2}/\d{2}/\d{4})", time_text)  # Matches the date in DD/MM/YYYY format
        start_time_match = re.search(r"(\d{2}:\d{2}) -", time_text)  # Matches the start time in HH:MM format

        # Check if both date and start time are found
        if date_match and start_time_match:
            date_str = date_match.group(1)  # Extract the date as a string
            start_time_str = start_time_match.group(1)  # Extract the start time as a string
            logger.info("Parsed date: %s, start time: %s", date_str, start_time_str)

            # Combine the date and start time into a single string
            full_datetime_str = date_str + " " + start_time_str  # e.g., "08/11/2024 12:30"
            logger.debug("Combined datetime string: %s", full_datetime_str)

            # Convert the combined string into a datetime object
            start_datetime = datetime.strptime(full_datetime_str, "%d/%m/%Y %H:%M")
            print("Start Time (as datetime object):", start_datetime)
            logger.info("Start datetime parsed: %s", start_datetime.isoformat())
            return start_datetime
        else:
            logger.error("Unable to parse date/time from text")
            raise ValueError("Error finding date of session")

def _get_book_button(driver, booking_time):
    logger.info("Preparing to locate 'Book' button with booking_time epoch: %s", booking_time)
    wait_time = max(min(booking_time + 0.5 - time.time(), 120), 0)
    logger.info("Computed wait_time before attempt: %.3f seconds", wait_time)
    time.sleep(wait_time)
    if wait_time > 0:
        logger.debug("Refreshing page after wait")
        driver.refresh()
    for attempt in range(5):
        try:
            logger.debug("Attempt %d/5 to locate 'Book' button", attempt + 1)
            button = WebDriverWait(driver, 3).until(EC.presence_of_element_located(
                (By.XPATH, "//button[@id='attendButtona' and text()='Book']")
            ))
            logger.info("'Book' button found")
            return button
        except TimeoutException:
            logger.warning("Timeout locating 'Book' button on attempt %d. Refreshing.", attempt + 1)
            driver.refresh()
    logger.error("Unable to find the 'Book' button after retries")
    raise TimeoutException(f"{datetime.now()}: Unable to find the book button")

def book_session(session_string: str, booking_time: float):
    logger.info("Starting booking flow. session_string='%s', booking_time=%s", session_string, booking_time)
    with FirefoxDriver() as driver:
    # with webdriver.Chrome() as driver:

        _playwaze_login(driver)
        _go_to_session_from_string(driver, session_string)

        logger.debug("Initializing short WebDriverWait for button interactions")
        wait = WebDriverWait(driver, 5)

        logger.info("Waiting for 'Book' button aligned with booking_time")
        book_button = _get_book_button(driver, booking_time)
        logger.info("Clicking 'Book' button via JS to avoid intercept issues")
        driver.execute_script("arguments[0].click();", book_button)

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
# if __name__ == "__main__":
#     book_session("Sun 2/3 12", 1740657600.0)
