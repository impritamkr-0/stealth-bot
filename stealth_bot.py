import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyvirtualdisplay import Display
import time
import random
import string
import re
import requests
from fake_useragent import UserAgent
import subprocess
import sys

# --- CONFIGURATION ---
TARGET_URL = "https://deepvincilimited.sjv.io/bkP2rv"
POLLING_DELAY = 2  # Seconds between checking Mail.tm API
MAX_POLLING_ATTEMPTS = 45  # Wait up to 90 seconds total

def get_chrome_major_version():
    """Automatically detects the installed Chrome major version on Linux."""
    try:
        output = subprocess.check_output(['google-chrome', '--version']).decode('utf-8')
        major_version = int(output.strip().split()[2].split('.')[0])
        return major_version
    except Exception as e:
        print(f"Failed to detect Chrome version: {e}")
        return None

def human_like_delay(min_sec=1.0, max_sec=2.0):
    time.sleep(random.uniform(min_sec, max_sec))

def human_like_type(element, text, min_delay=0.08, max_delay=0.18):
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(min_delay, max_delay))

# --- MAIL.TM API FUNCTIONS ---
API_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

def create_mail_tm_account():
    """Fetches a domain, generates an address, and returns the email & auth token."""
    try:
        res = requests.get("https://api.mail.tm/domains", headers=API_HEADERS, timeout=10)
        data = res.json()
        if isinstance(data, list):
            domain = data[0]['domain']
        else:
            domain = data.get('hydra:member', [{}])[0].get('domain')

        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        address = f"{username}@{domain}"
        password = "StealthP@ssword123!"

        payload = {"address": address, "password": password}
        requests.post("https://api.mail.tm/accounts", json=payload, headers=API_HEADERS, timeout=10)
        token_res = requests.post("https://api.mail.tm/token", json=payload, headers=API_HEADERS, timeout=10)
        token = token_res.json()['token']
        return address, token
    except Exception as e:
        print(f"Mail.tm API error: {e}")
        return None, None

def check_mail_tm_inbox(token):
    """Checks the inbox using the secure JWT token."""
    headers = API_HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"
    try:
        res = requests.get("https://api.mail.tm/messages", headers=headers, timeout=10)
        if res.status_code != 200:
            return []
        data = res.json()
        if isinstance(data, list):
            return data
        return data.get('hydra:member', [])
    except Exception:
        return []

def fetch_mail_tm_message(token, msg_id):
    """Fetches the actual body of the email."""
    headers = API_HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"
    try:
        res = requests.get(f"https://api.mail.tm/messages/{msg_id}", headers=headers, timeout=10)
        return res.json()
    except Exception:
        return {}

