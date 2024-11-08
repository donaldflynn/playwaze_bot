from selenium import webdriver
import time
from credentials import username, password

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

SESSION_NAME_KEYWORD = "Sat 9/11"

def book_session(keyword):
        
    driver = webdriver.Chrome()

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

    # Go to sessions
    driver.get("https://www.playwaze.com/oxford-university-badminton-club/e5vt8osgi3erh/Community-Details")

    # Filter to clubnight only
    marketplace_div = driver.find_element(By.XPATH, "//div[@class='marketplace-filter-type' and @data-type='activity']")
    marketplace_div.click()

    time.sleep(1)
    elements = driver.find_elements(By.CLASS_NAME, "marketplace-result-details-title")
    matching_elements = [e for e in elements if SESSION_NAME_KEYWORD in e.text]
    if len(matching_elements) != 1:
        raise ValueError(f"Expected single session matching {SESSION_NAME_KEYWORD}. Found {[e.text for e in matching_elements]}")
    session_button = matching_elements[0]
    session_button.click()


    time.sleep(20)

book_session(SESSION_NAME_KEYWORD)