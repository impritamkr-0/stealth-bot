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
from bs4 import BeautifulSoup

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

# --- MAIL.TM API FUNCTIONS (IMPROVED) ---
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

def get_all_mail_tm_messages(token):
    """Get all messages including those in spam"""
    headers = API_HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"
    res = requests.get("https://api.mail.tm/messages", headers=headers)
    data = res.json()

    if isinstance(data, list):
        return data
    return data.get('hydra:member', [])

def fetch_mail_tm_message(token, msg_id):
    """Fetches the full message content"""
    headers = API_HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"
    res = requests.get(f"https://api.mail.tm/messages/{msg_id}", headers=headers)
    return res.json()

def extract_verification_code(email_text):
    """Improved verification code extraction with multiple patterns"""
    if not email_text:
        return None

    # Try to find code in plain text
    code_patterns = [
        r'\b\d{4,6}\b',  # Simple 4-6 digit number
        r'code:\s*(\d{4,6})',  # code: 123456
        r'verification\s*code:\s*(\d{4,6})',  # verification code: 123456
        r'your\s*code\s*is:\s*(\d{4,6})',  # your code is: 123456
        r'[\-_\s](\d{1})[\-_\s]?(\d{1})[\-_\s]?(\d{1})[\-_\s]?(\d{1})[\-_\s]?(\d{1})[\-_\s]?(\d{1})\b',  # 1 2 3 4 5 6 or 1-2-3-4-5-6
        r'(\d{4,6})',  # Just any 4-6 digit number
    ]

    # Parse HTML if available
    soup = BeautifulSoup(email_text, 'html.parser')
    text_content = soup.get_text()

    for pattern in code_patterns:
        match = re.search(pattern, text_content, re.IGNORECASE)
        if match:
            code = ''.join(match.groups()).strip()
            if len(code) >= 4:
                return code

    return None

def generate_random_password(length=12):
    """Generate a random password"""
    chars = string.ascii_letters + string.digits + "!@#$%^&*()"
    return ''.join(random.choice(chars) for _ in range(length))

def run_stealth_automation():
    print("Starting DeepVinci Limited registration automation...")
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
        try:
            register_link = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Register') or contains(text(), 'register') or contains(text(), 'Create Account')]"))
            )
            driver.execute_script("arguments[0].click();", register_link)
            human_like_delay(2, 3)
        except Exception as e:
            print(f"Could not find Register link: {e}")
            # Try alternative approach - maybe it's already on registration page
            pass

        # 2. Enter email address
        print("Entering email address...")
        email_field = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
        )
        human_like_type(email_field, my_email)
        human_like_delay(1, 2)

        # 3. Click Next Step
        print("Clicking Next Step after email...")
        next_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Next') or contains(text(), 'Continue') or contains(text(), 'Submit')]"))
        )
        driver.execute_script("arguments[0].click();", next_button)
        human_like_delay(2, 3)

        # 4. Generate and enter password
        password = generate_random_password()
        print("Setting password...")
        password_field = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
        )
        human_like_type(password_field, password)

        # 5. Confirm password if field exists
        try:
            confirm_password_field = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "(//input[@type='password'])[2]"))
            )
            human_like_type(confirm_password_field, password)
        except:
            print("No confirm password field found, continuing...")

        human_like_delay(1, 2)

        # 6. Click Next Step after password
        print("Clicking Next Step after password...")
        next_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Next') or contains(text(), 'Continue') or contains(text(), 'Submit') or contains(text(), 'Sign Up')]"))
        )
        driver.execute_script("arguments[0].click();", next_button)
        human_like_delay(2, 3)

        # --- WAIT FOR VERIFICATION CODE VIA API (IMPROVED POLLING) ---
        print("Polling API every 5 seconds waiting for the verification email to arrive...")
        verification_code = None
        max_attempts = 24  # 2 minutes total
        attempt = 0

        while attempt < max_attempts and not verification_code:
            attempt += 1
            print(f"Polling attempt {attempt}/{max_attempts}...")
            time.sleep(5)

            try:
                messages = get_all_mail_tm_messages(api_token)
                if messages:
                    print(f"Found {len(messages)} messages in inbox")

                    # Sort messages by date (newest first)
                    messages_sorted = sorted(messages, key=lambda x: x.get('createdAt', ''), reverse=True)

                    for msg in messages_sorted:
                        msg_id = msg['id']
                        print(f"Checking message: {msg.get('subject', 'No subject')}")

                        email_data = fetch_mail_tm_message(api_token, msg_id)
                        email_text = email_data.get('text', '') or email_data.get('html', '')
                        email_subject = email_data.get('subject', '').lower()

                        # Only check emails that look like verification emails
                        if 'verify' in email_subject or 'confirm' in email_subject or 'code' in email_subject or 'deepvinci' in email_subject:
                            print("This looks like a verification email, extracting code...")
                            verification_code = extract_verification_code(email_text)
                            if verification_code:
                                print(f"Found verification code: {verification_code}")
                                break
                        else:
                            print(f"Skipping email with subject: {email_subject}")

                if verification_code:
                    break

            except Exception as e:
                print(f"Error checking messages: {e}")
                continue

        if verification_code:
            print("Entering verification code...")
            try:
                code_field = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
                )
                human_like_type(code_field, verification_code)
                human_like_delay(1, 2)

                # Click Complete Registration
                print("Clicking Complete Registration...")
                complete_button = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Complete') or contains(text(), 'Submit') or contains(text(), 'Verify') or contains(text(), 'Finish')]"))
                )
                driver.execute_script("arguments[0].click();", complete_button)

                print("Registration submitted! Waiting for completion...")
                human_like_delay(5, 7)
                print("AUTOMATION COMPLETE!")

                # Take screenshot for verification
                driver.save_screenshot('registration_complete.png')
                print("Saved screenshot as registration_complete.png")

            except Exception as e:
                print(f"Error during verification code submission: {e}")
        else:
            print("Failed to receive or extract verification code from the API after multiple attempts.")

            # Save the last email content for debugging
            try:
                messages = get_all_mail_tm_messages(api_token)
                if messages:
                    last_msg = messages[0]
                    email_data = fetch_mail_tm_message(api_token, last_msg['id'])
                    with open('last_email_content.html', 'w', encoding='utf-8') as f:
                        f.write(email_data.get('html', '') or email_data.get('text', ''))
                    print("Saved last email content to last_email_content.html for debugging")
            except Exception as e:
                print(f"Could not save email content for debugging: {e}")

    except Exception as e:
        print(f"Error encountered: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()
        display.stop()

if __name__ == "__main__":
    run_stealth_automation()
