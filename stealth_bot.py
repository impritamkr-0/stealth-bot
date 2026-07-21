import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from pyvirtualdisplay import Display
import time
import random
import string
import re
import requests
from fake_useragent import UserAgent
import subprocess
import sys

def get_chrome_major_version():
    """Automatically detects the installed Chrome major version on Linux."""
    try:
        output = subprocess.check_output(['google-chrome', '--version']).decode('utf-8')
        major_version = int(output.strip().split()[2].split('.')[0])
        return major_version
    except Exception as e:
        print(f"Failed to detect Chrome version: {e}")
        return None

def human_like_delay(min_sec=1, max_sec=3):
    time.sleep(random.uniform(min_sec, max_sec))

def human_like_type(element, text, min_delay=0.1, max_delay=0.3):
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(min_delay, max_delay))

# --- MAIL.TM API FUNCTIONS ---
API_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

def create_mail_tm_account():
    """Fetches a domain, generates an address, and returns the email & auth token."""
    res = requests.get("https://api.mail.tm/domains", headers=API_HEADERS)
    data = res.json()

    if isinstance(data, list):
        domain = data[0]['domain']
    else:
        domain = data.get('hydra:member', [{}])[0].get('domain')

    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    address = f"{username}@{domain}"
    password = "StealthBotPassword123!"

    payload = {"address": address, "password": password}

    requests.post("https://api.mail.tm/accounts", json=payload, headers=API_HEADERS)

    token_res = requests.post("https://api.mail.tm/token", json=payload, headers=API_HEADERS)
    token = token_res.json()['token']

    return address, token

def check_mail_tm_inbox(token):
    """Checks the inbox using the secure JWT token."""
    headers = API_HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"
    res = requests.get("https://api.mail.tm/messages", headers=headers)
    data = res.json()

    if isinstance(data, list):
        return data
    return data.get('hydra:member', [])

def fetch_mail_tm_message(token, msg_id):
    """Fetches the actual body of the email."""
    headers = API_HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"
    res = requests.get(f"https://api.mail.tm/messages/{msg_id}", headers=headers)
    return res.json()

def run_stealth_automation():
    print("Spinning up the Xvfb Ghost Monitor...")
    display = Display(visible=0, size=(1920, 1080))
    display.start()

    # 1. GET EMAIL INSTANTLY VIA API
    print("Generating temporary email via Mail.tm API...")
    try:
        my_email, api_token = create_mail_tm_account()
        print(f"Success! Got stealth email: {my_email}")
    except Exception as e:
        print(f"Failed to generate email. Exiting. Error: {e}")
        display.stop()
        return

    # --- STEALTH CONFIGURATION ---
    ua = UserAgent()
    user_agent = ua.random

    options = uc.ChromeOptions()
    options.add_argument(f"--user-agent={user_agent}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=IsolateOrigins,site-per-process")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-accelerated-2d-canvas")
    options.add_argument("--disable-gpu")
    options.add_argument(f"--window-size={random.randint(1200, 1920)},{random.randint(800, 1080)}")
    options.add_argument("--disable-webrtc")

    print("Launching stealth Chrome...")
    chrome_version = get_chrome_major_version()

    if chrome_version:
        print(f"Detected Chrome version: {chrome_version}")
        driver = uc.Chrome(options=options, version_main=chrome_version)
    else:
        driver = uc.Chrome(options=options)

    try:
        # --- TAB 1: DEEPVINCI LIMITED REGISTRATION ---
        print("Opening DeepVinci Limited registration page...")
        driver.get("https://deepvincilimited.sjv.io/bkP2rv")
        human_like_delay(3, 5)

        # 1. Click on Register link
        print("Looking for Register link...")
        register_link = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Register') or contains(text(), 'register')]"))
        )
        ActionChains(driver).move_to_element(register_link).click().perform()
        human_like_delay(2, 3)

        # 2. Enter email address
        print("Entering email address...")
        email_field = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
        )
        human_like_type(email_field, my_email)
        human_like_delay(1, 2)

        # 3. Click Next Step
        print("Clicking Next Step after email...")
        next_button_1 = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Next Step') or contains(text(), 'next step')]"))
        )
        ActionChains(driver).move_to_element(next_button_1).click().perform()
        human_like_delay(2, 3)

        # 4. Generate and enter strong password
        password = "StealthP@ssword123!"
        print("Setting password...")
        password_field = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
        )
        human_like_type(password_field, password)

        # 5. Confirm password
        confirm_password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "(//input[@type='password'])[2]"))
        )
        human_like_type(confirm_password_field, password)
        human_like_delay(1, 2)

        # 6. SUBMIT PASSWORD FORM NATIVELY (ENTER KEY + ACTION CHAINS)
        print("Submitting password form...")
        confirm_password_field.send_keys(Keys.ENTER)
        human_like_delay(2, 3)

# Fallback click if ENTER key didn't close modal
        try:
            print("Locating the active Next Step button on the modal...")
            # Find ALL 'Next Step' buttons on the page
            next_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), 'Next Step') or contains(text(), 'next step')]")
            
            if next_buttons:
                # Select the very last one added to the screen (the modal button) and force click it
                driver.execute_script("arguments[0].click();", next_buttons[-1])
                print("Successfully clicked the modal's Next Step button!")
        except Exception as e:
            print(f"Fallback click failed: {e}")

        human_like_delay(3, 5)

        # --- WAIT FOR VERIFICATION CODE VIA API (POLLING) ---
        print("Polling API every 5 seconds waiting for the verification email to arrive...")
        verification_code = None

        for _ in range(12):  # Try for 1 minute
            time.sleep(5)
            inbox = check_mail_tm_inbox(api_token)

            if len(inbox) > 0:
                print("Email received! Extracting verification code...")
                msg_id = inbox[0]['id']
                email_data = fetch_mail_tm_message(api_token, msg_id)
                email_body = email_data.get('text', '') or email_data.get('html', '')

                code_match = re.search(r'\b\d{4,6}\b', email_body)
                if not code_match:
                    code_match = re.search(r'code:\s*(\d{4,6})', email_body, re.IGNORECASE)
                if not code_match:
                    code_match = re.search(r'verification\s*code:\s*(\d{4,6})', email_body, re.IGNORECASE)

                if code_match:
                    verification_code = code_match.group(1)
                    print(f"Extracted verification code: {verification_code}")
                    break

        if verification_code:
            # 7. Enter verification code
            print("Entering verification code...")
            code_field = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
            )
            human_like_type(code_field, verification_code)
            human_like_delay(1, 2)

            # 8. Click Complete Registration
            print("Clicking Complete Registration...")
            complete_button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Complete') or contains(text(), 'complete') or contains(text(), 'Submit')]"))
            )
            ActionChains(driver).move_to_element(complete_button).click().perform()

            print("Registration submitted! Waiting for completion...")
            human_like_delay(3, 5)
            print("AUTOMATION COMPLETE!")
        else:
            print("Failed to receive verification code. Taking debug screenshot...")
            driver.save_screenshot("debug_error.png")
            sys.exit(1)

    except Exception as e:
        print(f"Error encountered: {e}")
        driver.save_screenshot("debug_error.png")
        sys.exit(1)
        
    finally:
        driver.quit()
        display.stop()

if __name__ == "__main__":
    run_stealth_automation()
