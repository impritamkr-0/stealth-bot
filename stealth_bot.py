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

# --- MAIL.TM API FUNCTIONS (FIXED PARSING) ---
API_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

def create_mail_tm_account():
    """Fetches a domain, generates an address, and returns the email & auth token."""
    res = requests.get("https://api.mail.tm/domains", headers=API_HEADERS)
    data = res.json()
    
    # FIX: Safely extract the domain whether the API returns a list or a dict
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
    
    # FIX: Safely return inbox messages whether it's a list or dict
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
        # --- TAB 1: POPAI (STEALTH LOGIN) ---
        print("Opening PopAI (stealth mode)...")
        driver.get("https://sheetspopaipro.sjv.io/login")
        human_like_delay(2, 4)

        login_button_1 = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Login')]"))
        )
        driver.execute_script("arguments[0].click();", login_button_1)
        human_like_delay(1, 2)

        email_field = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[placeholder='Email address']"))
        )
        human_like_type(email_field, my_email)
        human_like_delay(1, 2)

        print("Clicking the second Login button inside the modal...")
        login_button_2 = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'chat-modal-wrap')]//button[contains(., 'Login') or @type='submit']"))
        )
        driver.execute_script("arguments[0].click();", login_button_2)
        human_like_delay(1, 2)

        # --- WAIT FOR OTP VIA API (POLLING) ---
        print("Polling API every 5 seconds waiting for the PopAI email to arrive...")
        otp_code = None
        
        for _ in range(12):
            time.sleep(5)
            inbox = check_mail_tm_inbox(api_token)
            
            if len(inbox) > 0:
                print("Email received! Extracting OTP...")
                msg_id = inbox[0]['id']
                email_data = fetch_mail_tm_message(api_token, msg_id)
                email_body = email_data.get('text', '') or email_data.get('html', '')
                
                otp_match = re.search(r'\b\d{6}\b', email_body)
                if not otp_match:
                    otp_match = re.search(r'OTP:\s*(\d{6})', email_body, re.IGNORECASE)
                    
                if otp_match:
                    otp_code = otp_match.group(1) if otp_match.groups() else otp_match.group(0)
                    print(f"Extracted OTP: {otp_code}")
                break

        if otp_code:
            otp_input = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".chat-modal-wrap input"))
            )
            driver.execute_script("arguments[0].focus();", otp_input)
            driver.execute_script("arguments[0].click();", otp_input)
            human_like_delay(0.5, 1)

            print("Typing OTP naturally across all boxes...")
            actions = ActionChains(driver)
            for char in otp_code:
                actions.send_keys(char).perform()
                time.sleep(random.uniform(0.1, 0.3))
                
            human_like_delay(1, 2)

            print("Clicking the Verify button...")
            verify_button = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "(//*[contains(text(), 'Verify')])[last()]"))
            )
            driver.execute_script("arguments[0].click();", verify_button)
            
            print("Verification submitted! Waiting exactly 5 seconds for account creation...")
            time.sleep(5)
            print("AUTOMATION TRULY COMPLETE (GITHUB STEALTH MODE)!")
        else:
            print("Failed to receive or extract OTP from the API.")

    except Exception as e:
        print(f"Error encountered: {e}")
    finally:
        driver.quit()
        display.stop() 

if __name__ == "__main__":
    run_stealth_automation()