def extract_code_from_text(text_content):
    """Parses text to reliably extract a 4 to 6 digit verification code."""
    if not text_content:
        return None
    clean_text = re.sub(r'<[^>]+>', ' ', str(text_content))
    patterns = [
        r'(?:code|verification|otp)\s*(?:is|:|\s)\s*([0-9]{4,6})',
        r'([0-9]{4,6})\s*(?:is your verification code|is your code)',
        r'\b([0-9]{4,6})\b'
    ]
    for pat in patterns:
        match = re.search(pat, clean_text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None

def run_stealth_automation():
    print("Spinning up the Xvfb Ghost Monitor...")
    display = Display(visible=0, size=(1920, 1080))
    display.start()

    print("Generating temporary email via Mail.tm API...")
    my_email, api_token = create_mail_tm_account()
    if not my_email:
        print("Failed to generate email. Exiting.")
        display.stop()
        return
    print(f"Success! Got stealth email: {my_email}")

    ua = UserAgent()
    user_agent = ua.random

    options = uc.ChromeOptions()
    options.add_argument(f"--user-agent={user_agent}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    print("Launching stealth Chrome...")
    chrome_version = get_chrome_major_version()
    if chrome_version:
        driver = uc.Chrome(options=options, version_main=chrome_version)
    else:
        driver = uc.Chrome(options=options)

    wait = WebDriverWait(driver, 20)

    try:
        print(f"Opening registration landing page: {TARGET_URL}")
        driver.get(TARGET_URL)
        human_like_delay(3, 5)

        # ========================================================= #
        # STEP 1: SWITCH FROM LOGIN TO REGISTER                    #
        # ========================================================= #
        print("Looking for 'Register' button/link inside modal...")
        
        # Target the 'Register' link on the modal directly
        register_click_success = False
        register_xpaths = [
            "//a[contains(text(), 'Register')]",
            "//span[contains(text(), 'Register')]",
            "//*[contains(text(), \"Don't have an account?\")]/following-sibling::*",
            "//*[contains(text(), \"Don't have an account?\")]//a"
        ]

        for xpath in register_xpaths:
            try:
                elem = driver.find_element(By.XPATH, xpath)
                if elem.is_displayed():
                    driver.execute_script("arguments[0].click();", elem)
                    print(f"Clicked Register link using: {xpath}")
                    register_click_success = True
                    break
            except Exception:
                continue

        if not register_click_success:
            print("Notice: Could not locate explicit Register link, proceeding to check for email field directly.")

        human_like_delay(1.5, 2.5)

        # ========================================================= #
        # STEP 2: ENTER EMAIL ADDRESS                              #
        # ========================================================= #
        print("Waiting for Email input field...")
        email_field = wait.until(EC.visibility_of_element_located((
            By.CSS_SELECTOR, "input[type='email'], input[placeholder*='Email'], input[placeholder*='email']"
        )))
        
        print(f"Entering email address: {my_email}")
        email_field.clear()
        human_like_type(email_field, my_email)
        human_like_delay(1, 2)

        print("Clicking Next Step after entering email...")
        next_btn_email = wait.until(EC.presence_of_element_located((
            By.XPATH, "//button[contains(translate(text(), 'NEXT STEP', 'next step'), 'next step')]"
        )))
        driver.execute_script("arguments[0].click();", next_btn_email)
        human_like_delay(2, 3)

        # ========================================================= #
        # STEP 3: SET & CONFIRM PASSWORD                           #
        # ========================================================= #
        print("Waiting for Password input fields...")
        password_input = wait.until(EC.presence_of_element_located((
            By.XPATH, "//input[@placeholder='Password'] | (//input[@type='password'])[1]"
        )))
        confirm_input = wait.until(EC.presence_of_element_located((
            By.XPATH, "//input[@placeholder='Confirm Password'] | (//input[@type='password'])[2]"
        )))

        secure_password = "Stealth@P@ssword99!"
        print("Entering Password...")
        human_like_type(password_input, secure_password)
        human_like_delay(0.5, 1)

        print("Entering Confirm Password...")
        human_like_type(confirm_input, secure_password)

        # Trigger React validation events
        driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", confirm_input)
        driver.execute_script("arguments[0].dispatchEvent(new Event('blur', { bubbles: true }));", confirm_input)
        human_like_delay(1, 2)

        print("Clicking Next Step after entering password...")
        next_btn_pass = wait.until(EC.presence_of_element_located((
            By.XPATH, "//button[contains(translate(text(), 'NEXT STEP', 'next step'), 'next step')]"
        )))
        driver.execute_script("arguments[0].click();", next_btn_pass)
        human_like_delay(2, 3)

        # ========================================================= #
        # STEP 4: WAIT FOR VERIFICATION CODE VIA MAIL.TM API        #
        # ========================================================= #
        print(f"Polling Mail.tm every {POLLING_DELAY}s for verification code...")
        verification_code = None

        for attempt in range(MAX_POLLING_ATTEMPTS):
            time.sleep(POLLING_DELAY)
            inbox = check_mail_tm_inbox(api_token)

            if inbox:
                print(f"Email received on attempt {attempt+1}! Parsing code...")
                msg_id = inbox[0]['id']
                email_data = fetch_mail_tm_message(api_token, msg_id)
                full_content = f"{email_data.get('intro', '')} {email_data.get('text', '')} {email_data.get('html', '')}"
                verification_code = extract_code_from_text(full_content)

                if verification_code:
                    print(f"Extracted verification code: {verification_code}")
                    break

        if not verification_code:
            raise Exception("Timeout waiting for verification email.")

        # ========================================================= #
        # STEP 5: ENTER CODE & COMPLETE REGISTRATION               #
        # ========================================================= #
        print("Waiting for Verification Code input field...")
        code_input = wait.until(EC.presence_of_element_located((
            By.XPATH, "//input[@placeholder='Verification Code'] | //input[@type='text']"
        )))
        print(f"Entering extracted verification code: {verification_code}")
        human_like_type(code_input, verification_code)
        human_like_delay(1, 2)

        print("Clicking Complete Registration...")
        complete_btn = wait.until(EC.presence_of_element_located((
            By.XPATH, "//button[contains(translate(text(), 'COMPLETE REGISTRATION', 'complete registration'), 'complete registration')] | //button[contains(text(), 'Submit')]"
        )))
        driver.execute_script("arguments[0].click();", complete_btn)

        human_like_delay(5, 7)
        print("AUTOMATION COMPLETE SUCCESSFUL!")

    except Exception as e:
        print(f"Error encountered: {e}")
        try:
            driver.save_screenshot("debug_error_visual_flow.png")
            print("Debug screenshot saved: debug_error_visual_flow.png")
        except Exception:
            pass
        sys.exit(1)
    finally:
        driver.quit()
        display.stop()

if __name__ == "__main__":
    run_stealth_automation()
