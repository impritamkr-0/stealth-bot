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

# Try to import BeautifulSoup, but continue without it if not available
try:
    from bs4 import BeautifulSoup
    HAS_BEAUTIFULSOUP = True
except ImportError:
    print("BeautifulSoup not available, using fallback methods")
    HAS_BEAUTIFULSOUP = False

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
    """Extract verification code with multiple patterns and fallback methods"""
    if not email_text:
        return None

    # Clean the text - remove HTML tags if present (simple fallback if BeautifulSoup not available)
    clean_text = email_text
    if not HAS_BEAUTIFULSOUP:
        clean_text = re.sub(r'<[^>]+>', '', email_text)  # Simple HTML tag removal

    # If we have BeautifulSoup, use it for better HTML parsing
    if HAS_BEAUTIFULSOUP and '<' in email_text and '>' in email_text:
        try:
            soup = BeautifulSoup(email_text, 'html.parser')
            clean_text = soup.get_text()
        except:
            clean_text = re.sub(r'<[^>]+>', '', email_text)

    # Try multiple patterns to find the verification code
    code_patterns = [
        r'\b\d{4,6}\b',  # Simple 4-6 digit number
        r'code:\s*(\d{4,6})',  # code: 123456
        r'verification\s*code:\s*(\d{4,6})',  # verification code: 123456
        r'your\s*code\s*is:\s*(\d{4,6})',  # your code is: 123456
        r'[\-_\s](\d{1})[\-_\s]?(\d{1})[\-_\s]?(\d{1})[\-_\s]?(\d{1})[\-_\s]?(\d{1})[\-_\s]?(\d{1})\b',  # 1 2 3 4 5 6 or 1-2-3-4-5-6
        r'(\d{4,6})',  # Just any 4-6 digit number
        r'code\s*[:=]\s*[\'"\]*(\d{4,6})[\'"\]*',  # code:"123456" or code='123456'
    ]

    for pattern in code_patterns:
        match = re.search(pattern, clean_text, re.IGNORECASE)
        if match:
            code = ''.join([g for g in match.groups() if g]).strip()
            if len(code) >= 4 and len(code) <= 6:
                return code

    # If no code found, try to find the first 4-6 digit number in the text
    digit_matches = re.findall(r'\d{4,6}', clean_text)
    if digit_matches:
        return digit_matches[0]  # Return the first 4-6 digit number found

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
    try:
        chrome_version = get_chrome_major_version()
        if chrome_version:
            print(f"Detected Chrome version: {chrome_version}")
            driver = uc.Chrome(options=options, version_main=chrome_version)
        else:
            driver = uc.Chrome(options=options)
    except Exception as e:
        print(f"Error launching Chrome: {e}")
        display.stop()
        return

    try:
        # --- TAB 1: DEEPVINCI LIMITED REGISTRATION ---
        print("Opening DeepVinci Limited registration page...")
        driver.get("https://deepvincilimited.sjv.io/bkP2rv")
        human_like_delay(3, 5)

        # Rest of your registration code...
        # [Previous registration steps remain the same]

        # --- WAIT FOR VERIFICATION CODE VIA API ---
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
                        subject = msg.get('subject', 'No subject')
                        print(f"Checking message: {subject}")

                        email_data = fetch_mail_tm_message(api_token, msg_id)
                        email_text = email_data.get('text', '') or email_data.get('html', '')
                        email_subject = subject.lower()

                        # Only check emails that look like verification emails
                        if any(keyword in email_subject for keyword in ['verify', 'confirm', 'code', 'deepvinci', 'registration']):
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

        # Rest of your verification code submission...
        # [Previous verification steps remain the same]

    except Exception as e:
        print(f"Error encountered: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            driver.quit()
        except:
            pass
        display.stop()

if __name__ == "__main__":
    run_stealth_automation()
