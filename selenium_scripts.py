from selenium import webdriver
import time

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options

from datetime import datetime

import re

HUB_URL = 'http://firefox:4444/wd/hub'

class FirefoxDriver:
    def __init__(self):
        
        # Initialize Firefox options
        options = Options()
        options.add_argument('--headless')  # Optional: run Firefox in headless mode
        options.add_argument('--no-sandbox')  # Optional: required for certain environments
        options.add_argument('--disable-dev-shm-usage')  # Optional: to prevent out-of-memory errors in Docker

        self.driver = webdriver.Remote(command_executor=HUB_URL, options=options)
    def __enter__(self):
        return self.driver
    def __exit__(self, type, value, tb):
        driver = self.driver.quit()

def _playwaze_login(driver, username, password):
    # Go to login page
    driver.get("https://www.playwaze.com/Login")

    username_box = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "UserName"))
    )
    username_box = driver.find_element("id", "UserName")
    username_box.send_keys(username)
    password_box = driver.find_element("id", "Password")
    password_box.send_keys(password)

    continue_button = driver.find_element("class name", "PointerClass")
    continue_button.click()

def _go_to_session_from_string(driver, session_string):
    # Go to sessions
    driver.get("https://www.playwaze.com/oxford-university-badminton-club/e5vt8osgi3erh/Community-Details")

    # Filter to clubnight only
    marketplace_div = driver.find_element(By.XPATH, "//div[@class='marketplace-filter-type' and @data-type='activity']")
    marketplace_div.click()

    _look_for_and_click_matching_session(driver, session_string)
    

def _look_for_and_click_matching_session(driver, session_string):
    # The page may take a while to load. Look for up to NUM_ATTEMPTS seconds before giving up.
    NUM_ATTEMPTS = 10
    for i in range(NUM_ATTEMPTS):
        try:
            sessions = driver.find_elements(By.CLASS_NAME, "marketplace-result-details-title")
            matching_elements = [s for s in sessions if session_string in s.text]
            if len(matching_elements) != 1:
                time.sleep(1)
                continue
            matching_elements[0].click()
            return
        except:
            pass
    raise ValueError(f"Expected single session matching {session_string}. Found {[e.text for e in matching_elements]}")

def fetch_session_start_time(session_string: str, username: str, password: str):
    with FirefoxDriver() as driver:
        _playwaze_login(driver, username, password)
        _go_to_session_from_string(driver, session_string)
        time_div = driver.find_element(By.XPATH, "//i[@class='far fa-calendar-alt']/ancestor::div")
        # Get the text inside the div
        time_text = time_div.text

        # Extract the date and start time using regular expressions
        date_match = re.search(r"(\d{2}/\d{2}/\d{4})", time_text)  # Matches the date in DD/MM/YYYY format
        start_time_match = re.search(r"(\d{2}:\d{2}) -", time_text)  # Matches the start time in HH:MM format

        # Check if both date and start time are found
        if date_match and start_time_match:
            date_str = date_match.group(1)  # Extract the date as a string
            start_time_str = start_time_match.group(1)  # Extract the start time as a string
                    
            # Combine the date and start time into a single string
            full_datetime_str = date_str + " " + start_time_str  # e.g., "08/11/2024 12:30"
            
            # Convert the combined string into a datetime object
            start_datetime = datetime.strptime(full_datetime_str, "%d/%m/%Y %H:%M")
            print("Start Time (as datetime object):", start_datetime)
            return start_datetime
        else:
            raise ValueError("Error finding date of session")

def book_session(session_string: str, username: str, password: str):
    with FirefoxDriver() as driver:
        _playwaze_login(driver, username, password)
        _go_to_session_from_string(driver, session_string)

        wait = WebDriverWait(driver, 10)

        # book_button = driver.find_element("id", "attendButtona")
        book_button = driver.find_element(By.XPATH, "//button[@id='attendButtona' and text()='Book']")
        driver.execute_script("arguments[0].click();", book_button)

        continue_button = wait.until(EC.element_to_be_clickable((By.ID, "dependant-booking")))
        continue_button.click()

        account_div = wait.until(EC.element_to_be_clickable((By.XPATH, f"//div[@class='select-account' and @accusername='{username}']")))
        account_div.click()
        
        complete_button = wait.until(EC.element_to_be_clickable((By.ID, "session-book")))
        complete_button.click()