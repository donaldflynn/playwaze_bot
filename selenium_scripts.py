from selenium import webdriver
import time
from credentials import username, password

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from datetime import datetime

import re

SESSION_NAME_KEYWORD = "Sat 9/11"

def _playwaze_login(driver):
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

    time.sleep(1)
    sessions = driver.find_elements(By.CLASS_NAME, "marketplace-result-details-title")
    matching_elements = [s for s in sessions if SESSION_NAME_KEYWORD in s.text]
    if len(matching_elements) != 1:
        raise ValueError(f"Expected single session matching {session_string}. Found {[e.text for e in matching_elements]}")
    session_button = matching_elements[0]
    session_button.click()
    time.sleep(1)

def fetch_session_start_time(driver, session_string: str):
    _playwaze_login(driver)
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
    else:
        raise LookupError("Error finding date of session")



driver = webdriver.Chrome()
fetch_session_start_time(driver, SESSION_NAME_KEYWORD)
